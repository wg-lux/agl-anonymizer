from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import FileUploadSerializer
from .agl_anonymizer.agl_anonymizer import main   # Adjust the import based on your pipeline's entry point

class ProcessFileView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = FileUploadSerializer(data=request.data)
        if serializer.is_valid():
            file = serializer.validated_data['file']
            # Process the file using the agl_anonymizer pipeline
            processed_files, additional_values = process_pipeline(file)
            # Create a response with the processed files and additional values
            response_data = {
                'processed_files': processed_files,
                'additional_values': additional_values
            }
            return Response(response_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


import subprocess
import os
from django.conf import settings

def process_pipeline(file):
    # Save the uploaded file to a temporary location
    temp_file_path = os.path.join(settings.MEDIA_ROOT, file.name)
    with open(temp_file_path, 'wb') as temp_file:
        for chunk in file.chunks():
            temp_file.write(chunk)

    # Define the command line command
    command = [
        'python', 'agl-anonymizer/agl_anonymizer/main.py',  # Adjust this path to the location of main.py
        '--image', temp_file_path,
        '--east', 'agl-anonymizer/agl_anonymizer/frozen_east_text_detection.pb'  # Adjust this path to the location of the model file
    ]

    # Execute the command
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        # Process the result as needed
        processed_file_path = temp_file_path.replace(file.name, f"processed_{file.name}")
        additional_values = {'output': result.stdout}
    except subprocess.CalledProcessError as e:
        processed_file_path = None
        additional_values = {'error': str(e)}

    # Clean up temporary file if needed
    if os.path.exists(temp_file_path):
        os.remove(temp_file_path)

    return [processed_file_path], additional_values
