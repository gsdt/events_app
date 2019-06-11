# Generated by Django 2.2.2 on 2019-06-11 07:14

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0008_auto_20190610_1613'),
    ]

    operations = [
        migrations.AlterField(
            model_name='participate',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='events_participated', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterIndexTogether(
            name='comment',
            index_together={('event', 'user')},
        ),
        migrations.AlterIndexTogether(
            name='event',
            index_together={('start', 'end')},
        ),
    ]