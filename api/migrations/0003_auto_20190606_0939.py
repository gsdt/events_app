# Generated by Django 2.2.2 on 2019-06-06 02:39

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_auto_20190605_1525'),
    ]

    operations = [
        migrations.RenameField(
            model_name='image',
            old_name='main_image',
            new_name='image',
        ),
        migrations.RemoveField(
            model_name='image',
            name='description',
        ),
        migrations.RemoveField(
            model_name='image',
            name='title',
        ),
        migrations.RemoveField(
            model_name='image',
            name='updated_at',
        ),
    ]
