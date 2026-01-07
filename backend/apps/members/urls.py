from django.urls import path
from . import views

app_name = 'members'

urlpatterns = [
    path('', views.get_members, name='get_members'),
]
