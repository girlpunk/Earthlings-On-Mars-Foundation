import contextlib
import logging
from typing import Any, List

from calls import models
from calls.consumers import CallConsumer, InvalidMessageError
from django.urls import reverse

request_logger = logging.getLogger("eomf.calls.consumer.jambonz")


class JambonzCallConsumer(CallConsumer):
    def __init__(self) -> None:
        self.callLog: models.CallLog | None = None
        super().__init__()

    async def connect(self) -> None:
        self.outbound: List[dict[str, Any]] = []
        super().connect()
        await self.accept("ws.jambonz.org")

    async def _update_log(self, message: dict[str, Any]) -> None:
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

    async def receive_json(self, data: dict[str, Any]) -> None:
        """Decode message data from JSON, and send to the relevent handler."""
        request_logger.info("IN: %s", data)

        # TODO call self.call_hungup("reason...") when that event happens

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
    ) -> tuple[str | None, str]:
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


# vim: tw=0 ts=4 sw=4
