from django.core.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_handler


def exception_handler(exc, context):
    if isinstance(exc, ValidationError):
        return Response({"detail": exc.messages}, status=400)
    return drf_handler(exc, context)
