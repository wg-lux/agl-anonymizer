import os
import uuid
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import FileUploadSerializer
from agl_anonymizer_pipeline.main import main
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from endoreg_db.models.annotation import AnonymizedImageLabel, AnonymousImageAnnotation, DroppedName
from rest_framework.permissions import IsAuthenticated  # Optional, for secure API access

class Result:
    def __init__(self, **entries):
        self.__dict__.update(entries)

class ProcessFileView(APIView):
    #permission_classes = [IsAuthenticated]  # Optional, require authentication

    def post(self, request, *args, **kwargs):
        serializer = FileUploadSerializer(data=request.data)

        if serializer.is_valid():
            device = request.POST.get('device', 'olympus_cv_1500')
            file = serializer.validated_data['file']
            validation = request.POST.get('validation', 'false').lower() in ['true', '1']
            
            # Save the uploaded file to a temporary location
            temp_file_path = os.path.join(settings.MEDIA_ROOT, file.name)
            with open(temp_file_path, 'wb') as temp_file:
                for chunk in file.chunks():
                    temp_file.write(chunk)

            try:
                # Get the absolute path to the model file inside the Django application
                east_model_path = os.path.join(settings.BASE_DIR, 'agl_anonymizer', 'models', 'frozen_east_text_detection.pb')

                if not os.path.exists(east_model_path):
                    raise FileNotFoundError(f"Model file not found: {east_model_path}")
                
                # Call the main function from main.py, passing the device parameter
                if validation:
                    output_path, stats, original_img_path = main(temp_file_path, east_path=east_model_path, device=device, validation=True)
                    stats = Result(**stats)

                    # Save the annotation to the database
                    label, created = AnonymizedImageLabel.objects.get_or_create(name="Default Label")
                    annotation = AnonymousImageAnnotation.objects.create(
                        label=label,
                        image_name=os.path.basename(temp_file_path),
                        original_image_url=original_img_path,
                        polyp_count=len(stats.gender_pars),  # Example: counting genders as a proxy for polyp count
                        comments="Automatically generated annotation",
                        gender="mixed",  # Example: you might need to determine this more accurately
                        name_image_url=output_path,
                        processed=True
                    )

                    # Save dropped names to the database
                    for gender_par in stats.gender_pars:
                        DroppedName.objects.create(
                            annotation=annotation,
                            name=gender_par['name'],
                            gender=gender_par['gender'],
                            x=gender_par['x'],
                            y=gender_par['y'],
                            name_image_url=gender_par['image_url']
                        )

                    # Create a response with the processed files and additional values
                    response_data = {
                        'processed_files': [output_path],
                        'additional_values': 'Processing completed successfully',
                        'image_paths': [stats.modified_image_paths],
                        'gender_pars': [stats.gender_pars],
                        'original_image_path': [original_img_path]
                    }
                else:
                    output_path = main(temp_file_path, east_path=east_model_path, device=device, validation=False)
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

class HandleAnnotationView(APIView):
    def post(self, request, *args, **kwargs):
        # Extract data from the request
        annotation_data = request.data.get('annotation')

        if not annotation_data:
            return Response({"error": "No annotation data provided"}, status=status.HTTP_400_BAD_REQUEST)

        # Process the annotation data, e.g., save to database
        label, created = AnonymizedImageLabel.objects.get_or_create(name=annotation_data['label_name'])
        annotation = AnonymousImageAnnotation.objects.create(
            label=label,
            image_name=annotation_data['image_name'],
            original_image_url=annotation_data['original_image_url'],
            polyp_count=annotation_data.get('polyp_count', 0),
            comments=annotation_data.get('comments', ''),
            gender=annotation_data.get('gender', 'unknown'),
            name_image_url=annotation_data.get('name_image_url', ''),
            processed=True
        )

        return Response({"message": "Annotation saved successfully"}, status=status.HTTP_200_OK)


class SaveDataView(APIView):
    def post(self, request, *args, **kwargs):
        annotation_id = request.data.get('annotation_id')
        
        try:
            annotation = AnonymousImageAnnotation.objects.get(id=annotation_id)
            annotation.processed = True
            annotation.save()

            return Response({"message": "Data saved successfully"}, status=status.HTTP_200_OK)
        except AnonymousImageAnnotation.DoesNotExist:
            return Response({"error": "Annotation not found"}, status=status.HTTP_404_NOT_FOUND)
