"""Bound request bodies and multipart streams before temporary-file exhaustion."""

from django.core.files.uploadhandler import FileUploadHandler, StopUpload
from django.http import JsonResponse

MAX_REQUEST = 12 * 1024 * 1024


class UploadLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            length = int(request.META.get("CONTENT_LENGTH") or 0)
        except ValueError:
            return JsonResponse({"detail": "So‘rov hajmi noto‘g‘ri."}, status=400)
        if length < 0 or length > MAX_REQUEST:
            return JsonResponse({"detail": "So‘rov 12 MB dan oshmasin."}, status=413)
        return self.get_response(request)


class BoundedUploadHandler(FileUploadHandler):
    def __init__(self, request=None):
        super().__init__(request)
        self.received = 0

    def receive_data_chunk(self, raw_data, start):
        self.received += len(raw_data)
        if self.received > MAX_REQUEST:
            raise StopUpload(connection_reset=True)
        return raw_data

    def file_complete(self, file_size):
        return None


class PrivateAPIMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.path.startswith("/api/"):
            from django.utils.cache import patch_vary_headers

            response["Cache-Control"] = "private, no-store"
            patch_vary_headers(response, ["Cookie"])
        return response
