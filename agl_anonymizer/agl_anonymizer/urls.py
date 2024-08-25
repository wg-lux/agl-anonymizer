from django.urls import path
from .views import ProcessFileView, handle_annotation

from .views import save_data

urlpatterns = [
    path('save-annotated-data/', save_data, name='save_data'),## TODO: Add to API Folder in Django Project
    path('process/', ProcessFileView.as_view(), name='process-file'),
    path('annotation/', handle_annotation, name='handle_annotation'),## TODO: Add to API Folder in Django Project
    #path('g-play-annotation/', name='g-play-annotation_annotation'),## TODO: Add to API Folder in Django Project
    #path('g-play', name='g-play'),## TODO: Add to API Folder in Django Project


]
