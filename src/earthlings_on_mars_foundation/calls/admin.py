
from __future__ import annotations

from typing import ClassVar

from django.contrib import admin

from calls import models
from djangoeditorwidgets.widgets import MonacoEditorWidget
from django import forms
from django.urls import path
from django.template.response import TemplateResponse
from datetime import datetime, timedelta, time
from django.db.models import Sum

def admin_dashboard(request):
    context = {
        'call_count': models.CallLog.objects.count(),
        'recruit_count': models.Recruit.objects.count(),
    }
    return TemplateResponse(request, 'admin/dashboard.html', context)

class CustomAdminSite(admin.AdminSite):
    site_header = "Earthlings on Mars Foundation"
    index_title = "Dashboard"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('dashboard/', self.admin_view(admin_dashboard), name='dashboard'),
        ]
        return custom_urls + urls

custom_admin_site = CustomAdminSite(name='custom_admin')

custom_admin_site.register(models.Location)
custom_admin_site.register(models.RecruitMission)
custom_admin_site.register(models.MissionPrerequisite)

class NPCAdmin(admin.ModelAdmin):
    list_display: ClassVar[list[str]] = ["name", "extension"]
    search_fields: ClassVar[list[str]] = ["name", "extension"]

custom_admin_site.register(models.NPC, NPCAdmin)

class RecruitNPCInline(admin.TabularInline):
    verbose_name = "NPC Relationships"
    model = models.RecruitNPC
    fk_name = "recruit"
    extra = 0

class RecruitAdmin(admin.ModelAdmin):
    inlines = [RecruitNPCInline]

custom_admin_site.register(models.Recruit, RecruitAdmin)

class CallLogAdmin(admin.ModelAdmin):
    list_display = ["recruit", "NPC", "location", "date", "duration"]
    change_list_template = "admin/calllog_list.html"

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}

        today = datetime.now().date()
        tomorrow = today + timedelta(1)

        today_start = datetime.combine(today, time())
        today_end = datetime.combine(tomorrow, time())

        calls_today = models.CallLog.objects.filter(date__lte=today_end, date__gte=today_start)

        extra_context['current_calls'] = models.CallLog.objects.filter(completed=False).count()
        extra_context['total_calls_today'] = calls_today.filter(completed=True).count()
        extra_context['failed_calls_today'] = calls_today.filter(completed=True, success=False).count()

        today_aggregate = calls_today.aggregate(Sum("digits"), Sum("duration"))
        extra_context['digits_today'] = today_aggregate["digits__sum"]
        extra_context['duration_today'] = today_aggregate["duration__sum"]

        extra_context['total_calls'] = models.CallLog.objects.count()
        total_aggregate = models.CallLog.objects.aggregate(Sum("digits"), Sum("duration"))
        extra_context['total_digits'] = total_aggregate["digits__sum"]
        extra_context['total_duration'] = total_aggregate["duration__sum"]

        return super().changelist_view(
            request, extra_context=extra_context,
        )

custom_admin_site.register(models.CallLog, CallLogAdmin)

class PrerequisiteInline(admin.TabularInline):
    model = models.MissionPrerequisite
    fk_name = "mission"
    extra = 1

class MissionAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(MissionAdminForm, self).__init__(*args, **kwargs)
        self.fields['lua'].widget = MonacoEditorWidget(name="default", language="lua")

class MissionAdmin(admin.ModelAdmin):
    list_display: ClassVar[list[str]] = ["name", "issued_by"]
    search_fields: ClassVar[list[str]] = ["name", "give_text", "completion_text"]
    fieldsets: ClassVar[list[set[str, dict[str, list[str]]]]] = [
        (
            None,
            {
                "fields": [
                    "name",
                    "give_text",
                    "reminder_text",
                    "completion_text",
                    "issued_by",
                    "type",
                    "priority",
                    "points",
                    "followup_mission",
                    "only_start_from",
                    #"prerequisites",
                    "repeatable"
                ]
            }
        ),
        ("Time Limitations", {
            "fields": ["not_before", "not_after", "cancel_after_time", "cancel_after_tries", "cancel_text"],
            "description": "These settings affect when the mission can be given to a recruit"
        }),
        ("Call from a specific location", {"fields": ["call_back_from"], "classes": ["collapse"]}),
        ("Call another NPC", {"fields": ["call_another"], "classes": ["collapse"]}),
        ("Call back with a code from a physical item", {"fields": ["code"], "classes": ["collapse"]}),
        ("Lua script", {"fields": ["lua"], "classes": ["collapse"]})
    ]
    inlines: ClassVar[list[str]] = [PrerequisiteInline]
    form = MissionAdminForm

custom_admin_site.register(models.Mission, MissionAdmin)
