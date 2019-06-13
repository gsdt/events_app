import uuid,os
from . import helpers
import operator
import requests
import json
from dateutil.parser import parse as datetime_parse
from collections import OrderedDict

from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.conf import settings
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser, DjangoObjectPermissions
from rest_framework.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_302_FOUND,
    HTTP_204_NO_CONTENT
)
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework import filters
from rest_framework.pagination import PageNumberPagination


from api import models
from api import serializers
from api import permissions

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.shortcuts import render
from django.utils.safestring import mark_safe

# bellow is view for testing...

class NotifyView(ModelViewSet):
    def ping(self, request, pk=None):
        helpers.send_notifcation(pk, {
            'status': 'ping!'
        })
        return Response('Done!', status=HTTP_200_OK)

def view_event_detail(request, event_id):
    event = get_object_or_404(models.Event, pk=event_id)
    return render(request, 'room.html', {
        'event_title': event.title,
        'room_name_json': mark_safe(json.dumps(event_id))
    })