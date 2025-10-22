"""Websocket version of URLs."""

from calls.consumers_jambonz import JambonzCallConsumer
from calls.consumers_asterisk import AsteriskCallConsumer
from django.urls import path

websocket_urlpatterns = [
    path("ws/call/asterisk", AsteriskCallConsumer.as_asgi()),
    path("ws/call/jambonz", JambonzCallConsumer.as_asgi()),
]
