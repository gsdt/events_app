import uuid,os
from . import helpers
import operator
import requests
import json
from dateutil.parser import parse as datetime_parse
from datetime import timedelta
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
from api import tasks

from celery.task.control import revoke

class EventView(ModelViewSet):
    queryset = models.Event.objects.all().order_by('start')
    serializer_class = serializers.EventSerializer

    def get_permissions(self):
        permission_dict = {
            'list': [IsAuthenticated],
            'retrieve': [IsAuthenticated],
            'create': [IsAdminUser],
            'update': [IsAdminUser],
            'partial_update': [IsAdminUser],
            'destroy': [IsAdminUser],
            'add_image': [IsAdminUser],
        }
        permission_classes = []
        if self.action in permission_dict:
            permission_classes = permission_dict[self.action]

        return [permission() for permission in permission_classes]

    def list(self, request):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = serializers.SimpleEventSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = serializers.SimpleEventSerializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = request.data
        new_event = models.Event(
            title = data.get('title').strip(),
            description = data.get('description').strip(),
            location = data.get('location').strip(),
            start = data.get('start').strip(),
            end = data.get('end').strip()
        )
        new_event.save()

        # now we trying to add relationship with categories
        categories = [t.strip() for t in request.data.get('categories', '').split(',') if t.strip() != '']
        for cate_name in categories:
            category = models.Category.objects.filter(name=cate_name)
            if category.count() == 0:
                new_category = models.Category(name=cate_name)
                new_category.save()
                new_category.events.add(new_event)
            else:
                category = models.Category.objects.get(name=cate_name)
                category.events.add(new_event)

        # now we uploading file
        for file in request.FILES:
            file_extension = os.path.splitext(request.FILES[file].name)[1]
            print(file_extension)
            if file_extension not in helpers.valid_file_extension:
                continue
            image = models.Image(event=new_event)
            image.image.save(f'{uuid.uuid4()}{file_extension}', request.FILES[file])
            image.save()

        serializer = serializers.EventSerializer(new_event)

        # add notify task
        new_event = models.Event.objects.get(pk=new_event.id)
        new_event.task_id = tasks.notify_incomming_event.apply_async(
            (new_event.id,), 
            eta=new_event.start + timedelta(hours=-1)).id
        new_event.save()

        return Response(
            serializer.data, 
            status=HTTP_200_OK)

    def add_image(self, request, pk=None):
        event = self.get_object()

        for file in request.FILES:
            file_extension = os.path.splitext(request.FILES[file].name)[1]
            if file_extension not in helpers.valid_file_extension:
                continue
            image = models.Image(event=event)
            image.image.save(f'{uuid.uuid4()}{file_extension}', request.FILES[file])
            image.save()

        return Response({'message': 'Added new image'}, status=HTTP_200_OK)

    def update(self, request, pk=None):
        event = self.get_object()
        event.categories.clear()

        old_event = models.Event(start=event.start, end=event.end, location=event.location)

        # now we trying to add relationship with categories
        categories = [t.strip() for t in request.data.get('categories', '').split(',')]
        for cate_name in categories:
            category = models.Category.objects.filter(name=cate_name)
            if category.count() == 0:
                new_category = models.Category(name=cate_name)
                new_category.save()
                new_category.events.add(event)
            else:
                category = models.Category.objects.get(name=cate_name)
                category.events.add(event)

        serializer = self.get_serializer(event, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # now we are sending email if location or time range changed.
        try:
            if old_event.start != event.start:
                # skip old notify
                revoke(event.task_id)
                # update new nofity
                event.task_id = tasks.notify_incomming_event.apply_async(
                    (event.id,),
                    eta=event.start+timedelta(hours=-1)
                )
                event.save()

            if old_event.start != event.start or old_event.end != event.end or old_event.location != event.location:
                tasks.notify_changed_event.delay(event.id)

        except expression as identifier:
            print(identifier)

        return Response(serializer.data, HTTP_200_OK)

    def destroy(self, request, pk=None):
        event = self.get_object()
        revoke(event.task_id)
        event.delete()
        return Response(status=HTTP_204_NO_CONTENT)

    def comment(self, request, pk=None):
        event = self.get_object()
        user = request.user
        content = request.data.get("content").strip()

        if content == '':
            return Response(
                {
                    'detail': 'Empty comment are not allowed.'
                },
                status=HTTP_400_BAD_REQUEST
            )

        comment = models.Comment(user = user, event=event, content=content)
        comment.save()

        return_action = OrderedDict(
            action='comment',
            content=content,
            event = serializers.NotifyEventSerializer(event).data,
            user=serializers.SimpleUserSerializer(user).data
        )

        helpers.send_notifcation(pk, return_action)

        return Response(
            return_action,
            status=HTTP_200_OK
        )

    def comments_list(self, requests, pk=None):
        event = self.get_object()
        comments = event.comments.all().order_by('created_at')
        
        page = self.paginate_queryset(comments)
        if page is not None:
            serializer = serializers.SimpleCommentSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = serializers.SimpleCommentSerializer(queryset, many=True)

        return Response(serializer.data)

    def like(self, request, pk=None):
        event = self.get_object()
        user = request.user
        action = 'unlike'
        try:
            like = models.Like.objects.get(user=user, event=event)
            like.delete()
        except models.Like.DoesNotExist as identifier:
            like = models.Like(user = user, event=event)
            like.save()
            action = 'like'

        return_action = OrderedDict(
            action=action,
            event=serializers.NotifyEventSerializer(event).data,
            user=serializers.SimpleUserSerializer(user).data
        )

        helpers.send_notifcation(pk, return_action)

        return Response(
            return_action,
            status=HTTP_200_OK)

    def likes_list(self, requests, pk=None):
        event = self.get_object()
        likes = event.likes.all().order_by('created_at')
        
        page = self.paginate_queryset(likes)
        if page is not None:
            serializer = serializers.SimpleLikeSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = serializers.SimpleLikeSerializer(queryset, many=True)

        return Response(serializer.data)

    def participate(self, request, pk=None):
        event = self.get_object()
        user = request.user
        action = 'leave'
        serializer_conflict_event = []
        try:
            participate = models.Participate.objects.get(user=user, event=event)
            participate.delete()
        except models.Participate.DoesNotExist as identifier:
            # find conflict events
            query1 = Q(event__start__lte=event.start) & Q(event__end__gte=event.start)  # /////[///     ]
            query2 = Q(event__start__lte=event.end)   & Q(event__end__gte=event.end)    #      [    ////]/////    
            query3 = Q(event__start__gte=event.start) & Q(event__end__lte=event.end)    #      [  ////  ]


            participants_list = user.events_participated.filter(query1 | query2 | query3).values_list("event", flat=True)
            conflict_events = models.Event.objects.filter(id__in=participants_list).order_by('start')
            serializer_conflict_event = serializers.EventConflictSerializer(conflict_events, many=True).data
            
            # update participations
            participate = models.Participate(user = user, event=event)
            participate.save()
            action = 'participate'

        return_action = OrderedDict(
            action=action,
            event=serializers.NotifyEventSerializer(event).data,
            user=serializers.SimpleUserSerializer(user).data,
        )

        helpers.send_notifcation(pk, return_action)

        return_action['conflicts']=serializer_conflict_event

        return Response(
            return_action,
            status=HTTP_200_OK)

    def participants_list(self, requests, pk=None):
        event = self.get_object()
        participants = event.participants.all().order_by('created_at')
        
        page = self.paginate_queryset(participants)
        if page is not None:
            serializer = serializers.SimpleParticipateSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = serializers.SimpleParticipateSerializer(queryset, many=True)

        return Response(serializer.data)