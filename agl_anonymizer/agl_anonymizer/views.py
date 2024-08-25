import os
import uuid
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import FileUploadSerializer
from agl_anonymizer_pipeline.main import main  # Import the main function

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt  # Only if you're having issues with CSRF tokens in your JavaScript
def handle_annotation(request):
    if request.method == "POST":
        data = request.POST.get("annotation_data", "")
        # Handle the data here (e.g., save it to the database)
        response = {
            "status": "success",
            "message": "Annotation received",
        }
        return JsonResponse(response)
    return JsonResponse({"status": "failed", "message": "Invalid request method"})


class ProcessFileView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = FileUploadSerializer(data=request.data)
        print("aösldkaöslkd")

        if serializer.is_valid():
            # Get the device parameter from the request, default to 'olympus_cv_1500' if not provided
            device = request.POST.get('device', 'olympus_cv_1500')
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

                # Call the main function from main.py, passing the device parameter
                output_path = main(temp_file_path, east_path=east_model_path, device=device)

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


import json

@csrf_exempt  # Ensure CSRF is handled if not passed in the headers
def save_data(request):
    if request.method == "POST":
        data = json.loads(request.body)

        # Extract data from the POST request
        name = data.get('name')
        polyp_count = data.get('polypCount')
        comments = data.get('comments')

        # Save the data in the database or perform your logic
        # For example:
        # new_entry = YourModel(name=name, polyp_count=polyp_count, comments=comments)
        # new_entry.save()
        print(f"Data received: {name}, {polyp_count}, {comments}")

        return JsonResponse({"status": "success", "message": "Data saved successfully"})

    return JsonResponse({"status": "failed", "message": "Invalid request method"})
