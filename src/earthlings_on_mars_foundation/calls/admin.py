"""Admin panel for game."""

from __future__ import annotations

import datetime
from pathlib import Path
from typing import Any, ClassVar

import yaml
from calls import models
from django import forms
from django.contrib import admin
from django.db.models import Sum
from django.http import HttpRequest, HttpResponse
from django.template.response import TemplateResponse
from django.urls import path
from django_no_queryset_admin_actions import (
    NoQuerySetAdminActionsMixin,
    no_queryset_action,
)
from djangoeditorwidgets.widgets import MonacoEditorWidget


def admin_dashboard(request: HttpRequest) -> HttpResponse:
    """Page for Custom dashboard."""
    context = {
        "call_count": models.CallLog.objects.count(),
        "recruit_count": models.Recruit.objects.count(),
    }
    return TemplateResponse(request, "admin/dashboard.html", context)


class CustomAdminSite(admin.AdminSite):
    """Top-level admin metadata."""

    site_header = "Earthlings on Mars Foundation"
    index_title = "Dashboard"

    def get_urls(self) -> list:
        """Add custom URL for dashboard page."""
        urls = super().get_urls()
        custom_urls = [
            path("dashboard/", self.admin_view(admin_dashboard), name="dashboard"),
            path("sync/", self.admin_view(load_from_repo_page), name="load"),
        ]
        return custom_urls + urls


custom_admin_site = CustomAdminSite(name="custom_admin")

custom_admin_site.register(models.Location)
custom_admin_site.register(models.RecruitMission)
custom_admin_site.register(models.MissionPrerequisite)


class NPCAdmin(admin.ModelAdmin):
    """Admin pages for NPCs."""

    list_display: ClassVar[list[str]] = ["name", "extension"]
    search_fields: ClassVar[list[str]] = ["name", "extension"]


custom_admin_site.register(models.NPC, NPCAdmin)


class RecruitNPCInline(admin.TabularInline):
    """Admin pages for RecruitNPC Inline editor."""

    verbose_name = "NPC Relationships"
    model = models.RecruitNPC
    fk_name = "recruit"
    extra = 0


class RecruitAdmin(admin.ModelAdmin):
    """Admin pages for recruits."""

    inlines: ClassVar = [RecruitNPCInline]


custom_admin_site.register(models.Recruit, RecruitAdmin)


class CallLogAdmin(admin.ModelAdmin):
    """Admin pages for call logs."""

    list_display: ClassVar = ["recruit", "NPC", "location", "date", "duration"]
    change_list_template = "admin/calllog_list.html"

    def changelist_view(self, request: HttpRequest, extra_context: dict | None = None) -> HttpResponse:
        """Get metrics for log page."""
        extra_context = extra_context or {}

        today = datetime.datetime.now(tz=datetime.UTC).date()
        tomorrow = today + datetime.timedelta(1)

        today_start = datetime.datetime.combine(today, datetime.time())
        today_end = datetime.datetime.combine(tomorrow, datetime.time())

        calls_today = models.CallLog.objects.filter(
            date__lte=today_end,
            date__gte=today_start,
        )

        extra_context["current_calls"] = models.CallLog.objects.filter(
            completed=False,
        ).count()
        extra_context["total_calls_today"] = calls_today.filter(completed=True).count()
        extra_context["failed_calls_today"] = calls_today.filter(
            completed=True,
            success=False,
        ).count()

        today_aggregate = calls_today.aggregate(Sum("digits"), Sum("duration"))
        extra_context["digits_today"] = today_aggregate["digits__sum"]
        extra_context["duration_today"] = today_aggregate["duration__sum"]

        extra_context["total_calls"] = models.CallLog.objects.count()
        total_aggregate = models.CallLog.objects.aggregate(
            Sum("digits"),
            Sum("duration"),
        )
        extra_context["total_digits"] = total_aggregate["digits__sum"]
        extra_context["total_duration"] = total_aggregate["duration__sum"]

        return super().changelist_view(
            request,
            extra_context=extra_context,
        )


custom_admin_site.register(models.CallLog, CallLogAdmin)


class PrerequisiteInline(admin.TabularInline):
    """Inline editor for mission prerequisites."""

    model = models.MissionPrerequisite
    fk_name = "mission"
    extra = 1


class MissionAdminForm(forms.ModelForm):
    """Form for editing missions."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa:ANN401
        """Prepare form."""
        super().__init__(*args, **kwargs)
        self.fields["lua"].widget = MonacoEditorWidget(name="default", language="lua")


@no_queryset_action(description="Load from repo")
def load_from_repo_action(_: HttpRequest) -> None:
    """Load missions from the repo, as an admin action."""
    actual_load_from_repo()


def load_from_repo_page(_: HttpRequest) -> None:
    """Load missions from the repo, as an HTTP request."""
    actual_load_from_repo()


def actual_load_from_repo() -> HttpResponse:
    """Load missions from the repo, actual implementation."""
    source = Path("/repo")

    load_locations(source)
    load_npcs(source)

    return HttpResponse("OK")


def load_locations(source: Path) -> None:
    """Load locations."""
    locations = (source / "locations").iterdir()
    for location_path in locations:
        with location_path.open(encoding="utf-8") as f:
            location = yaml.safe_load(f)

            db_location, _ = models.Location.objects.get_or_create(
                pk=location["id"],
                defaults={
                    "pk": location["id"],
                    "extension": location["extension"],
                },
            )

            db_location.name = location["name"]
            db_location.extension = location["extension"]

            db_location.save()


def load_npcs(source: Path) -> None:
    """Load NPCs."""
    npcs = (source / "NPCs").iterdir()
    for npc_path in npcs:
        with (npc_path / "npc.yaml").open(encoding="utf-8") as f:
            npc = yaml.safe_load(f)

            db_npc, _ = models.NPC.objects.get_or_create(
                pk=npc["id"],
                defaults={
                    "pk": npc["id"],
                    "extension": npc["extension"],
                },
            )

            db_npc.name = npc["name"]
            db_npc.extension = npc["extension"]
            db_npc.introduction = npc["introduction"]

            db_npc.save()

        # Load Missions
        for mission_path in (npc_path / "missions").glob("**/*.yaml"):
            with mission_path.open(encoding="utf-8") as f:
                mission = yaml.safe_load(f)

                update_mission(mission, mission_path, db_npc)


def update_mission(mission: dict, path: Path, db_npc: models.NPC) -> None:
    """Update a mission."""
    db_mission, _ = models.Mission.objects.get_or_create(
        pk=mission["id"],
        defaults={
            "pk": mission["id"],
            "type": models.MissionTypes[mission["type"]],
            "points": mission["points"],
            "repeatable": mission["repeatable"],
            "issued_by_id": db_npc.pk,
        },
    )

    db_mission.issued_by_id = db_npc.pk
    db_mission.name = mission["name"]
    db_mission.give_text = mission["giveText"]
    db_mission.reminder_text = mission["reminderText"]
    db_mission.completion_text = mission["completionText"]

    db_mission.type = models.MissionTypes[mission["type"]]
    db_mission.points = mission["points"]

    db_mission.save()

    update_mission_metadata(mission, db_mission)
    update_mission_completion(mission, path, db_mission)


def update_mission_metadata(mission: dict, db_mission: models.Mission) -> None:  # noqa:C901
    """Update the metadata for a mission."""
    db_mission.followup_mission_id = None
    if "followup_mission" in mission:
        db_mission.followup_mission_id = mission["followup_mission"]

    if "priority" in mission:
        db_mission.priority = mission["priority"]
    if "onlyStartFrom" in mission:
        db_mission.only_start_from = mission["onlyStartFrom"]

    db_mission.prerequisites.clear()
    if "prerequisites" in mission:
        for m in mission["prerequisites"]:
            db_mission.prerequisites.add(m)

    db_mission.dependents.clear()
    if "dependents" in mission:
        for m in mission["dependents"]:
            db_mission.dependents.add(m)

    db_mission.repeatable = mission["repeatable"]

    if "notBefore" in mission:
        db_mission.not_before = datetime.datetime.fromisoformat(
            mission["notBefore"],
            tz=datetime.UTC,
        )
    if "notAfter" in mission:
        db_mission.not_after = datetime.datetime.fromisoformat(
            mission["notAfter"],
            tz=datetime.UTC,
        )
    if "cancelAfterTime" in mission:
        db_mission.cancel_after_time = datetime.datetime.fromisoformat(
            mission["cancelAfterTime"],
            tz=datetime.UTC,
        )
    if "cancelAfterTries" in mission:
        db_mission.cancel_after_tries = mission["cancelAfterTries"]
    if "cancelText" in mission:
        db_mission.cancel_text = mission["cancelText"]


def update_mission_completion(mission: dict, path: Path, db_mission: models.Mission) -> None:
    """Update the completion requirements for a mession."""
    if "callBackFrom" in mission:
        db_mission.call_back_from = mission["callBackFrom"]

    if "callAnother" in mission:
        db_mission.call_another = mission["callAnother"]

    if "code" in mission:
        db_mission.code = mission["code"]
    if "incorrectText" in mission:
        db_mission.incorrect_text = mission["incorrectText"]

    if db_mission.type == models.MissionTypes.LUA:
        db_mission.lua = path.with_suffix(".lua").read_text(encoding="utf-8")

    db_mission.save()


class MissionAdmin(NoQuerySetAdminActionsMixin, admin.ModelAdmin):
    """Admin pages for missions."""

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
                    # "prerequisites",
                    "repeatable",
                ],
            },
        ),
        (
            "Time Limitations",
            {
                "fields": [
                    "not_before",
                    "not_after",
                    "cancel_after_time",
                    "cancel_after_tries",
                    "cancel_text",
                ],
                "description": "These settings affect when the mission can be given to a recruit",
            },
        ),
        (
            "Call from a specific location",
            {"fields": ["call_back_from"], "classes": ["collapse"]},
        ),
        ("Call another NPC", {"fields": ["call_another"], "classes": ["collapse"]}),
        (
            "Call back with a code from a physical item",
            {"fields": ["code"], "classes": ["collapse"]},
        ),
        ("Lua script", {"fields": ["lua"], "classes": ["collapse"]}),
    ]
    inlines: ClassVar[list[str]] = [PrerequisiteInline]
    form = MissionAdminForm

    actions: ClassVar = [load_from_repo_action]


custom_admin_site.register(models.Mission, MissionAdmin)
