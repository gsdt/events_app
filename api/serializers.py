from rest_framework import serializers
from api.models import User, Event, Category, Like, Comment, Participate, Image
from rest_framework.pagination import PageNumberPagination
from django.core.paginator import Paginator
from django.conf import settings
from collections import OrderedDict

class CreateUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'is_staff')

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'is_staff')

class SimpleUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username')

class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ('id', 'image', 'created_at')

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name')


class SupperSimpleEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ('id', 'title', 'description')

class EventConflictSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ('id', 'title', 'description', 'start', 'end')

class NotifyEventSerializer(serializers.ModelSerializer):
    likes_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    participants_count = serializers.SerializerMethodField()

    def get_likes_count(self, obj):
        return Like.objects.filter(event=obj).count()

    def get_comments_count(self, obj):
        return Comment.objects.filter(event=obj).count()

    def get_participants_count(self, obj):
        return Participate.objects.filter(event=obj).count()

    class Meta:
        model = Event
        fields = ('id', 'title', 'likes_count', 'comments_count', 'participants_count')


class SimpleEventSerializer(serializers.ModelSerializer):
    images = ImageSerializer(many=True, read_only=True)
    likes_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    participants_count = serializers.SerializerMethodField()
    categories = CategorySerializer(many=True)

    def get_likes_count(self, obj):
        return Like.objects.filter(event=obj).count()

    def get_comments_count(self, obj):
        return Comment.objects.filter(event=obj).count()

    def get_participants_count(self, obj):
        return Participate.objects.filter(event=obj).count()

    class Meta:
        model = Event
        fields = ('id', 'title', 'description', 'start', 'end', 'location', 'categories', 'likes_count', 'comments_count', 'participants_count', 'images', 'created_at', 'updated_at')

class EventSerializer(serializers.ModelSerializer):
    images = ImageSerializer(many=True, read_only=True)
    likes = serializers.SerializerMethodField()
    comments = serializers.SerializerMethodField()
    participants = serializers.SerializerMethodField()
    categories = CategorySerializer(read_only=True, many=True)

    def validate(self, data):
        if data['start'] >= data['end']:
            raise serializers.ValidationError({'end':'End date must be after start date.'})
        if data.get('title', '').strip() == '':
            raise serializers.ValidationError({'title': 'Event must have a non empty title'})
        data['title'] = data['title'].strip()
        data['description'] = data['description'].strip()
        data['location'] = data['location'].strip()
        return data

    def get_likes(self, obj):
        saved_likes = Like.objects.filter(event=obj)
        serializers = SimpleLikeSerializer(saved_likes, many=True)
        return self.get_paging(serializers.data, 'likes', obj)

    def get_comments(self, obj):        
        saved_comment = Comment.objects.filter(event=obj)
        serializers = SimpleCommentSerializer(saved_comment, many=True)
        return self.get_paging(serializers.data, 'comments', obj)

    def get_participants(self, obj):
        saved_participate = Participate.objects.filter(event=obj)
        serializers = SimpleParticipateSerializer(saved_participate, many=True)
        return self.get_paging(serializers.data, 'paticipants', obj)

    def get_paging(self, serializers, path, obj):
        page_size = settings.REST_FRAMEWORK['PAGE_SIZE']
        if len(serializers) <= page_size:
            return OrderedDict(
                count = len(serializers),
                next = "null",
                previous = "null",
                results = serializers
            )
        else:
            return OrderedDict(
                count = len(serializers),
                next = f"http://{settings.SERVER_DOMAIN}:{settings.SERVER_PORT}/api/event/{obj.id}/{path}?page=2",
                previous = "null",
                results = serializers[:page_size]
            )
        

    class Meta:
        model = Event
        fields = ('id', 'title', 'description', 'start', 'end', 'location', 'categories', 'likes', 'comments', 'participants', 'images', 'created_at', 'updated_at')

class SimpleLikeSerializer(serializers.ModelSerializer):
    user = SimpleUserSerializer(read_only=True)
    class Meta:
        model = Like
        fields = ('id', 'user', 'created_at', 'updated_at')

class LikeSerializer(serializers.ModelSerializer):
    user = SimpleUserSerializer(read_only=True)
    class Meta:
        model = Like
        fields = ('id', 'event', 'user', 'created_at', 'updated_at')

class SimpleCommentSerializer(serializers.ModelSerializer):
    user = SimpleUserSerializer(read_only=True)
    class Meta:
        model = Comment
        fields = ('id', 'user', 'content', 'created_at', 'updated_at')

class CommentSerializer(serializers.ModelSerializer):
    def validate(self, data):
        comment = data['content']
        if len(comment.strip()) == 0:
            raise serializers.ValidationError({'content': 'Empty comment is not allowed.'})
    user = SimpleUserSerializer(read_only=True)
    class Meta:
        model = Comment
        fields = ('id', 'event', 'user', 'content', 'created_at', 'updated_at')

class SimpleParticipateSerializer(serializers.ModelSerializer):
    user = SimpleUserSerializer(read_only=True)
    class Meta:
        model = Participate
        fields = ('id', 'user','created_at', 'updated_at')

class ParticipateSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = Participate
        fields = ('id', 'event', 'user','created_at', 'updated_at')

class SearchSerializer(serializers.ModelSerializer):
    keywords = serializers.CharField()
    start = serializers.DateTimeField()
    end = serializers.DateField()




