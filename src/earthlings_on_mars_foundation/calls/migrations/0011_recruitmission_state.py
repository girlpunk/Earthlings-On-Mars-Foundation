# Generated by Django 5.2.2 on 2025-06-22 14:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('calls', '0010_calllog_completed_calllog_success_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='recruitmission',
            name='state',
            field=models.JSONField(default=dict),
        ),
    ]
