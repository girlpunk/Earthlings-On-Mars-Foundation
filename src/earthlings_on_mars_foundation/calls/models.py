"""Database models."""

from __future__ import annotations

from enum import IntEnum
from typing import ClassVar

from django.db import models


class Recruit(models.Model):
    """Player."""

    missions = models.ManyToManyField("Mission", through="RecruitMission")
    NPCs = models.ManyToManyField("NPC", through="RecruitNPC")

    def __str__(self) -> str:
        """Get the recruit number."""
        return f"Recruit {self.pk}"


class NPC(models.Model):
    """Not player."""

    name = models.CharField(max_length=200, unique=True)
    extension = models.PositiveSmallIntegerField(
        help_text="What number is dialled (B-Number) to reach this NPC",
    )
    introduction = models.TextField(
        help_text="This text is given to the player the first time they call",
    )
    recruits = models.ManyToManyField(Recruit, through="RecruitNPC")

    def __str__(self) -> str:
        """Get the NPC name."""
        return self.name

    class Meta:
        """Database table metadata."""

        verbose_name = "NPC"
        indexes: ClassVar[list[models.Index]] = [models.Index(fields=["extension"])]


class RecruitNPC(models.Model):
    """Player-NPC relation."""

    recruit = models.ForeignKey(Recruit, on_delete=models.CASCADE)
    NPC = models.ForeignKey(NPC, on_delete=models.CASCADE)
    contacted = models.BooleanField(default=False)

    # TODO(Me): Reputations https://github.com/girlpunk/Earthlings-On-Mars-Foundation/issues/1
    score = models.IntegerField(default=0)


class MissionTypes(IntEnum):
    """Built-in ways a mission can work."""

    # Call from a specific location
    LOCATION = 1

    # Call another NPC
    NPC = 2

    # Call back with a code from a physical item
    CODE = 3

    # Two players complete an action at the same time
    # TODO(Me): Implement https://github.com/girlpunk/Earthlings-On-Mars-Foundation/issues/2
    # TOGETHER = 4

    # Get an arbitrary input, we don't really care what
    COUNT = 5

    # Custom scripted mission
    LUA = 6

    @classmethod
    def choices(cls: IntEnum) -> list[tuple[int, str]]:
        """Iterate over mission types."""
        return [(key.value, key.name) for key in cls]


class Location(models.Model):
    """Known locations players can call from."""

    name = models.CharField(max_length=200, unique=True)
    extension = models.PositiveSmallIntegerField(
        help_text="What number do calls originate from (A-Number) when placed from this location",
    )

    def __str__(self) -> str:
        """Get the location name."""
        return self.name

    class Meta:
        """Database table metadata."""

        indexes: ClassVar[list[models.Index]] = [models.Index(fields=["extension"])]


class Mission(models.Model):
    """Takss for players."""

    name = models.CharField(max_length=200, unique=True)
    give_text = models.TextField(
        help_text="This text is given to the player when they initially begin the mission",
    )
    reminder_text = models.TextField(
        help_text="This text is given to the player when the call back about the mission, without meeting the completion criteria",
    )
    completion_text = models.TextField(
        help_text="This text is given to the player when they successfully complete the mission",
    )
    issued_by = models.ForeignKey(
        NPC,
        on_delete=models.PROTECT,
        help_text="Which NPC can start the mission",
    )
    type = models.IntegerField(choices=MissionTypes.choices())
    points = models.IntegerField(
        help_text="How many points will be given to the user upon completion",
    )
    followup_mission = models.ForeignKey(
        "Mission",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        help_text="Which mission will automatically be started upon completion of this mission",
    )
    priority = models.PositiveSmallIntegerField(
        default=5,
        help_text="If multiple missions are available, ones with higher priorities are preferred",
    )
    only_start_from = models.ForeignKey(
        "Location",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="only_start_from",
        help_text="If set, this mission can only be started from the specified location",
    )
    prerequisites = models.ManyToManyField(
        "self",
        through="MissionPrerequisite",
        through_fields=("mission", "prerequisite"),
        help_text="Missions that need to be done before this mission",
    )
    dependents = models.ManyToManyField(
        "self",
        through="MissionPrerequisite",
        through_fields=("prerequisite", "mission"),
        help_text="Missions that need this mission to be done first",
    )
    instances = models.ManyToManyField(Recruit, through="RecruitMission")
    repeatable = models.BooleanField()

    # time-limitations
    not_before = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Only start this mission if the current date/time is after the specified date/time",
    )
    not_after = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Only start this mission if the current date/time is before the specified date/time",
    )
    cancel_after_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Cancel the mission if it is outstanding after the specified date/time",
    )
    cancel_after_tries = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Cancel the mission if the player calls its NPC without completing it this many times",
    )
    cancel_text = models.TextField(
        max_length=2000,
        blank=True,
        help_text="This text is given to the player when the mission is cancelled",
    )

    # Call from a specific location
    call_back_from = models.ForeignKey(
        Location,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )

    # Call another NPC
    call_another = models.ForeignKey(
        NPC,
        on_delete=models.PROTECT,
        related_name="call_another",
        null=True,
        blank=True,
    )

    # Call back with a code from a physical item
    code = models.PositiveIntegerField(null=True, blank=True)
    incorrect_text = models.TextField(
        blank=True,
        help_text="Given to the user when the get the code wrong",
    )

    # Lua
    lua = models.TextField(help_text="Lua script for custom requirements", blank=True)

    def __str__(self) -> str:
        """Get the name of the mission."""
        return self.name

    class Meta:
        """Database table metadata."""

        constraints: ClassVar[list[models.CheckConstraint]] = [
            models.CheckConstraint(
                condition=models.Q(priority__gte=1, priority__lte=10),
                name="priority",
            ),
        ]


class MissionPrerequisite(models.Model):
    """Missions that must be completed before other missions."""

    mission = models.ForeignKey(Mission, on_delete=models.PROTECT)
    prerequisite = models.ForeignKey(
        Mission,
        on_delete=models.PROTECT,
        related_name="prerequisite",
    )

    def __str__(self) -> str:
        """Get a summary of the requirement."""
        return f"{self.mission} needs {self.prerequisite}"

    class Meta:
        """Database table metadata."""

        indexes: ClassVar[list[models.Index]] = [
            models.Index(fields=["mission"]),
        ]


class RecruitMission(models.Model):
    """Recruit-mission data."""

    recruit = models.ForeignKey(Recruit, on_delete=models.CASCADE)
    mission = models.ForeignKey(Mission, on_delete=models.CASCADE)
    started = models.DateTimeField(auto_now_add=True)
    finished = models.DateTimeField(null=True, blank=True)
    completed = models.BooleanField(default=False)

    # Call back with a code from a physical item
    code_tries = models.PositiveSmallIntegerField(null=True)

    # Two players complete an action at the same time
    # TODO(Me): Implement https://github.com/girlpunk/Earthlings-On-Mars-Foundation/issues/2

    # Get an arbitrary input, we don't really care what
    count_value = models.PositiveIntegerField(null=True)

    # Lua state
    state = models.JSONField(default=dict, blank=True)

    def __str__(self) -> str:
        """Get a summary of the mission assignment."""
        return f"{self.recruit} doing {self.mission}"

    class Meta:
        """Database table metadata."""

        indexes: ClassVar[list[models.Index]] = [
            models.Index(fields=["recruit", "completed"]),
        ]


class CallLog(models.Model):
    """Logging data."""

    call_id = models.CharField(unique=True, max_length=64, primary_key=True)
    recruit = models.ForeignKey(
        Recruit,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    NPC = models.ForeignKey(NPC, on_delete=models.CASCADE, null=True, blank=True)
    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    date = models.DateTimeField(auto_now_add=True)
    duration = models.PositiveIntegerField(default=0)
    digits = models.PositiveIntegerField(default=0)
    completed = models.BooleanField(default=False)
    success = models.BooleanField(default=False)

    def __str__(self) -> str:
        """Get the call ID."""
        return self.call_id


class Speech(models.Model):
    """Pre-recorded speech."""

    NPC = models.ForeignKey(NPC, on_delete=models.CASCADE, null=True, blank=True)
    text = models.TextField()
    recording = models.FileField()
    tts = models.BooleanField(default=True)
