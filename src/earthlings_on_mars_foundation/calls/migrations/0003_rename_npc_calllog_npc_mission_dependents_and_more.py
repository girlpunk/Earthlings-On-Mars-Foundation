# Generated by Django 5.2.2 on 2025-06-14 13:53

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('calls', '0002_alter_mission_call_another_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='calllog',
            old_name='npc',
            new_name='NPC',
        ),
        migrations.AddField(
            model_name='mission',
            name='dependents',
            field=models.ManyToManyField(help_text='Missions that need this mission to be done first', through='calls.MissionPrerequisites', through_fields=('prerequisite', 'mission'), to='calls.mission'),
        ),
        migrations.AddField(
            model_name='npc',
            name='introduction',
            field=models.TextField(default='', help_text='This text is given to the player the first time they call'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='recruit',
            name='missions',
            field=models.ManyToManyField(through='calls.RecruitMission', to='calls.mission'),
        ),
        migrations.AlterField(
            model_name='mission',
            name='prerequisites',
            field=models.ManyToManyField(help_text='Missions that need to be done before this mission', through='calls.MissionPrerequisites', through_fields=('mission', 'prerequisite'), to='calls.mission'),
        ),
        migrations.CreateModel(
            name='RecruitNPC',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('contacted', models.BooleanField()),
                ('NPC', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='calls.npc')),
                ('recruit', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='calls.recruit')),
            ],
        ),
        migrations.AddField(
            model_name='npc',
            name='recruits',
            field=models.ManyToManyField(through='calls.RecruitNPC', to='calls.recruit'),
        ),
        migrations.AddField(
            model_name='recruit',
            name='NPCs',
            field=models.ManyToManyField(through='calls.RecruitNPC', to='calls.npc'),
        ),
    ]
