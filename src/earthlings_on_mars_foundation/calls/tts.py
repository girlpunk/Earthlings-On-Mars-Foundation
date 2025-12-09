import os
from cartesia import AsyncCartesia
# from cartesia.tts import OutputFormat_Raw, TtsRequestIdSpecifier

class Tts:

    def __init__(self) -> None:
        api_key = os.getenv("CARTESIA_API_KEY")
        if not api_key:
            raise Exception("Missing cartesia API key envvar CARTESIA_API_KEY")
        self.client = AsyncCartesia(api_key=api_key)

    async def audio_bytes(self, text: str):
        b = bytearray()
        async for output in self.client.tts.bytes(
            model_id="sonic-2",
            transcript=text,
            voice={"id": "694f9389-aac1-45b6-b726-9d9369183238"},
            language="en",
            output_format={
                "container": "raw",
                "sample_rate": 8000,
                "encoding": "pcm_alaw",
            },
        ):
            b += output
        return bytes(b)


# vim: tw=0 ts=4 sw=4
