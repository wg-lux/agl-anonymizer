# api/views.py

import os
import subprocess
import tempfile
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework import status

class ProcessFileView(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request, *args, **kwargs):
        file_obj = request.data['file']
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            for chunk in file_obj.chunks():
                temp_file.write(chunk)
            temp_file_path = temp_file.name

        # Define the command to run your pipeline
        command = [
            'python', '/path/to/agl_anonymizer/main.py',  # Update this path to your main.py
            '--image', temp_file_path,
            '--east', '/path/to/frozen_east_text_detection.pb'  # Update this path to your model file
        ]

        try:
            # Run the command
            result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            processed_file_path = result.stdout.decode().strip()

            # Read the processed file and prepare the response
            with open(processed_file_path, 'rb') as processed_file:
                response = {
                    'processed_file': processed_file.read(),
                    'additional_values': {'example_key': 'example_value'}
                }

            return Response(response, status=status.HTTP_200_OK)
        except subprocess.CalledProcessError as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            os.remove(temp_file_path)
