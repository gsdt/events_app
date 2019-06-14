from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.db.models import Q
from rest_framework_jwt.settings import api_settings

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from collections import OrderedDict
from api import serializers

import threading
import string

valid_file_extension = [".jpg", ".jpeg", ".png", ".gif", ".tiff"]

EVENT_CHANGE = 1

# class SendEmailThread(threading.Thread):
#     def __init__(self, participants, old_event, new_event, action):
#         self.participants = participants
#         self.old_event = old_event
#         self.new_event = new_event
#         self.action = action
#         threading.Thread.__init__(self)

#     def send_event_changed_notifcation(self):
#         email_list = []
#         for e in self.participants:
#             user = e.user

#             html_message = render_to_string(
#                 'event_changed_email.html', 
#                 {
#                     'event_title': self.new_event.title,
#                     'event_start_time': self.new_event.start.strftime("%Y-%m-%d %H:%M:%S"),
#                     'event_end_time': self.new_event.end.strftime("%Y-%m-%d %H:%M:%S"),
#                     'event_location': self.new_event.location,
#                     'username': user.username
#                 }
#             )

#             message = strip_tags(html_message)

#             send_mail(
#                 "[alert] Event that your participate has been changed.",
#                 message,
#                 settings.EMAIL_HOST_USER, [user.email],
#                 html_message=html_message
#             )

#     def run(self):
#         if self.action == EVENT_CHANGE:
#             self.send_event_changed_notifcation()

#         print("Done send email jobs!")

def filter_special_character(input):
    output = ''
    for c in input:
        if c in string.ascii_letters + string.digits + ' ':
            output += c
    return output

def gen_token_response(user):
    jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
    jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

    payload = jwt_payload_handler(user)
    token = jwt_encode_handler(payload)
    return OrderedDict(
        user=serializers.UserSerializer(user).data,
        token=token,
        expired=api_settings.JWT_EXPIRATION_DELTA,
        type=api_settings.JWT_AUTH_HEADER_PREFIX
    )

def send_notifcation(event_id, data):
    layer = get_channel_layer()
    async_to_sync(layer.group_send)('group_'+event_id, {
        'type': 'events.alarm',
        'content': data
    })