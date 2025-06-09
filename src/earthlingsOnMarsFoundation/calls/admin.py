from django.contrib import admin

# Register your models here.
from . import models

admin.site.register(models.Recruit)
admin.site.register(models.NPC)
admin.site.register(models.Location)
admin.site.register(models.RecruitMission)
admin.site.register(models.MissionPrerequisites)
admin.site.register(models.CallLog)

class PrerequisiteInline(admin.TabularInline):
    model = models.MissionPrerequisites
    fk_name = "mission"
    extra = 1

class MissionAdmin(admin.ModelAdmin):
    list_display = ["name", "issued_by"]
    search_fields = ["name", "give_text", "completion_text"]
    fieldsets = [
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
        ("Time Limitations", {"fields": ["not_before", "not_after", "cancel_after_time", "cancel_after_tries", "cancel_text"]}),
        ("Call from a specific location", {"fields": ["call_back_from"], "classes": ["collapse"]}),
        ("Call another NPC", {"fields": ["call_another"], "classes": ["collapse"]}),
        ("Call back with a code from a physical item", {"fields": ["code"], "classes": ["collapse"]})
    ]

    inlines = [PrerequisiteInline]


admin.site.register(models.Mission, MissionAdmin)
