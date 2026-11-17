import math
import posixpath

from .images import normalize_image

"""Bounded template v1 importer. No archive member is extracted to disk.

openpyxl 3.1's private image collection is used only behind this adapter,
with explicit anchor checks and regression tests (the library has no public
image-reading API). Unsupported anchors are errors, never silently dropped.
"""

import base64
import io
import stat
import zipfile
from decimal import Decimal, InvalidOperation
from pathlib import PurePosixPath
from xml.etree.ElementTree import ParseError, fromstring

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils.exceptions import InvalidFileException
from openpyxl.worksheet.datavalidation import DataValidation
from rest_framework.exceptions import ValidationError

HEADERS = [
    "Question",
    "Option A",
    "Option B",
    "Option C",
    "Option D",
    "Correct Answer",
    "Points",
    "Image File Name",
]
MAX_UPLOAD = 10 * 1024 * 1024
MAX_EXPANDED = 40 * 1024 * 1024


def template():
    w = Workbook()
    s = w.active
    s.title = "Questions"
    s.append(HEADERS)
    s.append(["2 + 2 = ?", "3", "4", "5", "6", "B", 1, ""])
    for cell in s[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="2563EB")
    for col in "ABCDEFGH":
        s.column_dimensions[col].width = 24
    s.freeze_panes = "A2"
    v = DataValidation(type="list", formula1='"A,B,C,D"')
    s.add_data_validation(v)
    v.add("F2:F501")
    instructions = w.create_sheet("Instructions")
    instructions.append(["QUIZ_BOT_TEMPLATE_V1"])
    instructions.append(["One question per row. A–D; points > 0; at most 500 rows."])
    instructions.append(
        [
            "ZIP: one XLSX plus PNG/JPEG/WebP files; relative image paths; no nested archives."
        ]
    )
    instructions.append(
        ["Embedded images: one image anchored in column H on its exact question row."]
    )
    out = io.BytesIO()
    w.save(out)
    return out.getvalue()


def archive(data, outer=False):
    try:
        z = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile:
        raise ValidationError("ZIP/XLSX fayli noto‘g‘ri.")
    infos = z.infolist()
    if len(infos) > 1500 or sum(x.file_size for x in infos) > MAX_EXPANDED:
        raise ValidationError("Arxiv hajmi yoki fayllar soni me’yordan oshgan.")
    names = set()
    result = {}
    for x in infos:
        name = x.filename
        path = PurePosixPath(name)
        if (
            name in names
            or name.startswith("/")
            or "\\" in name
            or ":" in name
            or ".." in path.parts
            or str(path) != name.rstrip("/")
            or stat.S_ISLNK(x.external_attr >> 16)
        ):
            raise ValidationError("Arxivda xavfli yoki takrorlangan yo‘l bor.")
        names.add(name)
        if x.flag_bits & 1:
            raise ValidationError("Shifrlangan arxiv qabul qilinmaydi.")
        if x.is_dir():
            continue
        if x.file_size > MAX_UPLOAD:
            raise ValidationError("Arxivdagi fayl juda katta.")
        if outer and path.suffix.lower() not in [
            ".xlsx",
            ".png",
            ".jpg",
            ".jpeg",
            ".webp",
        ]:
            raise ValidationError("Arxivda ruxsat etilmagan fayl bor.")
        try:
            result[name] = z.read(x)
        except (RuntimeError, zipfile.BadZipFile):
            raise ValidationError("Arxivni o‘qib bo‘lmadi.")
    return result


def image_bytes(data):
    return base64.b64encode(normalize_image(data)).decode()


def unsupported_image_rows(parts, unsupported):
    rows = []
    for part, payload in parts.items():
        if not part.startswith("xl/drawings/") or not part.endswith(".xml"):
            continue
        rel_path = str(
            PurePosixPath(part).parent / "_rels" / (PurePosixPath(part).name + ".rels")
        )
        try:
            rels = {
                rel.attrib.get("Id"): rel.attrib.get("Target", "")
                for rel in fromstring(parts.get(rel_path, b"<Relationships/>"))
            }
            for anchor in fromstring(payload):
                cell = anchor.find("./{*}from/{*}row")
                try:
                    row = int(cell.text) + 1 if cell is not None else 0
                except (ValueError, TypeError):
                    row = 0
                for blip in anchor.findall(".//{*}blip"):
                    rid = next(
                        (
                            value
                            for key, value in blip.attrib.items()
                            if key.endswith("}embed")
                        ),
                        None,
                    )
                    target = rels.get(rid, "")
                    path = (
                        target.lstrip("/")
                        if target.startswith("/")
                        else posixpath.normpath(
                            posixpath.join(str(PurePosixPath(part).parent), target)
                        )
                    )
                    if path in unsupported:
                        rows.append(
                            {
                                "row": row,
                                "message": "Bu qatordagi rasm PNG, JPEG yoki WebP formatida bo‘lsin.",
                            }
                        )
        except ParseError:
            raise ValidationError("Rasm XML tuzilishi noto‘g‘ri.")
    return rows or [
        {
            "row": 0,
            "message": "Excel ichida qo‘llab-quvvatlanmaydigan rasm formati bor.",
        }
    ]


def parse_upload(data, name):
    if len(data) > MAX_UPLOAD:
        raise ValidationError("Fayl 10 MB dan oshmasin.")
    suffix = PurePosixPath(name).suffix.lower()
    images = {}
    if suffix == ".zip":
        files = archive(data, outer=True)
        books = [n for n in files if n.lower().endswith(".xlsx")]
        if len(books) != 1:
            raise ValidationError("ZIP ichida aynan bitta XLSX bo‘lsin.")
        images = {n: b for n, b in files.items() if n != books[0]}
        data = files[books[0]]
    elif suffix != ".xlsx":
        raise ValidationError("Faqat XLSX yoki ZIP qabul qilinadi.")
    parts = archive(data)
    if any(
        b"<!DOCTYPE" in v.replace(b"\x00", b"")
        or b"<!ENTITY" in v.replace(b"\x00", b"")
        for n, v in parts.items()
        if n.endswith((".xml", ".rels"))
    ):
        raise ValidationError("Xavfli XML.")
    if any(
        n.endswith("vbaProject.bin") or n.startswith("xl/embeddings/") for n in parts
    ):
        raise ValidationError("Makros va tashqi obyektlar qo‘llab-quvvatlanmaydi.")
    if any(n.startswith("xl/externalLinks/") for n in parts):
        raise ValidationError("Tashqi havolalar qo‘llab-quvvatlanmaydi.")
    source_images = 0
    unsupported = set()
    for part, payload in parts.items():
        if part.startswith("xl/media/") and PurePosixPath(part).suffix.lower() not in [
            ".png",
            ".jpg",
            ".jpeg",
            ".webp",
        ]:
            unsupported.add(part)
        if part.endswith(".rels") and b'TargetMode="External"' in payload:
            raise ValidationError("Excel ichidagi tashqi havolalar qabul qilinmaydi.")
        if part.startswith("xl/drawings/") and part.endswith(".xml"):
            try:
                source_images += sum(
                    node.tag.rsplit("}", 1)[-1] == "pic"
                    for node in fromstring(payload).iter()
                )
            except ParseError:
                raise ValidationError("Rasm XML tuzilishi noto‘g‘ri.")
    if unsupported:
        return [], unsupported_image_rows(parts, unsupported)
    try:
        w = load_workbook(io.BytesIO(data), data_only=False, keep_links=False)
    except (
        InvalidFileException,
        zipfile.BadZipFile,
        KeyError,
        OSError,
        ValueError,
        TypeError,
        ParseError,
        IndexError,
        AttributeError,
    ):
        raise ValidationError("XLSX faylini o‘qib bo‘lmadi.")
    if (
        "Questions" not in w
        or "Instructions" not in w
        or w["Instructions"]["A1"].value != "QUIZ_BOT_TEMPLATE_V1"
    ):
        raise ValidationError(
            "Shablon versiyasi mos emas. Yangi shablonni yuklab oling."
        )
    sheet = w["Questions"]
    if sheet.max_row > 501 or sheet.max_column > 8:
        raise ValidationError("Shablon chegarasi: 500 savol, 8 ustun.")
    if [c.value for c in sheet[1]] != HEADERS:
        raise ValidationError("Shablon ustunlari noto‘g‘ri.")
    if source_images != len(sheet._images):
        raise ValidationError(
            "Ba’zi rasmlar shablonning Questions varag‘iga to‘g‘ri biriktirilmagan."
        )
    embedded = {}
    errors = []
    for image in sheet._images:
        anchor = image.anchor
        if (
            not hasattr(anchor, "_from")
            or (
                hasattr(anchor, "to")
                and hasattr(anchor, "_from")
                and anchor.to.row != anchor._from.row
            )
            or anchor._from.col != 7
            or anchor._from.row < 1
            or anchor._from.row > 500
            or anchor._from.row + 1 in embedded
        ):
            errors.append(
                {
                    "row": getattr(getattr(anchor, "_from", None), "row", -1) + 1,
                    "message": "Rasm H ustunida aynan bitta savol qatoriga biriktirilsin.",
                }
            )
            continue
        try:
            embedded[anchor._from.row + 1] = image_bytes(image._data())
        except ValidationError as e:
            errors.append(
                {
                    "row": anchor._from.row + 1,
                    "message": " ".join(str(message) for message in e.detail)
                    if isinstance(e.detail, list)
                    else str(e.detail),
                }
            )
        except (OSError, ValueError, TypeError, AttributeError):
            errors.append(
                {
                    "row": anchor._from.row + 1,
                    "message": "Bu qatordagi rasmni o‘qib bo‘lmadi.",
                }
            )
    for image_row in embedded:
        value = sheet.cell(image_row, 1).value
        if not isinstance(value, str) or not value.strip():
            errors.append(
                {
                    "row": image_row,
                    "message": "Rasm biriktirilgan qatorda savol matni yo‘q.",
                }
            )
    rows = []
    normalized_size = 0
    image_cache = {}
    seen = set()
    for idx, cells in enumerate(sheet.iter_rows(min_row=2, max_col=8), 2):
        values = [c.value for c in cells]
        if all(x is None for x in values):
            continue
        try:
            if any(c.data_type == "e" for c in cells):
                raise ValidationError("Excel katagida hisoblash xatosi bor.")
            if any(c.data_type == "f" for c in cells):
                raise ValidationError("Formula qabul qilinmaydi.")
            text = values[0]
            opts = [
                str(v)
                if isinstance(v, (int, float))
                and not isinstance(v, bool)
                and (isinstance(v, int) or math.isfinite(v))
                else v
                for v in values[1:5]
            ]
            correct = str(values[5] or "").upper()
            if not isinstance(text, str) or not text.strip() or len(text) > 10000:
                raise ValidationError("Savol matni noto‘g‘ri.")
            if not all(
                isinstance(x, str) and x.strip() and len(x) <= 2000 for x in opts
            ):
                raise ValidationError("To‘rtta variantni kiriting.")
            if correct not in ["A", "B", "C", "D"]:
                raise ValidationError("To‘g‘ri javob A, B, C yoki D bo‘lsin.")
            try:
                points = Decimal(str(values[6]))
            except (InvalidOperation, TypeError):
                raise ValidationError("Ball noto‘g‘ri.")
            if (
                not points.is_finite()
                or points <= 0
                or points > 999999
                or points.as_tuple().exponent < -2
            ):
                raise ValidationError(
                    "Ball musbat, ko‘pi bilan ikki kasr xonali bo‘lsin."
                )
            signature = (text.strip(), *opts)
            if signature in seen:
                raise ValidationError("Takrorlangan savol.")
            seen.add(signature)
            image = embedded.get(idx)
            reference = values[7]
            if reference:
                if image:
                    raise ValidationError(
                        "Ikkita rasm usuli bir qatorda ishlatilmasin."
                    )
                if not isinstance(reference, str) or reference not in images:
                    raise ValidationError("Ko‘rsatilgan rasm topilmadi.")
                if reference not in image_cache:
                    image_cache[reference] = image_bytes(images[reference])
                image = image_cache[reference]
            normalized_size += len(image or "")
            if normalized_size > MAX_EXPANDED:
                raise ValidationError(
                    "Import rasmlarining jami hajmi me’yordan oshgan."
                )
            rows.append(
                {
                    "source_row": idx,
                    "text": text.strip(),
                    "options": opts,
                    "correct_option": ord(correct) - 65,
                    "points": str(points),
                    "image_base64": image,
                }
            )
        except ValidationError as e:
            errors.append(
                {
                    "row": idx,
                    "message": " ".join(str(message) for message in e.detail)
                    if isinstance(e.detail, list)
                    else str(e.detail),
                }
            )
    if not rows and not errors:
        errors.append({"row": 0, "message": "Savollar yo‘q."})
    return rows, errors
