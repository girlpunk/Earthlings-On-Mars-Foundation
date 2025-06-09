from datetime import datetime

from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.urls import reverse

from . import jambon, models


def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")


def new_call(request, npc_id):
    return JsonResponse(jambon.gather(
        "Please enter your recruit number to connect your call. If you've lost your multipass and need a replacement recruit number, press 0",
        request.build_absolute_uri(reverse("new_call_identified", kwargs={"npc_id": npc_id})),
        min_digits=1,
        max_digits=4), safe=False)

def new_call_identified(request, npc_id):
    try:
        recruit_id = request.POST["dtmf"]
    except KeyError:
        print(request.POST)
        # Redisplay the question voting form.
        return HttpResponseRedirect(request.build_absolute_uri(reverse("new_call", kwargs={"npc_id": npc_id})))

    output = []

    if recruit_id == "0":
        # New recruit
        recruit = models.Recruit()
        recruit.save()
        output += [jambon.say(f"OK let's see, scanner says you're recruit {recruit.id}. You got that? {recruit.id}, don't forget it.")]
    else:
        # Existing recruit
        recruit = models.Recruit.objects.get(id=recruit_id)

        # Verify the recruit number
        if recruit is None or len(recruit) == 0:
            return JsonResponse(jambon.say("Sorry, that number was not recognised"))

        output += jambon.say("Caller verified!")

    # Find what NPC is being called
    npc = models.NPC.objects.get(extension=request.GET["call_to"])

    if npc is None:
        return JsonResponse(jambon.say("Unable to identify what NPC you are calling"))

    # TODO: Check for any "call NPC" missions going to this NPC, complete if needed
    call_npc_missions = models.RecruitMission.objects.filter(recruit=recruit, mission__type==models.MissionTypes.NPC, completed=False)

    for mission in call_npc_missions
        output += _complete_mission(mission)


    only_start_from = models.ForeignKey("Location", on_delete=models.PROTECT, null=True, blank=True, related_name="only_start_from", help_text="If set, this mission can only be started from the specified locatio>
    prerequisites = models.ManyToManyField("self", through="MissionPrerequisites", related_name="prerequisites", through_fields=('mission', 'prerequisite'))
    instances = models.ManyToManyField(Recruit, through="RecruitMission")
    repeatable = models.BooleanField()





    # TODO: Check for any "call from location" missions from this NPC, complete if needed

    # TODO: Check for any "get code" missions from this NPC, complete if needed

    # TODO: Check for any existing missions from this NPC, send reminder

    # TODO: Issue new mission


#"Hey, we've got a pressure anomaly near shaft 4. Can you patch it? Thre should be a phone round there somewhere, give me a call when you get there"



def _complete_mission(recruitMission):
    recruitMission.completed = True
    recruitMission.finished = datetime.now()
    recruitMission.save()

    recruitMission.recruit.score += recruitMission.mission.points
    recruitMission.recruit.save()

    return recruitMission.mission.completion_text


def _start_mission(mission, recruit):
    # create RecruitMission
    # get output
