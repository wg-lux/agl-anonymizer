from django.urls import path
from .views import ProcessFileView, HandleAnnotationView, SaveDataView
from rest_framework.authtoken.views import obtain_auth_token


urlpatterns = [
    path('process-file/', ProcessFileView.as_view(), name='process_file'),
    path('handle-annotation/', HandleAnnotationView.as_view(), name='handle_annotation'),
    path('save-data/', SaveDataView.as_view(), name='save_data'),
    path('api/token/', obtain_auth_token, name='api_token_auth'),
]

