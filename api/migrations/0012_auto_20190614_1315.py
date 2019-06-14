# Generated by Django 2.2.2 on 2019-06-14 06:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0011_remove_user_facebook_id'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='event',
            name='is_notified',
        ),
        migrations.AddField(
            model_name='event',
            name='task_id',
            field=models.CharField(max_length=36, null=True, unique=True),
        ),
    ]