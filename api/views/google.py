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
                helpers.gen_token_response(user),
                status=HTTP_200_OK
            )
        except models.User.DoesNotExist:
            return Response(data={'detail': 'user not found'}, status=HTTP_404_NOT_FOUND)