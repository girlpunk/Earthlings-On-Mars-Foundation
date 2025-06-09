from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from . import views

urlpatterns = [
    path("",                       views.index,                            name="index"),
    path("<int:npc_id>/",          csrf_exempt(views.new_call),            name="new_call"),
    path("<int:npc_id>/identify/", csrf_exempt(views.new_call_identified), name="new_call_identified")
]
