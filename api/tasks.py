# Create your tasks here
from __future__ import absolute_import, unicode_literals
from celery import shared_task
from api import models
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

@shared_task
def add(x, y):
    return x + y


@shared_task
def mul(x, y):
    return x * y


@shared_task
def xsum(numbers):
    return sum(numbers)

@shared_task
def notify_incomming_event(event_id):
    event = models.Event.objects.get(pk=event_id)
    participants = models.Participate.objects.filter(event = event)
    for e in participants:
        user = e.user
        html_message = render_to_string(
            'incomming_event.html', 
            {
                'event_title': event.title,
                'username': user.username
            }
        )

        message = strip_tags(html_message)

        send_mail(
            "[alert] Your event will start shortly.",
            message,
            settings.EMAIL_HOST_USER, [user.email],
            html_message=html_message
        )

@shared_task
def notify_changed_event(event_id):
    event = models.Event.objects.get(pk=event_id)
    participants = models.Participate.objects.filter(event = event)
    for e in participants:
        user = e.user

        html_message = render_to_string(
            'event_changed_email.html', 
            {
                'event_title': event.title,
                'event_start_time': event.start.strftime("%Y-%m-%d %H:%M:%S"),
                'event_end_time': event.end.strftime("%Y-%m-%d %H:%M:%S"),
                'event_location': event.location,
                'username': user.username
            }
        )

        message = strip_tags(html_message)

        send_mail(
            "[alert] Event that your participate has been changed.",
            message,
            settings.EMAIL_HOST_USER, [user.email],
            html_message=html_message
        )