from rest_framework import serializers
from api.models import User, Event, Category, Like, Comment, Participate, Image

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'is_superuser', 'facebook_id', 'created_at', 'updated_at')

class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ('id', 'image', 'event', 'created_at')

class EventSerializer(serializers.ModelSerializer):
    images = ImageSerializer(many=True)
    like = serializers.SerializerMethodField()
    comment = serializers.SerializerMethodField()
    participate = serializers.SerializerMethodField()

    def get_like(self, obj):
        return Like.objects.filter(event=obj).count()

    def get_comment(self, obj):
        saved_comment = Comment.objects.filter(event=obj)
        serializers = CommentSerializer(saved_comment, many=True)
        return serializers.data
    def get_participate(self, obj):
        saved_participate = Participate.objects.filter(event=obj)
        serializers = ParticipateSerializer(saved_participate, many=True)
        return serializers.data

    class Meta:
        model = Event
        fields = ('id', 'title', 'description', 'start', 'end', 'location', 'like', 'comment', 'participate', 'images', 'created_at', 'updated_at')

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'created_at', 'updated_at')

class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = ('id', 'event', 'user', 'created_at', 'updated_at')

class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ('id', 'event', 'user', 'content', 'created_at', 'updated_at')

class ParticipateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Participate
        fields = ('id', 'event', 'user','created_at', 'updated_at')




