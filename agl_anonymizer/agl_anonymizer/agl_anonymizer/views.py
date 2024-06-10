import os
import uuid
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import FileUploadSerializer
from agl_anonymizer_pipeline.main import main  # Import the main function

class ProcessFileView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = FileUploadSerializer(data=request.data)
        if serializer.is_valid():
            file = serializer.validated_data['file']
            # Save the uploaded file to a temporary location
            temp_file_path = os.path.join(settings.MEDIA_ROOT, file.name)
            with open(temp_file_path, 'wb') as temp_file:
                for chunk in file.chunks():
                    temp_file.write(chunk)

            try:
                # Get the absolute path to the model file inside the Django application
                east_model_path = os.path.join(settings.BASE_DIR, 'agl_anonymizer', 'models', 'frozen_east_text_detection.pb')

                # Verify the file exists
                if not os.path.exists(east_model_path):
                    raise FileNotFoundError(f"Model file not found: {east_model_path}")

                # Call the main function from main.py
                output_path = main(temp_file_path, east_model_path)

                # Create a response with the processed files and additional values
                response_data = {
                    'processed_files': [output_path],
                    'additional_values': 'Processing completed successfully'
                }
                return Response(response_data, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            finally:
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
