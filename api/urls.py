from django.urls import path
from . import views


urlpatterns = [
    path('user/login', views.UserView.as_view({'post': 'login'})),
    path('user/logout', views.UserView.as_view({'get': 'logout'})),
    path('users', views.UserView.as_view({'get': 'list'})),
    path('user/<pk>', views.UserView.as_view(
        {
            'get': 'retrieve',
            'put': 'update',
            'delete': 'destroy'
        })),

    path('events', views.EventView.as_view(
        {
            'get': 'list',
            'post': 'create'
        })),
    path('event/<pk>', views.EventView.as_view(
        {
            'get': 'retrieve',
            'put': 'update',
            'delete': 'destroy',
            'patch': 'add_image'
        }
    )),
    path('event/<pk>/like', views.UserView.as_view({'put': 'like'}))
]
