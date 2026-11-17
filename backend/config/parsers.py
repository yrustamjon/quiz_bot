"""All JSON mutation contracts accept an object at the top level."""

from rest_framework.exceptions import ParseError
from rest_framework.parsers import JSONParser


class ObjectJSONParser(JSONParser):
    def parse(self, stream, media_type=None, parser_context=None):
        data = super().parse(
            stream, media_type=media_type, parser_context=parser_context
        )
        if not isinstance(data, dict):
            raise ParseError("JSON so‘rovi maydonlardan iborat obyekt bo‘lsin.")
        return data
