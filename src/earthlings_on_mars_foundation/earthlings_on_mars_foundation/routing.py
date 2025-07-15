from calls.consumers import CallConsumer
from django.urls import path, re_path

websocket_urlpatterns = [
    re_path(r"^ws/call/$", CallConsumer.as_asgi()),
    re_path(r"^ws/call$", CallConsumer.as_asgi()),
    path("ws/call", CallConsumer.as_asgi()),
]
