from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from . import views

urlpatterns = [
    path("",          views.index,                   name="index"),
    path("hook/",     csrf_exempt(views.new_call),   name="new_call"),
    path("identify/", csrf_exempt(views.identified), name="identified"),
    path("code/",     csrf_exempt(views.code),       name="code"),
    path("status/",   csrf_exempt(views.status),     name="status")
]
