from django.http import JsonResponse, FileResponse, Http404
from django.views.decorators.csrf import csrf_exempt
import os
from django.conf import settings

from utils.image_pii_presidio import anonymize_path as anonymize_file_path
from django.utils.text import get_valid_filename
import uuid

# Folders for upload and output
UPLOAD_FOLDER = os.path.join(settings.MEDIA_ROOT, 'uploads')
OUTPUT_FOLDER = os.path.join(settings.MEDIA_ROOT, 'output')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


@csrf_exempt
def index(request):
    """
    Handles single or multiple file upload and anonymization.
    Accepts:
      - multiple files with input name="files" (recommended), OR
      - multiple files with input name="file" (common), OR
      - single file with name="file" (backwards-compatible)
    Returns JSON with list of results for every uploaded file.
    """
    if request.method != 'POST':
        return JsonResponse({"status": "error", "message": "Only POST allowed"}, status=405)
        
    # Collect uploaded files robustly:
    files = []
    # Prefer explicit 'files' multi-field
    files_list = request.FILES.getlist('files')
    if files_list:
        files = files_list
    else:
        # Accept multiple 'file' entries or a single 'file'
        files_list = request.FILES.getlist('file')
        if files_list:
            files = files_list
        elif request.FILES:
            # fallback: collect all uploaded files regardless of field name
            files = list(request.FILES.values())

    if not files:
        return JsonResponse({"status": "error", "message": "No file(s) uploaded"}, status=400)

    results = []
    for uploaded_file in files:
        original_filename = uploaded_file.name
        # sanitize filename and add uuid to avoid collisions
        safe_name = get_valid_filename(original_filename)
        unique_prefix = uuid.uuid4().hex[:8]
        saved_input_name = f"{unique_prefix}_{safe_name}"
        input_path = os.path.join(UPLOAD_FOLDER, saved_input_name)

        # Prepare output filename
        output_filename = f"anonymized_{saved_input_name}"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)

        # Save uploaded file
        try:
            with open(input_path, 'wb+') as dest:
                for chunk in uploaded_file.chunks():
                    dest.write(chunk)
        except Exception as e:
            results.append({
                "original_filename": original_filename,
                "anonymized_filename": None,
                "download_url": None,
                "status": "error",
                "message": f"Failed to save file: {str(e)}"
            })
            continue

        # Call your anonymization (works for images & pdf through anonymize_path)
        try:
            anonymize_file_path(input_path, output_path)

            # remove the original uploaded file to save disk (optional but recommended)
            try:
                os.remove(input_path)
            except Exception:
                # don't fail the whole flow if removal fails
                pass

            # build absolute URL so frontend can download directly
            download_path = f"/download/{output_filename}"
            try:
                download_url = request.build_absolute_uri(download_path)
            except Exception:
                # fallback to relative URL if build_absolute_uri fails
                download_url = download_path

            results.append({
                "original_filename": original_filename,
                "anonymized_filename": output_filename,
                "download_url": download_url,
                "status": "success",
                "message": "Anonymized successfully"
            })
        except Exception as e:
            # Keep original input file for debugging if anonymization fails
            results.append({
                "original_filename": original_filename,
                "anonymized_filename": None,
                "download_url": None,
                "status": "error",
                "message": f"Anonymization failed: {str(e)}"
            })
            # continue processing other files

    return JsonResponse({"status": "done", "results": results})


def download(request, filename):
    """
    Download anonymized file
    """
    file_path = os.path.join(OUTPUT_FOLDER, filename)
    if not os.path.exists(file_path):
        raise Http404("File not found")

    return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=filename)
