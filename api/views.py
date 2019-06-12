import uuid,os
from . import helpers
import operator
import requests
import json
from dateutil.parser import parse as datetime_parse
from collections import OrderedDict

from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt
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
    HTTP_302_FOUND
)
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework import filters
from rest_framework.pagination import PageNumberPagination
from rest_framework_jwt.settings import api_settings

from api import models
from api import serializers
from api import permissions

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

 

class UserView(ModelViewSet):
    queryset = models.User.objects.all().order_by('id')
    serializer_class = serializers.UserSerializer

    def get_permissions(self):
        permission_dict = {
            'list': [IsAdminUser],
            'retrieve': [permissions.IsOwner],
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

    def create(self, request):
        serializer = serializers.CreateUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_user = models.User.objects.create_user(
            username = serializer.data.get('username'),
            password = serializer.data.get('password'),
            is_staff = serializer.data.get('is_staff'),
            email = serializer.data.get('email')
        )
        serializer = self.get_serializer(new_user)
        return Response(data=serializer.data ,status=HTTP_201_CREATED)

    def update(self, request):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        instance
        self.perform_update(serializer)
        
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
                    'error': 'Invalid Credentials'
                },
                status=HTTP_404_NOT_FOUND
            )

        return Response(gen_token_response(user), status=HTTP_200_OK)
        

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
            title = data.get('title', ''),
            description = data.get('description', ''),
            location = data.get('location', ''),
            start = data.get('start', ''),
            end = data.get('end', '')
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
            return Response(
            {
                'action': 'participate',
                'event': event.id,
                'user': user.id,
                'conflict_event': serializer_conflict_event
            },
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
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination
    def search(self, request):
        if request.data.__contains__('keywords'):
            keywords = request.data.get('keywords')
            # keywords = helpers.filter_special_character(keywords)
            event = models.Event.objects.extra(
                tables = ['api_event'],
                where=[
                    "MATCH (title, description, location) " +
                    f"AGAINST (%s IN NATURAL LANGUAGE MODE) "
                ],
                params = [keywords]
            )
        else:
            event = models.Event.objects.all()

        # continue search by categories
        if request.data.__contains__('categories'):
            categories = [t.strip() for t in request.data.get('categories').split(',') if t.strip() != '']
        else:
            categories = []
        if len(categories) >0:
            event = event.filter(categories__name__in=categories)

        # continue search by date ranges
        query1 = Q(start__lte=request.data.get('start')) & Q(end__gte=request.data.get('start'))   # /////[///     ]
        query2 = Q(start__lte=request.data.get('end')) & Q(end__gte=request.data.get('end'))       #      [    ////]/////  
        query3 = Q(start__gte=request.data.get('start')) & Q(end__lte=request.data.get('end'))     #      [  ////  ]

        if request.data.__contains__('start') and request.data.__contains__('end'):
            start_time = datetime_parse(request.data.get('start'))
            end_time = datetime_parse(request.data.get('end'))
            if start_time >= end_time:
                return Response({
                    'detail': 'Invalid datetime range.'
                },
                status=HTTP_400_BAD_REQUEST)
            event = event.filter(query1 | query2 | query3)
        elif request.data.__contains__('start'):
            event = event.filter(query1)
        elif request.data.__contains__('end'):
            event = event.filter(query2)

        # sorting
        event = event.order_by('start', 'end')

        # paging result
        page = self.paginate_queryset(event)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)

        
        # return response
        return Response(serializer.data)


class GoogleSignInView(ModelViewSet):
    permission_classes = [AllowAny]
    #step 01: send auth request to google server
    def auth(self, request):
        google_oauth_server = f"https://accounts.google.com/o/oauth2/v2/auth?client_id={settings.SOCIAL_GOOGLE_CLIENT_ID}"
        google_oauth_server += f"&redirect_uri={settings.SOCIAL_GOOGLE_REDIRECT_URI}"
        google_oauth_server += "&scope=profile email openid&access_type=offline&prompt=consent"
        google_oauth_server += "&response_type=code&include_granted_scopes=true"
        return Response(headers={'Location': google_oauth_server},status=HTTP_302_FOUND)
    
    def callback(self, request):
        # step 02: recieve code from google
        data = {
            'code': request.GET.get('code'),
            'client_id': settings.SOCIAL_GOOGLE_CLIENT_ID,
            'client_secret': settings.SOCIAL_GOOGLE_CLIENT_SECRET,
            'grant_type': 'authorization_code',
            'redirect_uri': settings.SOCIAL_GOOGLE_REDIRECT_URI,
        }

        google_token_server = "https://www.googleapis.com/oauth2/v4/token"
        google_api_userinfo = "https://www.googleapis.com/oauth2/v2/userinfo"


        # step 03: get tooken
        response = requests.post(url=google_token_server, data=data)
        response = json.loads(response.text)
        if 'error_description' in response:
            return Response(data=response, status=HTTP_400_BAD_REQUEST)
        
        # step 04: retrieve user email
        headers = {
            'Authorization' : f"Bearer {response['access_token']}"
        }
        response = requests.get(url=google_api_userinfo, headers=headers)
        response = json.loads(response.text)
        
        # step 05: find and return user token
        try:
            user = models.User.objects.get(email=response['email'])
            token, _ = Token.objects.get_or_create(user=user)
            return Response(
                gen_token_response(user),
                status=HTTP_200_OK
            )
        except models.User.DoesNotExist:
            return Response(data={'detail': 'user not found'}, status=HTTP_404_NOT_FOUND)


            