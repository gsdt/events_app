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

class SearchView(ModelViewSet):
    serializer_class = serializers.SimpleEventSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination
    def search(self, request):
        if request.GET.__contains__('keywords'):
            keywords = request.GET.get('keywords')
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
        if request.GET.__contains__('categories'):
            categories = [t.strip() for t in request.GET.get('categories').split(',') if t.strip() != '']
        else:
            categories = []
        if len(categories) >0:
            event = event.filter(categories__name__in=categories)

        # continue search by date ranges
        query1 = Q(start__lte=request.GET.get('start')) & Q(end__gte=request.GET.get('start'))   # /////[///     ]
        query2 = Q(start__lte=request.GET.get('end')) & Q(end__gte=request.GET.get('end'))       #      [    ////]/////  
        query3 = Q(start__gte=request.GET.get('start')) & Q(end__lte=request.GET.get('end'))     #      [  ////  ]

        if request.GET.__contains__('start') and request.GET.__contains__('end'):
            start_time = datetime_parse(request.GET.get('start'))
            end_time = datetime_parse(request.GET.get('end'))
            if start_time >= end_time:
                return Response({
                    'detail': 'Invalid datetime range.'
                },
                status=HTTP_400_BAD_REQUEST)
            event = event.filter(query1 | query2 | query3)
        elif request.GET.__contains__('start'):
            event = event.filter(query1)
        elif request.GET.__contains__('end'):
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
        return Response(serializer.GET)
