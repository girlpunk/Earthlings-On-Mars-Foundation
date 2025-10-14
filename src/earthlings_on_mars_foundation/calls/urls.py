from calls import views
from calls.admin import custom_admin_site
from django.urls import path
from django.views.decorators.csrf import csrf_exempt

urlpatterns = [
    path("", views.index, name="index"),
    path("hook/", csrf_exempt(views.new_call), name="new_call"),
    path("identify/", csrf_exempt(views.identified), name="identified"),
    path("code/<recruit_mission_id>/", csrf_exempt(views.code), name="code"),
    path("status/", csrf_exempt(views.status), name="status"),
    path("speech/<id>/", views.speech, name="speech"),
    path("admin/", custom_admin_site.urls),
]
