from django.urls import path
from .views import file_upload

urlpatterns = [
    path('upload/', file_upload, name='file_upload'),
]