from rest_framework import serializers
from .models import UploadedFile, AnonymizedFile


class FileUploadSerializer(serializers.Serializer):
    file = serializers.FileField()


class UploadedFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadedFile
        fields = '__all__'

class AnonymizedFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnonymizedFile
        fields = '__all__'
