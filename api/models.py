from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

# Create your models here.

class CommonInfo(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Event(CommonInfo):
    title = models.CharField(max_length=255)
    description = models.TextField(null=True)
    location = models.CharField(max_length=255)
    start = models.DateTimeField()
    end = models.DateTimeField()
    is_notified = models.BooleanField(default=False)

    def __str__(self):
        return self.title

    class Meta:
        index_together = [
            ('start', 'end')
        ]

class Image(CommonInfo):
    image = models.ImageField(upload_to="images")
    event = models.ForeignKey(Event, related_name='images', on_delete=models.CASCADE)
    
    def __str__(self):
        return self.image.name
    

class Category(CommonInfo):
    name = models.CharField(max_length=255, unique=True)
    events = models.ManyToManyField(Event, related_name='categories')

    def __str__(self):
        return self.name

class User(AbstractUser):
    email = models.EmailField(unique=True)
    # class Meta:
        # unique

class Like(CommonInfo):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user} liked {self.event}"

    class Meta:
        unique_together = ('event', 'user')
    

class Participate(CommonInfo):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='events_participated')

    def __str__(self):
        return f"{self.user} participated {self.event}"

    class Meta:
        unique_together = ('event', 'user')

class Comment(CommonInfo):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()

    def __str__(self):
        return f"{self.user} commented on {self.event}: {self.content}"

    class Meta:
        index_together = [
            ('event', 'user')
        ]
    


