
# Register your models here.
from django.contrib import admin
from .models import UploadedFile, AnonymizedFile

admin.site.register(UploadedFile)
admin.site.register(AnonymizedFile)
