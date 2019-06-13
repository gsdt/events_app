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

class CommentView(ModelViewSet):
    serializer_class = serializers.CommentSerializer
    queryset = models.Comment.objects.all()

    permission_classes = [permissions.IsOwner]

    def update(self, request, pk=None):
        comment = self.get_object()
        content = request.data.get('content', '')
        if content.strip() == '':
            return Response(
                {
                    'detail': 'content must not be empty'
                },
                status=HTTP_400_BAD_REQUEST
            )
        comment.content = content
        comment.save()

        return Response(
            data=self.get_serializer(comment).data,
            status=HTTP_200_OK
        )

    def destroy(self, request, pk=None):
        comment = self.get_object()
        event = comment.event
        user = comment.user
        comment_id = comment.id
        comment.delete()

        return_action = OrderedDict(
            action='remove comment',
            event=serializers.NotifyEventSerializer(event).data,
            user=serializers.SimpleUserSerializer(user).data,
        )

        helpers.send_notifcation(str(event.id), return_action)

        return Response(
            return_action,
            HTTP_204_NO_CONTENT
        )