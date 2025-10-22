"""Standard HTTP requests."""

from calls import models
from django.http import FileResponse, HttpRequest, HttpResponse, HttpResponseNotFound


def index(_: HttpRequest) -> HttpResponse:
    """Index page."""
    return HttpResponse("Hello, world.")


def speech(request: HttpRequest, recording_id: int) -> HttpResponse:
    """Look up a speech file and return it."""
    try:
        # TODO make async?
        recording = models.Speech.objects.get(id=recording_id)
        return FileResponse(recording.recording)
    except models.Recruit.DoesNotExist:
        return HttpResponseNotFound()
