from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import ProcessFileView, UploadedFileViewSet, AnonymizedFileViewSet

router = DefaultRouter()
router.register(r'uploads', UploadedFileViewSet)
router.register(r'anonymized', AnonymizedFileViewSet)
router.register(r'process', ProcessFileView.as_view(), name='process-file')    

urlpatterns = [
    path('', include(router.urls)),
]
