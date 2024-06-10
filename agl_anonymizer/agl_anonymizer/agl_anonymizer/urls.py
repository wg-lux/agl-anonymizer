from django.urls import path
from .views import ProcessFileView

urlpatterns = [
    path('process/', ProcessFileView.as_view(), name='process-file'),
]
