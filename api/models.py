from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

# Create your models here.
class Event(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(null=True)
    location = models.CharField(max_length=255)
    start = models.DateTimeField()
    end = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def clean(self):
        # Don't allow end <= start
        if self.start >= self.end:
            raise ValidationError(_('End time must be later than start time.'))

    def __str__(self):
        return self.title

class Image(models.Model):
    title = models.CharField(max_length=255, null=True)
    main_image = models.ImageField(upload_to="images")
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    description = models.TextField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def clean(self):
        # default value for title
        self.title = self.main_image.name

    def __str__(self):
        return title
    

class Category(models.Model):
    name = models.CharField(max_length=255)
    events = models.ManyToManyField(Event)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class User(AbstractUser):
    facebook_id = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Like(models.Model):
    event = models.OneToOneField(Event, on_delete=models.CASCADE)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} liked {self.event}"

    class Meta:
        unique_together = ('event', 'user')
    

class Participate(models.Model):
    event = models.OneToOneField(Event, on_delete=models.CASCADE)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} participated {self.event}"

    class Meta:
        unique_together = ('event', 'user')

class Comment(models.Model):
    event = models.OneToOneField(Event, on_delete=models.CASCADE)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        # Don't empty comment
        if len(self.content.strip()) == 0:
            raise ValidationError(_('Empty comment is not allowed.'))

    def __str__(self):
        return f"{self.name} commented on {self.event}: {self.content}"
    


