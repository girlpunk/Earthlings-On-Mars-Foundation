
from __future__ import annotations

from typing import ClassVar

from django.contrib import admin

from . import models

admin.site.register(models.Location)
admin.site.register(models.RecruitMission)
admin.site.register(models.MissionPrerequisite)

class NPCAdmin(admin.ModelAdmin):
    list_display: ClassVar[list[str]] = ["name", "extension"]
    search_fields: ClassVar[list[str]] = ["name", "extension"]

admin.site.register(models.NPC, NPCAdmin)

class RecruitNPCInline(admin.TabularInline):
    verbose_name = "NPC Relationships"
    model = models.RecruitNPC
    fk_name = "recruit"
    extra = 0

class RecruitAdmin(admin.ModelAdmin):
    inlines = [RecruitNPCInline]

admin.site.register(models.Recruit, RecruitAdmin)

class CallLogAdmin(admin.ModelAdmin):
    list_display = ["recruit", "NPC", "location", "date", "duration"]

admin.site.register(models.CallLog, CallLogAdmin)

class PrerequisiteInline(admin.TabularInline):
    model = models.MissionPrerequisite
    fk_name = "mission"
    extra = 1

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
        ("Call back with a code from a physical item", {"fields": ["code"], "classes": ["collapse"]})
    ]

    inlines: ClassVar[list[str]] = [PrerequisiteInline]


admin.site.register(models.Mission, MissionAdmin)
