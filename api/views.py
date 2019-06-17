import uuid,os
from . import helpers
from functools import reduce
import operator

from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.utils.dateparse import parse_date
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser, DjangoObjectPermissions
from rest_framework.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_200_OK
)
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework import filters
from rest_framework.pagination import PageNumberPagination
from api import models
from api import serializers
from api import permissions

class UserView(ModelViewSet):
    queryset = models.User.objects.all().order_by('id')
    serializer_class = serializers.UserSerializer

    def get_permissions(self):
        permission_dict = {
            'list': [IsAdminUser],
            'retrieve': [IsAdminUser],
            'create': [IsAdminUser],
            'update': [IsAdminUser],
            'partial_update': [IsAdminUser],
            'destroy': [IsAdminUser],
            'login': [AllowAny],
            'logout': [IsAuthenticated]
        }
        permission_classes = []
        if self.action in permission_dict:
            permission_classes = permission_dict[self.action]
            
        return [permission() for permission in permission_classes]

    def login(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        if username is None or password is None:
            return Response({'message': 'Please provide both username and password'},
                            status=HTTP_400_BAD_REQUEST)
        user = authenticate(username=username, password=password)
        if not user:
            return Response(
                {
                    'message': 'Invalid Credentials'
                },
                status=HTTP_404_NOT_FOUND
            )
        token, _ = Token.objects.get_or_create(user=user)
        return Response(
            {
                'token': token.key
            },
            status=HTTP_200_OK
        )

    def logout(self, request):
        request.user.auth_token.delete()
        return Response(
            {
                'message': 'Logout success'
            },status=HTTP_200_OK
        )

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

    def create(self, request):
        data = request.data
        new_event = models.Event(
            title = data.get('title', ''),
            description = data.get('description', ''),
            location = data.get('location', ''),
            start = data.get('start', ''),
            end = data.get('end', '')
        )
        if new_event.start > new_event.end:
            return Response(
                data = {'message': 'Start date must be smaller than end date.'}, 
                status=HTTP_400_BAD_REQUEST
            )
        new_event.save()
        # now we trying to add relationship with categories
        categories = [t.strip() for t in request.data.get('categories', '').split(',')]
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
            print('DEBUG', image.image.url)

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
            if old_event.start != event.start or old_event.end != event.end or old_event.location != event.location:
                print("Datetime or location has changed!")
                participants = models.Participate.objects.filter(event = event)
                
                helpers.SendEmailThread(participants, old_event, event, helpers.EVENT_CHANGE).start()

        except expression as identifier:
            print(identifier)
            pass

        return Response(serializer.data, HTTP_200_OK)

    def comment(self, request, pk=None):
        event = self.get_object()
        user = request.user
        content = request.data.get("content")

        comment = models.Comment(user = user, event=event, content=content)
        comment.save()
        return Response(
        {
            'action': 'comment',
            'event': event.id,
            'user': user.id,
            'content': content
        },
        status=HTTP_200_OK)

    def like(self, request, pk=None):
        event = self.get_object()
        user = request.user

        try:
            like = models.Like.objects.get(user=user, event=event)
            like.delete()
            return Response(
                {
                    'action': 'unlike',
                    'event': event.id,
                    'user': user.id
                },
                status=HTTP_200_OK)
        except models.Like.DoesNotExist as identifier:
            like = models.Like(user = user, event=event)
            like.save()
            return Response(
                {
                    'action': 'like',
                    'event': event.id,
                    'user': user.id
                },
                status=HTTP_200_OK)

    def participate(self, request, pk=None):
        event = self.get_object()
        user = request.user

        try:
            participate = models.Participate.objects.get(user=user, event=event)
            participate.delete()
            return Response(
            {
                'action': 'leave',
                'event': event.id,
                'user': user.id
            },
            status=HTTP_200_OK)
        except models.Participate.DoesNotExist as identifier:
            participate = models.Participate(user = user, event=event)
            participate.save()
            return Response(
            {
                'action': 'participate',
                'event': event.id,
                'user': user.id
            },
            status=HTTP_200_OK)

class CommentView(ModelViewSet):
    serializer_class = serializers.CommentSerializer
    queryset = models.Comment.objects.all()

    permission_classes = [permissions.IsOwner]

    def update(self, request, pk=None):
        comment = self.get_object()
        content = request.data.get('content')
        comment.content = content
        comment.save()

        return Response(
        status=HTTP_200_OK)
    
class CategoryView(ModelViewSet):
    serializer_class = serializers.CategorySerializer
    queryset = models.Category.objects.all()
    
    def get_permissions(self):
        permission_dict = {
            'list': [IsAuthenticated],
            'retrieve': [IsAuthenticated],
            'create': [IsAdminUser],
            'update': [IsAdminUser],
            'partial_update': [IsAdminUser],
            'destroy': [IsAdminUser]
        }
        permission_classes = []
        if self.action in permission_dict:
            permission_classes = permission_dict[self.action]

        return [permission() for permission in permission_classes]

class SearchView(ModelViewSet):
    serializer_class = serializers.SimpleEventSerializer
    queryset = models.Event.objects.all()
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination
    def search(self, request):
        # search by keyword on title, description, location
        keywords_list = [keyword.strip() for keyword in request.data.get('keywords', '').split(',')]
        if len(keywords_list) > 0:
            first_kword = keywords_list[0]
            query = Q(title__icontains=first_kword) | Q(description__icontains=first_kword)
            for kword in keywords_list:
                query.add(
                    Q(title__icontains=kword) | Q(description__icontains=kword) | Q(location__icontains=kword),
                    query.connector
                )
            event = models.Event.objects.filter(query)
        else:
            event = models.Event.objects.all()

        # continue search by categories
        if request.data.__contains__('categories'):
            categories = [t.strip() for t in request.data.get('categories').split(',')]
        else:
            categories = []
        if len(categories) >0:
            event = event.filter(categories__name__in=categories)

        # continue search by date ranges
        if request.data.__contains__('start'):
            event = event.filter(start__gte=request.data.get('start'))
        if request.data.__contains__('end'):
            event = event.filter(end__lte=request.data.get('end'))

        # sorting
        event = event.order_by('start')

        # paging result
        page = self.paginate_queryset(event)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)

        # return response
        return Response(serializer.data)

            