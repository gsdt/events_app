# Generated by Django 2.2.2 on 2019-06-10 09:13

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0007_auto_20190610_1004'),
    ]

    operations = [
        migrations.AlterField(
            model_name='like',
            name='event',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='likes', to='api.Event'),
        ),
    ]
