"""Websocket entrypoints."""

from __future__ import annotations

import asyncio
import contextlib
import datetime
import json
import logging
import threading
import uuid

from asgiref.sync import sync_to_async
from calls import models
from calls.lua import AsyncLuaRuntime
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.db.models import Count, Exists, F, OuterRef, Q
from django.urls import reverse

request_logger = logging.getLogger("django.calls.consumer")


class InvalidMessageError(Exception):
    """Unknown message type recieved."""

    def __init__(self, msg_type: str, data: dict[str, str]) -> None:
        """Prepare the message exception."""
        super().__init__(
            "Unknown message type %s. Message body: %s",
            msg_type,
            data,
        )


class CallConsumer(AsyncJsonWebsocketConsumer):
    """Manage websocket connections."""

    def __init__(self) -> None:
        super().__init__()
        self.incomingMessage = None
        self.newMessage = threading.Event()
        self.callLog = None
        self.active_message = None
        self.ack_done = False
        self.action_thread = None

    async def connect(self) -> None:
        """Handle a new incoming connection."""
        request_logger.info("New connect!")

    async def disconnect(self, _: str) -> None:
        """Handle a disconnect."""
        if self.callLog is not None:
            self.callLog.completed = True
            await self.callLog.asave()

    async def receive(self, text_data: str) -> None:
        """Handle an incoming message."""
        data = json.loads(text_data)
        await self.receive_json(data)

    async def _authenticate(self) -> models.Recruit:
        """Allow a player to authenticate themselves."""
        recruit = None

        while recruit is None:
            recruit_id, reason = await self._gather(
                "Please enter your recruit number to connect your call. If you've lost your multipass and need a replacement recruit number, press 0",
                min_digits=1,
                max_digits=4,
            )

            if reason != "dtmfDetected" or recruit_id is None:
                continue

            if recruit_id == "0":
                # New recruit
                recruit = models.Recruit()
                await recruit.asave()

                number = " ".join(f"{recruit.id:04}")

                await self._say(
                    f"OK let's see, scanner says you're recruit {number}. You got that? {number}, don't forget it!",
                )
            else:
                # Existing recruit
                try:
                    recruit_id = int(recruit_id)
                    recruit = await models.Recruit.objects.aget(id=recruit_id)
                except (models.Recruit.DoesNotExist, TypeError):
                    # Verify the recruit number
                    await self._say("Sorry, that number was not recognised.")
                    continue

        self.callLog.recruit = recruit
        await self._say("Caller verified!")
        return recruit

    async def _check_existing_missions(self, recruit: models.Recruit) -> bool:
        """Check if the player has existing missions for this NPC, and process their completion states."""
        has_uncompleted = False
        recruit_missions = (
            models.RecruitMission.objects.filter(recruit=recruit, finished=None)
            .select_related("mission")
            .select_related("mission__issued_by")
            .select_related("mission__call_back_from")
        )

        async for recruit_mission in recruit_missions.aiterator():
            if recruit_mission.mission.cancel_after_time is not None and recruit_mission.mission.cancel_after_time >= datetime.datetime.now(tz=datetime.UTC):
                await self._cancel_mission(recruit_mission)
                continue

            if recruit_mission.mission.issued_by == self.callLog.NPC:
                if recruit_mission.mission.type == models.MissionTypes.LOCATION:
                    if recruit_mission.mission.call_back_from == self.callLog.location:
                        # Complete "go to location" mission
                        await self._complete_mission(recruit_mission)
                    else:
                        # Issue reminder
                        has_uncompleted = True
                        await self._say(recruit_mission.mission.reminder_text)
                elif recruit_mission.mission.type == models.MissionTypes.CODE:
                    has_uncompleted |= await self._check_code_mission(recruit_mission)
                elif recruit_mission.mission.type == models.MissionTypes.COUNT:
                    has_uncompleted |= await self._check_count_mission(recruit_mission)
                elif recruit_mission.mission.type == models.MissionTypes.LUA:
                    has_uncompleted |= await self._check_lua_mission(recruit_mission)
            elif recruit_mission.mission.type == models.MissionTypes.NPC and recruit_mission.mission.call_another == self.callLog.NPC:
                # Complete "call NPC" mission
                await self._complete_mission(recruit_mission)

        return has_uncompleted

    async def _check_lua_mission(self, recruit_mission: models.RecruitMission) -> bool:
        """Run Lua to check a mission."""
        lua = AsyncLuaRuntime(unpack_returned_tuples=True)

        uncomplete = True

        async def complete_mission() -> None:
            nonlocal uncomplete
            uncomplete = False
            await self._complete_mission(recruit_mission)

        async def cancel_mission() -> None:
            nonlocal uncomplete
            uncomplete = False
            await self._cancel_mission(recruit_mission)

        lua.globals().recruit_mission = recruit_mission
        lua.globals().state = lua.table_from(recruit_mission.state)
        lua.globals().complete_mission = complete_mission
        lua.globals().cancel_mission = cancel_mission
        lua.globals().say = self._say
        lua.globals().gather = self._gather

        request_logger.info("State is: %s", recruit_mission.state)

        await lua.execute(recruit_mission.mission.lua)
        recruit_mission.state = dict(lua.globals().state)

        request_logger.info("State is: %s", recruit_mission.state)

        await recruit_mission.asave()

        return uncomplete

    async def _check_code_mission(self, recruit_mission: models.RecruitMission) -> bool:
        """Recieve a code from the user, and check it against the mission."""
        code = None

        while code is None:
            # Get code prompt
            code, reason = await self._gather(
                recruit_mission.mission.reminder_text,
                min_digits=1,
            )

            if reason != "dtmfDetected" or code is None:
                continue

        if code == str(recruit_mission.mission.code):
            # Correct code
            await self._complete_mission(recruit_mission)
            return False

        # Incorrect code

        # Increment fail counter
        recruit_mission.code_tries += 1
        await recruit_mission.asave()

        if recruit_mission.code_tries >= recruit_mission.mission.cancel_after_tries:
            await self._cancel_mission(recruit_mission)
            return False

        await self._say(recruit_mission.mission.incorrect_text)
        return True

    async def _check_count_mission(self, recruit_mission: models.RecruitMission) -> bool:
        """Recieve a count from the user, and save it to the mission."""
        code = None

        while code is None:
            # Get code prompt
            code, reason = await self._gather(
                recruit_mission.mission.reminder_text,
                min_digits=1,
            )

            if reason != "dtmfDetected" or code is None:
                continue

        recruit_mission.count_value = code
        await recruit_mission.asave()
        await self._complete_mission(recruit_mission)
        return False

    async def _cancel_mission(self, recruit_mission: models.RecruitMission) -> None:
        """Cancel or fail a mission."""
        recruit_mission.finished = datetime.datetime.now(tz=datetime.UTC)
        await recruit_mission.asave()

        recruit_mission.recruit.score -= recruit_mission.mission.points
        await recruit_mission.recruit.asave()

        await self._say(recruit_mission.mission.cancel_text)

    async def _complete_mission(self, recruit_mission: models.RecruitMission) -> None:
        """Successfully complete a mission."""
        recruit_mission.completed = True
        recruit_mission.finished = datetime.datetime.now(tz=datetime.UTC)
        await recruit_mission.asave()

        recruit_mission.recruit.score += recruit_mission.mission.points
        await recruit_mission.recruit.asave()

        await self._say(recruit_mission.mission.completion_text)

    @sync_to_async
    def speech_get_or_create(self, npc: models.NPC, text: str):
        # TODO handle NPC being null, fall back to defalt for error msgs etc
        return models.Speech.objects.get_or_create(
            NPC=npc,
            text=text,
        )

    async def _send(self) -> None:
        """Send a command to Jambonz."""
        if self.ack_done:
            message = {"type": "command", "command": "redirect", "data": self.outbound}
        else:
            self.ack_done = True
            message = {
                "type": "ack",
                "msgid": self.active_message,
                "data": self.outbound,
            }

        request_logger.info("OUT: %s", message)
        await self.send_json(message)

        self.outbound.clear()

    async def _session_new(self) -> None:
        """Start processing a new call."""
        # Start a second thread to actually execute the call logic
        self.action_thread = threading.Thread(
            target=asyncio.run,
            args=(self._new_call(),),
        )
        self.action_thread.start()

    async def _new_call(self) -> None:
        """Prepare new call logic."""
        try:
            recruit = await self._authenticate()

            if self.callLog.NPC is None:
                request_logger.warning("NPC is none")
                await self._say("Unable to identify what NPC you are calling")
                self._send()
                return

            recruit_npc, created = await models.RecruitNPC.objects.aget_or_create(
                recruit=recruit,
                NPC=self.callLog.NPC,
            )

            if created or not recruit_npc.contacted:
                await self._say(self.callLog.NPC.introduction)
                recruit_npc.contacted = True
                await recruit_npc.asave()

            if self.callLog.location is None:
                request_logger.warning("Location is none")

            all_finished = await self._check_existing_missions(recruit)

            if not all_finished:
                await self._find_new_mission(recruit)

            # Send hangup
            await self._hangup()

            if self.callLog is not None:
                self.callLog.completed = True
                self.callLog.success = True
                await self.callLog.asave()
        except Exception:
            await self._say("Sorry, something went wrong")
            await self._hangup()

            if self.callLog is not None:
                self.callLog.completed = True
                self.callLog.success = False
                await self.callLog.asave()

            request_logger.exception("Error during call processing")

    async def _find_new_mission(self, recruit: models.recruit) -> None:
        """Find a new mission for the player to start."""
        mission = (
            await models.Mission.objects.annotate(
                total_prerequisites=Count(
                    "prerequisites",
                ),  # Calculate total number of prerequisites
                completed_prerequisites=Count(  # And completed number of prerequisites
                    models.MissionPrerequisite.objects.filter(
                        Q(mission=OuterRef("pk")),
                        Q(
                            Exists(
                                models.RecruitMission.objects.filter(
                                    mission=OuterRef("prerequisite__id"),
                                    recruit=recruit,
                                    completed=True,
                                ),
                            ),
                        ),
                    ).values("id"),
                ),
                followup_to=Count("mission"),
            )
            .filter(
                Q(
                    issued_by=self.callLog.NPC,
                )  # Issued by the user the NPC is talking to
                & (
                    Q(
                        only_start_from=self.callLog.location,
                    )  # Issued from the location the user is calling from
                    | Q(only_start_from=None)  # Or from any location
                )
                & Q(
                    ~Exists(
                        models.RecruitMission.objects.filter(
                            mission=OuterRef("pk"),
                            recruit=recruit,
                            finished__isnull=False,
                        ),
                    )
                    | Q(repeatable=True),
                )  # User has not already completed, or the mission is repeatable
                & Q(
                    total_prerequisites=F("completed_prerequisites"),
                )  # All prerequisites are complete
                & (Q(not_before__lte=datetime.datetime.now(tz=datetime.UTC)) | Q(not_before=None))  # not before is before now (or unset)
                & (Q(not_after__gte=datetime.datetime.now(tz=datetime.UTC)) | Q(not_after=None)),  # Not after is after now (or unset)
            )
            .order_by("-followup_to", "-priority")
            .afirst()
        )

        if mission is None:
            await self._say(
                "I don't have any more work for you at the moment, give me a call back later.",
            )
            return

        recruit_mission = models.RecruitMission()
        recruit_mission.recruit = recruit
        recruit_mission.mission = mission
        await recruit_mission.asave()

        await self._say(mission.give_text)
        return

    async def _session_reconnect(self, data: str) -> None:
        """Reconnect a disconnected websocket."""
        # TODO(Me): Implement https://github.com/girlpunk/Earthlings-On-Mars-Foundation/issues/3
        raise NotImplementedError


class JambonzCallConsumer(CallConsumer):
    async def connect(self) -> None:
        self.outbound = []
        super().connect()
        await self.accept("ws.jambonz.org")

    async def _update_log(self, message: str) -> None:
        """Update the log for an in-progress call."""
        if self.callLog is None:
            self.callLog, created = await models.CallLog.objects.aget_or_create(
                call_id=message["call_sid"],
                defaults={"duration": 0, "digits": 0},
            )

        if self.callLog.NPC is None:
            with contextlib.suppress(models.NPC.DoesNotExist):
                self.callLog.NPC = await models.NPC.objects.aget(
                    extension=message["data"]["to"],
                )

        if self.callLog.location is None:
            with contextlib.suppress(ValueError, models.Location.DoesNotExist):
                self.callLog.location = await models.Location.objects.aget(
                    extension=message["data"]["from"],
                )

        if "duration" in message["data"]:
            self.callLog.duration = message["data"]["duration"]

        if message["data"]["call_status"] == "completed":
            self.callLog.completed = True

        await self.callLog.asave()

    async def receive_json(self, data: str) -> None:
        """Decode message data from JSON, and send to the relevent handler."""
        request_logger.info("IN: %s", data)

        if data["type"] == "session:new":
            self.active_message = data["msgid"]
            await self._update_log(data)
            await self._session_new()
        elif data["type"] == "session:reconnect":
            await self._session_reconnect(data)
        elif data["type"] == "call:status":
            await self._update_log(data)
            message = {"type": "ack", "msgid": data["msgid"]}
            request_logger.info("OUT: %s", message)
            await self.send_json(message)
        elif data["type"] == "verb:hook":
            self.incomingMessage = data
            self.active_message = data["msgid"]
            self.newMessage.set()
        else:
            raise InvalidMessageError(
                data["type"],
                data,
            )

    async def _say(self, text: str, npc: models.NPC | None = None) -> None:
        """Read text to the player."""
        if npc is None and self.callLog.NPC is None:
            request_logger.warning("Say with unknown NPC!")
            self.outbound.append({"say": {"text": text}})
            return
        if npc is None:
            npc = self.callLog.NPC

        recording, created = await self.speech_get_or_create(npc=npc, text=text)

        if created or recording.recording is None:
            request_logger.warning("Missing text for %s: %s", npc.name, text)
            self.outbound.append({"say": {"text": text}})
        else:
            self.outbound.append(
                {
                    "play": {
                        "url": reverse("speech", kwargs={"id": recording.id}),
                    },
                },
            )

    async def _gather(
        self,
        text: str,
        digits: int | None = None,
        min_digits: int | None = None,
        max_digits: int | None = None,
    ) -> [str, str]:
        """Gather DTMF digits from the player."""
        command = {
            "input": ["digits"],  # Can also include "speech"
            "actionHook": "wss://fa8340b16a8854.lhr.life/ws/call/",
            "bargein": False,
            "dtmfBargein": True,
            "finishOnKey": "#",
            "say": {"text": text},
            "interDigitTimeout": 5,
        }

        if digits is not None:
            command["numDigits"] = digits
        if min_digits is not None:
            command["minDigits"] = min_digits
        if max_digits is not None:
            command["maxDigits"] = max_digits

        recording, created = await self.speech_get_or_create(npc=self.callLog.NPC, text=text)

        if created or recording.recording is None:
            request_logger.warning("Missing text for %s: %s", self.callLog.NPC.name, text)
            command["say"] = {"text": text}
        else:
            command["play"] = {
                "url": reverse("speech", kwargs={"recording_id": recording.id}),
            }

        self.outbound.append({"gather": command})

        await self._send()

        self.newMessage.wait(20)
        value = self.incomingMessage
        self.newMessage.clear()
        self.incomingMessage = None

        digits = None

        if "digits" in value["data"]:
            digits = value["data"]["digits"]
            self.callLog.digits += len(digits)
            await self.callLog.asave()

        return (digits, value["data"]["reason"])

    async def _hangup(self) -> None:
        self.outbound.append({"hangup": {}})

        await self._send()


class AsteriskCallConsumer(CallConsumer):
    async def connect(self) -> None:
        request_logger.info("Asterisk connect()")
        super().connect()
        await self.accept()

    @sync_to_async
    def _update_log(self, message: str) -> None:
        """Update the log for an in-progress call."""
        if self.callLog is None:
            self.callLog, created = models.CallLog.objects.get_or_create(
                call_id=message["channel"]["id"],
                defaults={"duration": 0, "digits": 0},
            )

        if self.callLog.NPC is None:
            with contextlib.suppress(models.NPC.DoesNotExist, ValueError):
                extension = int(message["channel"]["dialplan"]["exten"])
                self.callLog.NPC = models.NPC.objects.get(
                    extension=extension,
                )

        if self.callLog.location is None:
            with contextlib.suppress(ValueError, models.Location.DoesNotExist):
                self.callLog.location = models.Location.objects.get(
                    extension=message["channel"]["caller"]["number"],
                )

        # if "duration" in message["data"]:
        stamp = datetime.datetime.fromisoformat(message["timestamp"])
        created = datetime.datetime.fromisoformat(message["channel"]["creationtime"])
        self.callLog.duration = (stamp - created).total_seconds()

        if message["channel"]["state"] != "Up":
            self.callLog.completed = True

        self.callLog.asave()

    async def receive_json(self, data: str) -> None:
        """Decode message data from JSON, and sent to the relevent handler."""
        request_logger.info("IN: %s", data)

        if data["type"] == "ApplicationRegistered":
            request_logger.info("ApplicationRegistered")
        elif data["type"] == "StasisStart":
            # self.active_message = data["msgid"]
            await self._update_log(data)
            # await self._send("POST", f"channels/{data["channel"]["id"]}/moh", mohClass="default")
            await self._session_new()
        elif data["type"] == "ChannelVarset":
            pass
        elif data["type"] == "ChannelHangupRequest":
            request_logger.info(f"Hangup {data['cause']}")
            data["channel"]["state"] = "Down"
            await self._update_log(data)
            # TODO: Stop thread
        elif data["type"] == "ChannelDialplan" or data["type"] == "ChannelUserevent" or data["type"] == "StasisEnd":
            # TODO: Figure out what this is for
            await self._update_log(data)
        elif data["type"] == "DeviceStateChanged":
            pass
        elif data["type"] == "ChannelDestroyed":
            request_logger.info(f"Hangup {data['cause']}")
            data["channel"]["state"] = "Down"
            await self._update_log(data)
            # TODO: Stop thread
        else:
            raise InvalidMessageError(
                data["type"],
                data,
            )

    async def _send(self, method: str | None, uri: str, **kwargs: dict[str, str]) -> None:
        if method is None:
            pass

        request = {
            "type": "RESTRequest",
            "request_id": str(uuid.uuid4()),
            "method": method,
            "uri": uri,
        }

        for key, value in kwargs.items():
            request[key] = value

        request_logger.info("OUT: %s %s - %s", method, uri, request)
        await self.send_json(request)

        return_object = {"result": ""}
        # if wait_for_response:
        #    return_object['event'] = asyncio.Event()

        # self.requests[uuidstr] = rtnobj
        # await self.websocket.send(msg.encode('utf-8'), text=True)
        # if wait_for_response:
        #    await rtnobj['event'].wait()
        # del self.requests[uuidstr]
        # resp = rtnobj['result']
        # self.log(INFO, f"RESTResponse: {method} {uri} {resp['status_code']} {resp['reason_phrase']}")
        # if callback is not None:
        #    return callback(self.websocket, uuidstr, req, rtnobj['result'])
        # return rtnobj['result']

    async def _say(self, text: str, npc: models.NPC | None = None) -> None:
        """Read text to the player."""
        if npc is None and self.callLog.NPC is None:
            request_logger.warning("Say with unknown NPC!")
            # self.outbound.append({"say": {"text": text}})
            return
        if npc is None:
            npc = self.callLog.NPC

        recording, created = await self.speech_get_or_create(npc=npc, text=text)

        if recording.recording is None:
            request_logger.warning("Missing text for %s: %s", npc.name, text)
            await self._send("POST", f"channels/{self.callLog.call_id}/dtmf", dtmf="012345678ABCD#*")
        #    self.outbound.append({"say": {"text": text}})
        else:
            await self._send("POST", f"channels/{self.callLog.call_id}/play", media=reverse("speech", kwargs={"recording_id": recording.id}))

    async def _gather(
        self,
        text: str,
        digits: int | None = None,
        min_digits: int | None = None,
        max_digits: int | None = None,
    ) -> [str, str]:
        """Gather DTMF digits from the player."""

        # TODO implement
        return ("", "not implemented TODO.")

    async def _hangup(self) -> None:
        # await self._send("DELETE", f"channels/{self.callLog.call_id}", reason_code=16)
        pass
