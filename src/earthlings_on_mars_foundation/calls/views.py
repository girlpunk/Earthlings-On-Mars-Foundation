import contextlib
import json
from datetime import datetime

from calls import jambon, models
from django.db.models import Count, Exists, F, OuterRef, Q
from django.http import FileResponse, HttpResponse, HttpResponseRedirect, JsonResponse
from django.urls import reverse


def index(request):
    return HttpResponse("Hello, world.")


def new_call(request):
    return JsonResponse(
        [
            jambon.gather(
                "Please enter your recruit number to connect your call. If you've lost your multipass and need a replacement recruit number, press 0",
                request.build_absolute_uri(reverse("identified")),
                min_digits=1,
                max_digits=4,
            ),
        ],
        safe=False,
    )


def identified(request):
    body = json.loads(request.body)
    output = []
    digits = 0

    if (
        "digits" not in body
        or (body["reason"] == "timeout" and body["digits"] != "0")
        or body["reason"] == "error"
    ):
        # Prompt for the input again
        return HttpResponseRedirect(request.build_absolute_uri(reverse("new_call")))

    recruit_id = body["digits"]

    if recruit_id == "0":
        # New recruit
        recruit = models.Recruit()
        recruit.save()

        number = " ".join(f"{recruit.id:04}")

        output += [
            jambon.say(
                f"OK let's see, scanner says you're recruit {number}. You got that? {number}, don't forget it!",
            ),
        ]
        digits = 1
    else:
        # Existing recruit
        try:
            recruit = models.Recruit.objects.get(id=recruit_id)
        except models.Recruit.DoesNotExist:
            # Verify the recruit number
            return JsonResponse(
                [jambon.say("Sorry, that number was not recognised")],
                safe=False,
            )

        output += [jambon.say("Caller verified!")]
        digits = 4

    # Find what NPC is being called
    try:
        npc = models.NPC.objects.get(extension=body["to"])
    except models.NPC.DoesNotExist:
        return JsonResponse([jambon.say("Unable to identify what NPC you are calling")])

    recruit_npc, created = models.RecruitNPC.objects.get_or_create(
        recruit=recruit,
        NPC=npc,
    )

    if created or not recruit_npc.contacted:
        output += [jambon.say(npc.introduction)]
        recruit_npc.contacted = True
        recruit_npc.save()

    location = _find_location(body["from"])
    _add_details_to_call(body["call_sid"], recruit, npc, location, digits)

    # Check for any "call NPC" missions going to this NPC, complete if needed
    npc_missions = models.RecruitMission.objects.filter(
        recruit=recruit,
        mission__type=models.MissionTypes.NPC,
        mission__call_another=npc,
        completed=False,
    )

    for mission in npc_missions:
        output += [_complete_mission(mission)]

    # Check for any "call from location" missions from this NPC, complete if needed
    location_missions = models.RecruitMission.objects.filter(
        recruit=recruit,
        mission__type=models.MissionTypes.LOCATION,
        mission__call_back_from=location,
        mission__issued_by=npc,
        completed=False,
    )

    for mission in location_missions:
        output += [_complete_mission(mission)]

    # Check for any "get code" missions from this NPC, complete if needed
    code_mission = models.RecruitMission.objects.filter(
        recruit=recruit,
        mission__type=models.MissionTypes.CODE,
        mission__issued_by=npc,
        completed=False,
    )

    if code_mission is not None and len(code_mission) > 0:
        mission = code_mission[0]
        # Get code prompt
        output += [
            jambon.gather(
                mission.mission.reminder_text,
                request.build_absolute_uri(
                    reverse("code", kwargs={"recruit_mission_id": mission.id}),
                ),
                min_digits=1,
            ),
        ]

        return JsonResponse(output, safe=False)

    # Check for any existing missions from this NPC, send reminder
    outstanding_missions = models.RecruitMission.objects.filter(
        recruit=recruit,
        mission__issued_by=npc,
        completed=False,
    )

    if len(outstanding_missions) > 0:
        for mission in outstanding_missions:
            output += [jambon.say(mission.mission.reminder_text)]
        return JsonResponse(output, safe=False)

    # Issue new mission
    output += [_get_mission(recruit, npc, location)]

    return JsonResponse(output, safe=False)


# "Hey, we've got a pressure anomaly near shaft 4. Can you patch it? Thre should be a phone round there somewhere, give me a call when you get there"


def code(request, recruit_mission_id):
    body = json.loads(request.body)

    recruit_mission = models.RecruitMission.objects.get(id=recruit_mission_id)

    if body["reason"] == "timeout" or body["reason"] == "error" or "digits" not in body:
        # Prompt for the input again

        return JsonResponse(
            [
                jambon.gather(
                    recruit_mission.mission.reminder_text,
                    request.build_absolute_uri(
                        reverse(
                            "code",
                            kwargs={"recruit_mission_id": recruit_mission.id},
                        ),
                    ),
                    min_digits=1,
                ),
            ],
            safe=False,
        )

    code = body["digits"]

    # Add digits to call log
    _add_details_to_call(
        body["call_sid"],
        recruit_mission.recruit,
        recruit_mission.mission.issued_by,
        None,
        len(code),
    )

    if code == str(recruit_mission.mission.code):
        # Correct code
        location = _find_location(body["from"])
        return JsonResponse(
            [
                _complete_mission(recruit_mission),
                _get_mission(
                    recruit_mission.recruit,
                    recruit_mission.mission.issued_by,
                    location,
                ),
            ],
            safe=False,
        )

    # Incorrect code
    return JsonResponse(
        [jambon.say(recruit_mission.mission.incorrect_text)],
        safe=False,
    )


def _get_mission(recruit, npc, location):
    now = datetime.utcnow()

    mission = (
        models.Mission.objects.annotate(
            total_prerequisites=Count(
                "prerequisites",
            ),  # Calculate total number of prerequisites
            completed_prerequisites=Count(  # And completed number of prerequisites
                models.MissionPrerequisite.objects.filter(
                    Q(mission=OuterRef("pk")),
                    Q(
                        Exists(
                            models.RecruitMission.objects.filter(
                                mission=OuterRef("prerequisite__id"),
                                recruit=recruit,
                            ),
                        ),
                    ),
                ).values("id"),
            ),
            followup_to=Count("mission"),
        )
        .filter(
            Q(issued_by=npc)  # Issued by the user the NPC is talking to
            & (
                Q(
                    only_start_from=location,
                )  # Issued from the location the user is calling from
                | Q(only_start_from=None)  # Or from any location
            )
            & Q(
                ~Exists(
                    models.RecruitMission.objects.filter(
                        mission=OuterRef("pk"),
                        recruit=recruit,
                        completed=True,
                    ),
                )
                | Q(repeatable=True),
            )  # User has not already completed, or the mission is repeatable
            & Q(
                total_prerequisites=F("completed_prerequisites"),
            )  # All prerequisites are complete
            & (
                Q(not_before__lte=now) | Q(not_before=None)
            )  # not before is before now (or unset)
            & (
                Q(not_after__gte=now) | Q(not_after=None)
            ),  # Not after is after now (or unset)
        )
        .order_by("-followup_to", "-priority")
        .first()
    )

    if mission is None:
        return jambon.say(
            "I don't have any more work for you at the moment, give me a call back later.",
        )

    recruitMission = models.RecruitMission()
    recruitMission.recruit = recruit
    recruitMission.mission = mission
    recruitMission.save()

    return jambon.say(mission.give_text)


def _complete_mission(recruit_mission):
    recruit_mission.completed = True
    recruit_mission.finished = datetime.utcnow()
    recruit_mission.save()

    recruit_mission.recruit.score += recruit_mission.mission.points
    recruit_mission.recruit.save()

    return jambon.say(recruit_mission.mission.completion_text)


def _add_details_to_call(call_sid, recruit, npc, location, digits):
    call, created = models.CallLog.objects.get_or_create(
        call_id=call_sid,
        defaults={"duration": 0, "digits": 0},
    )

    if npc is not None:
        call.NPC = npc
    if recruit is not None:
        call.recruit = recruit
    if location is not None:
        call.location = location
    if digits is not None:
        call.digits += digits

    call.save()


def _find_location(call_from):
    try:
        return models.Location.objects.get(extension=call_from)
    except (ValueError, models.Location.DoesNotExist):
        return None


def status(request):
    body = json.loads(request.body)

    call, created = models.CallLog.objects.get_or_create(
        call_id=body["call_sid"],
        defaults={"duration": 0, "digits": 0},
    )

    if call.NPC is None:
        with contextlib.suppress(models.NPC.DoesNotExist):
            call.NPC = models.NPC.objects.get(extension=body["to"])

    if call.location is None:
        call.location = _find_location(body["from"])

    if "duration" in body:
        call.duration = body["duration"]

    call.save()

    return HttpResponse("OK")


def speech(request, id):
    recording = models.Speech.get(id=id)

    return FileResponse(request, recording.recording)
