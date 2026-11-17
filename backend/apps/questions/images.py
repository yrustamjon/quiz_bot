import io

from PIL import Image, UnidentifiedImageError
from rest_framework.exceptions import ValidationError

MAX_IMAGE = 5 * 1024 * 1024
MAX_PIXELS = 16000000


def normalize_image(data):
    if len(data) > MAX_IMAGE:
        raise ValidationError("Rasm 5 MB dan oshmasin.")
    try:
        image = Image.open(io.BytesIO(data))
        if (
            image.format not in ["PNG", "JPEG", "WEBP"]
            or image.width * image.height > MAX_PIXELS
        ):
            raise ValueError()
        image.verify()
        image = Image.open(io.BytesIO(data)).convert("RGB")
        output = io.BytesIO()
        image.save(output, format="PNG")
        if output.tell() > MAX_IMAGE:
            raise ValidationError("Qayta ishlangan rasm 5 MB dan oshgan.")
        return output.getvalue()
    except (ValueError, OSError, UnidentifiedImageError, Image.DecompressionBombError):
        raise ValidationError("Rasm formati yoki o‘lchami noto‘g‘ri.")
