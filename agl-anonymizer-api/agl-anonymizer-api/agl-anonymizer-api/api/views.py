# api/views.py
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import UploadedFile
from .serializers import UploadedFileSerializer
import os
import shutil

@api_view(['POST'])
def file_upload(request):
    if request.method == 'POST':
        serializer = UploadedFileSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            # Process the uploaded file with agl_anonymizer
            file_path = serializer.data['file']
            process_file(file_path)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def process_file(file_path):
    # Implement your file processing with agl_anonymizer here
    result_directory = os.path.join(os.path.dirname(file_path), 'results')
    os.makedirs(result_directory, exist_ok=True)
    # Example: move file to results directory after processing
    shutil.move(file_path, result_directory)
