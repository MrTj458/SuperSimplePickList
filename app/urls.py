from django.urls import path

from .views import app, auth, auth_callback, uninstalled

app_name = 'app'
urlpatterns = [
    path('', app, name='app'),
    path('auth/', auth, name='auth'),
    path('authcallback/', auth_callback, name='authcallback'),
    path('uninstalled/', uninstalled, name='uninstalled')
]
