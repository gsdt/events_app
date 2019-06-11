from django.urls import path, include
from . import views


urlpatterns = [
    # user
    path('user/login', views.UserView.as_view({'post': 'login'})),
    path('user/logout', views.UserView.as_view({'get': 'logout'})),
    path('users', views.UserView.as_view({'get': 'list'})),
    path('user/<pk>', views.UserView.as_view(
        {
            'get': 'retrieve',
            'put': 'update',
            'delete': 'destroy'
        })),

    # event
    path('events', views.SearchView.as_view(
        {
            'get': 'search'
        })),
    path('events', views.EventView.as_view(
        {
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
    path('event/<pk>/like', views.EventView.as_view({'put': 'like'})),
    path('event/<pk>/likes', views.EventView.as_view({'get': 'likes_list'})),

    path('event/<pk>/participate', views.EventView.as_view({'put': 'participate'})),
    path('event/<pk>/participants', views.EventView.as_view({'get': 'participants_list'})),

    path('event/<pk>/comment', views.EventView.as_view({'post': 'comment'})),
    path('event/<pk>/comments', views.EventView.as_view({'get': 'comments_list'})),


    # comment
    path('comment/<pk>', views.CommentView.as_view(
        {
            'get': 'retrieve',
            'put': 'update',
            'delete': 'destroy'
        }
    )),

    # category
    path('categories', views.CategoryView.as_view(
        {
            'get': 'list',
            'post': 'create'
        }
    )),
    path('category/<pk>', views.CategoryView.as_view(
        {
            'get': 'retrieve',
            'put': 'update',
            'delete': 'destroy'
        }
    )),
    # search
    path('search', views.SearchView.as_view(
        {'get': 'search'}
    )),

    # google sign in
    path('auth/', views.GoogleSignInView.as_view(
        {'get': 'auth'}
    )),
    path('auth/callback', views.GoogleSignInView.as_view(
        {'get': 'callback'}
    ))
]