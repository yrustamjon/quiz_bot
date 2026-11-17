"""Keep machine-readable fields/statuses and consistent Uzbek user messages."""

import logging
import re

from django.core.exceptions import ValidationError
from rest_framework.exceptions import NotAuthenticated, PermissionDenied, Throttled
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_handler

MESSAGES = {
    "This field is required.": "Majburiy maydonni to‘ldiring.",
    "This field may not be blank.": "Bu maydon bo‘sh bo‘lmasin.",
    "This field may not be null.": "Bu maydonni to‘ldiring.",
    "A valid integer is required.": "Butun son kiriting.",
    "A valid number is required.": "To‘g‘ri son kiriting.",
    "Enter a valid email address.": "Email manzilini to‘g‘ri kiriting.",
    "Authentication credentials were not provided.": "Hisobga kiring.",
    "You do not have permission to perform this action.": "Ushbu amal uchun ruxsat yo‘q.",
    "Not found.": "Ma’lumot topilmadi.",
    "Invalid page.": "Bunday sahifa mavjud emas.",
    "No file was submitted.": "Faylni tanlang.",
    "The submitted file is empty.": "Yuklangan fayl bo‘sh.",
    "Upload a valid image. The file you uploaded was either not an image or a corrupted image.": "To‘g‘ri PNG, JPEG yoki WebP rasm yuklang.",
    "This password is too common.": "Bu parol juda oddiy. Murakkabroq parol tanlang.",
    "This password is entirely numeric.": "Parol faqat raqamlardan iborat bo‘lmasin.",
}


def localize(value):
    if isinstance(value, dict):
        return {key: localize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [localize(item) for item in value]
    if not isinstance(value, str):
        return value
    text = str(value)
    if text in MESSAGES:
        return MESSAGES[text]
    patterns = [
        (
            r"Ensure this value is greater than or equal to (.+)\.",
            r"Qiymat kamida \1 bo‘lsin.",
        ),
        (
            r"Ensure this value is less than or equal to (.+)\.",
            r"Qiymat ko‘pi bilan \1 bo‘lsin.",
        ),
        (
            r"Ensure this field has no more than (\d+) characters\.",
            r"Matn \1 belgidan oshmasin.",
        ),
        (
            r"Ensure this field has at least (\d+) characters\.",
            r"Matn kamida \1 belgidan iborat bo‘lsin.",
        ),
    ]
    for pattern, replacement in patterns:
        if re.fullmatch(pattern, text):
            return re.sub(pattern, replacement, text)
    if text.startswith("This password is too short."):
        return "Parol kamida 8 belgidan iborat bo‘lsin."
    if "too similar to" in text and text.startswith("The password"):
        return "Parol shaxsiy ma’lumotlaringizga o‘xshamasin."
    if text.startswith("CSRF Failed:"):
        return (
            "Xavfsizlik tekshiruvi bajarilmadi. Sahifani yangilab qayta urinib ko‘ring."
        )
    if text.startswith("Date has wrong format."):
        return "Sanani YYYY-MM-DD ko‘rinishida kiriting."
    if text.startswith("JSON parse error"):
        return "So‘rov formati noto‘g‘ri."
    if "is not a valid choice" in text:
        return "Ro‘yxatdagi qiymatlardan birini tanlang."
    return text


def exception_handler(exc, context):
    if isinstance(exc, (PermissionDenied, NotAuthenticated)):
        logging.getLogger(__name__).warning(
            "Panel authorization denied view=%s", type(context.get("view")).__name__
        )
    if isinstance(exc, ValidationError):
        return Response({"detail": localize(exc.messages)}, status=400)
    response = drf_handler(exc, context)
    if response is not None:
        response.data = localize(response.data)
        if isinstance(exc, Throttled):
            response.data = {
                "detail": "Juda ko‘p urinish. Birozdan so‘ng qayta urinib ko‘ring."
            }
    return response


def csrf_failure(request, reason=""):
    from django.http import JsonResponse

    return JsonResponse(
        {
            "detail": "Xavfsizlik tekshiruvi bajarilmadi. Sahifani yangilab qayta urinib ko‘ring."
        },
        status=403,
    )
