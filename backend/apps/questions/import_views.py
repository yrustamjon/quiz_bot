from django.http import HttpResponse
from rest_framework.response import Response
from rest_framework.views import APIView

from .import_services import confirm_import, preview_import
from .importer import template


class ImportView(APIView):
    def get(self, request, operation):
        if operation != "template":
            return Response(status=404)
        response = HttpResponse(
            template(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = (
            'attachment; filename="quiz-questions-v1.xlsx"'
        )
        return response

    def post(self, request, operation):
        if operation == "preview":
            return Response(
                preview_import(
                    request.user, request.data.get("quiz"), request.FILES.get("file")
                )
            )
        if operation == "confirm":
            return Response(confirm_import(request.user, request.data.get("id")))
        return Response(status=404)
