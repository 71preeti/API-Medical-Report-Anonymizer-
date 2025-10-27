from django.http import JsonResponse, FileResponse, Http404
from django.views.decorators.csrf import csrf_exempt
import os
from django.conf import settings
from utils.image_pii_presidio import anonymize_image  # Your utility function

# Folders for upload and output
UPLOAD_FOLDER = os.path.join(settings.MEDIA_ROOT, 'uploads')
OUTPUT_FOLDER = os.path.join(settings.MEDIA_ROOT, 'output')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@csrf_exempt
def index(request):
    """
    Handles file upload and anonymization.
    Returns JSON with filename and download URL.
    """
    if request.method == 'POST' and request.FILES.get('file'):
        file = request.FILES['file']
        filename = file.name

        input_path = os.path.join(UPLOAD_FOLDER, filename)
        output_filename = 'anonymized_' + filename
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)

        # Save uploaded file
        with open(input_path, 'wb+') as dest:
            for chunk in file.chunks():
                dest.write(chunk)

        # Call your anonymization
        anonymize_image(input_path, output_path)

        # Return JSON response
        download_url = f"/download/{output_filename}"
        return JsonResponse({
            "status": "success",
            "original_filename": filename,
            "anonymized_filename": output_filename,
            "download_url": download_url
        })

    return JsonResponse({"status": "error", "message": "No file uploaded"}, status=400)


def download(request, filename):
    """
    Download anonymized file
    """
    file_path = os.path.join(OUTPUT_FOLDER, filename)
    if not os.path.exists(file_path):
        raise Http404("File not found")

    return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=filename)
