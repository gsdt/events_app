import uuid,os

from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_200_OK
)
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from api import models
from api import serializers

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
            return Response({'message': 'Invalid Credentials'},
                            status=HTTP_404_NOT_FOUND)
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'token': token.key},
            status=HTTP_200_OK)

    def logout(self, request):
        request.user.auth_token.delete()
        return Response(
            {
                'message': 'Logout success'
            },status=HTTP_200_OK)

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
            title = data['title'],
            description = data['description'],
            location = data['location'],
            start = data['start'],
            end = data['end']
        )
        if new_event.start > new_event.end:
            return Response(
                data = {'message': 'Start date must be smaller than end date.'}, 
                status=HTTP_400_BAD_REQUEST
            )
        new_event.save()
        print(new_event.id)
        for file in request.FILES:
            file_extension = os.path.splitext(request.FILES[file].name)[1]
            print(file_extension)
            if file_extension not in [".jpg", ".jpeg", ".png", ".gif", ".tiff"]:
                continue
            image = models.Image(event=new_event)
            image.image.save(f'{uuid.uuid4()}{file_extension}', request.FILES[file])
            image.save()

        return Response({'message': 'Created new event.'}, status=HTTP_200_OK)

    def add_image(self, request, pk=None):
        event = self.get_object()

        for file in request.FILES:
            file_extension = os.path.splitext(request.FILES[file].name)[1]
            if file_extension not in [".jpg", ".jpeg", ".png", ".gif", ".tiff"]:
                continue
            image = models.Image(event=event)
            image.image.save(f'{uuid.uuid4()}{file_extension}', request.FILES[file])
            image.save()

        return Response({'message': 'Added new image'}, status=HTTP_200_OK)

    # def like(self, request, pk=None):
    #     event = self.get_object()
    #     user = request.user

    #     like = models.Like.objects.get(user=user, event=event)
    #     print(like)

    #     return Response(status=HTTP_200_OK)
    

            