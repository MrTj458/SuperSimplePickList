from django.urls import path

from .views import app, auth, auth_callback, uninstalled, pick_list

app_name = 'app'
urlpatterns = [
    path('', app, name='app'),
    path('list/', pick_list, name='list'),
    path('auth/', auth, name='auth'),
    path('authcallback/', auth_callback, name='authcallback'),
    path('uninstalled/', uninstalled, name='uninstalled')
]
