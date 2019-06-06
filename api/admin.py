from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Event, Image, Like, Comment, Participate
# Register your models here.
admin.site.register(User, UserAdmin)
admin.site.register(Event)
admin.site.register(Image)
admin.site.register(Like)
admin.site.register(Comment)
admin.site.register(Participate)



