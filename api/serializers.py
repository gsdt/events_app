from rest_framework import serializers
from api.models import User, Event, Category, Like, Comment, Participate, Image

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'is_superuser', 'facebook_id')

class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ('id', 'image', 'created_at')

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name')


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
    likes_count = serializers.SerializerMethodField()
    comments = serializers.SerializerMethodField()
    participants = serializers.SerializerMethodField()
    categories = CategorySerializer(read_only=True, many=True)

    def validate(self, data):
        if data['start'] >= data['end']:
            raise serializers.ValidationError({'end_date':'End date must be after start date.'})
        return data

    def get_likes_count(self, obj):
        return Like.objects.filter(event=obj).count()

    def get_comments(self, obj):
        saved_comment = Comment.objects.filter(event=obj)
        serializers = CommentSerializer(saved_comment, many=True)
        return serializers.data

    def get_participants(self, obj):
        saved_participate = Participate.objects.filter(event=obj)
        serializers = ParticipateSerializer(saved_participate, many=True)
        return serializers.data

    class Meta:
        model = Event
        fields = ('id', 'title', 'description', 'start', 'end', 'location', 'categories', 'likes_count', 'comments', 'participants', 'images', 'created_at', 'updated_at')


class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = ('id', 'event', 'user', 'created_at', 'updated_at')

class CommentSerializer(serializers.ModelSerializer):
    def validate(self, data):
        comment = data['content']
        if len(comment.strip()) == 0:
            raise serializers.ValidationError({'content': 'Empty comment is not allowed.'})
    user = UserSerializer(read_only=True)
    class Meta:
        model = Comment
        fields = ('id', 'event', 'user', 'content', 'created_at', 'updated_at')

class ParticipateSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = Participate
        fields = ('id', 'event', 'user','created_at', 'updated_at')




