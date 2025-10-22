import asyncio
import contextlib
import datetime
import json
import logging
import uuid

from asgiref.sync import sync_to_async
from calls import models
from calls.consumers import CallConsumer, InvalidMessageError
from calls.tts import Tts
from django.db.models import Count, Exists, F, OuterRef, Q
from django.urls import reverse

request_logger = logging.getLogger("eomf.calls.consumer.asterisk")


class AsteriskCallConsumer(CallConsumer):

    def __init__(self) -> None:
        super().__init__()
        self.tts = Tts()

    async def connect(self) -> None:
        await super().connect()
        request_logger.info("Asterisk connect()")
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
        #request_logger.info("IN: %s", data)

        mtype = data["type"]
        if mtype == "ApplicationRegistered":
            request_logger.info("ApplicationRegistered")
        elif mtype == "StasisStart":
            # self.active_message = data["msgid"]
            await self._update_log(data)
            # await self._send("POST", f"channels/{data["channel"]["id"]}/moh", mohClass="default")
            await self._session_new()
        elif mtype == "ChannelCreated":
            pass
        elif mtype == "ChannelVarset":
            pass
        elif mtype == "ChannelHangupRequest":
            self.call_hungup(mtype)
            data["channel"]["state"] = "Down"
            await self._update_log(data)
        elif mtype == "ChannelDialplan" or mtype == "ChannelUserevent" or mtype == "StasisEnd":
            # TODO: Figure out what this is for
            await self._update_log(data)
        elif mtype == "DeviceStateChanged":
            pass
        elif mtype == "ChannelDestroyed":
            self.call_hungup(mtype)
            data["channel"]["state"] = "Down"
            await self._update_log(data)
        elif mtype == "ChannelDtmfReceived":
            digit = data["digit"]
            print(f"TONE digit: {digit}")
            # TODO implement gathering digits
        elif mtype == "RESTResponse":
            if data["status_code"] < 200 or data["status_code"] >= 300:
                request_logger.error(f"Failed REST request: {data}")
        elif mtype == "PlaybackStarted":
            pass
        elif mtype == "PlaybackFinished":
            pass
        else:
            raise InvalidMessageError(mtype, data)

    async def _send(self, method: str | None, uri: str, **kwargs: dict[str, str]) -> None:
        if method is None:
            pass

        request = {
            "type": "RESTRequest",
            "request_id": str(uuid.uuid4()),
            "method": method,
            "uri": uri,
            "query_strings": [{"name": name, "value": value} for (name, value) in kwargs.items()],
        }

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

        speech, created = await self.speech_get_or_create(npc=npc, text=text)

        if not speech.recording:
            request_logger.warning("Generating TTS for missing text for %s: %s", npc.name, text)
            audio_bytes = await self.tts.audio_bytes(text)
            await self.speech_store_recording(speech, audio_bytes, True)

        headers = self.scope['headers']
        host = next(iter([h[1].decode('ascii') for h in headers if h[0] == b'host']))
        # TODO detect http/https
        media = "sound:http://%s%s" % (host, reverse("speech", kwargs={"recording_id": speech.id}))
        await self._send("POST", f"channels/{self.callLog.call_id}/play", media=media)

        # TODO wait for event
        await asyncio.sleep(15)

    async def _gather(
        self,
        text: str,
        digits: int | None = None,
        min_digits: int | None = None,
        max_digits: int | None = None,
    ) -> [str, str]:
        """Gather DTMF digits from the player."""

        await self._say(text)

        # TODO implement
        return ("", "not implemented TODO.")

    async def _hangup(self) -> None:
        # https://docs.asterisk.org/Configuration/Miscellaneous/Hangup-Cause-Mappings/#asterisk-hangup-cause-code-mappings
        # 16 = Normal Clearing
        await self._send("DELETE", f"channels/{self.callLog.call_id}", reason_code=16)


# vim: tw=0 ts=4 sw=4
