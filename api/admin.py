from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Event, Image, Like, Comment, Participate, Category

class InlineImage(admin.TabularInline):
    model = Image
class CustomEventAdmin(admin.ModelAdmin):
    inlines = [InlineImage]
    fields = ('title', 'description', 'location', 'start', 'end')

# Register your models here.
admin.site.register(User, UserAdmin)
admin.site.register(Event, CustomEventAdmin)
admin.site.register(Image)
admin.site.register(Like)
admin.site.register(Comment)
admin.site.register(Participate)
admin.site.register(Category)



