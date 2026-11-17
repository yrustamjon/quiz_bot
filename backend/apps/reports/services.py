import io
from collections import defaultdict
from decimal import Decimal

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

from apps.attempts.scoring import percent_display
from apps.attempts.services import released


def ranking(attempts, student_visibility=False):
    best = {}
    for a in (
        attempts.exclude(status="in_progress")
        .select_related("student", "quiz")
        .order_by("-percentage", "elapsed_seconds", "finished_at", "id")
    ):
        if student_visibility and (not a.quiz.show_ranking or not released(a.quiz)):
            continue
        key = (a.student_id, a.quiz_id)
        if key not in best:
            best[key] = a
    groups = defaultdict(list)
    for a in best.values():
        groups[a.student_id].append(a)
    result = []
    for sid, items in groups.items():
        result.append(
            {
                "student_id": sid,
                "name": items[0].student.full_name,
                "percentage": sum(a.percentage for a in items) / len(items),
                "quizzes": len(items),
                "elapsed_seconds": sum(a.elapsed_seconds for a in items),
            }
        )
    result.sort(key=lambda x: (-x["percentage"], x["elapsed_seconds"], x["student_id"]))
    return [{"rank": i + 1, **x} for i, x in enumerate(result)]


def safe_cell(value):
    if isinstance(value, str) and value.lstrip().startswith(
        ("=", "+", "-", "@", "\t", "\r")
    ):
        return "'" + value
    return value


def export_results(attempts):
    w = Workbook()
    s = w.active
    s.title = "Natijalar"
    s.append(
        [
            "O‘quvchi",
            "Test",
            "O‘qituvchi",
            "Urinish",
            "Boshlangan",
            "Yakunlangan",
            "Vaqt (s)",
            "To‘g‘ri",
            "Noto‘g‘ri",
            "Javobsiz",
            "Ball",
            "Maksimum",
            "Foiz",
            "Holat",
        ]
    )
    for a in attempts.select_related("student", "quiz__owner").order_by("-started_at"):
        s.append(
            [
                safe_cell(a.student.full_name),
                safe_cell(a.quiz.title),
                safe_cell(a.quiz.owner.full_name or a.quiz.owner.username),
                a.number,
                a.started_at.isoformat(),
                a.finished_at.isoformat() if a.finished_at else "",
                a.elapsed_seconds,
                a.correct,
                a.incorrect,
                a.unanswered,
                float(a.earned),
                float(a.maximum),
                float(percent_display(a.percentage)),
                {
                    "in_progress": "Jarayonda",
                    "completed": "Yakunlangan",
                    "timed_out": "Vaqt tugagan",
                }.get(a.status, a.status),
            ]
        )
    for c in s[1]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="2563EB")
    for row in s.iter_rows(min_row=2):
        row[10].number_format = "0.00"
        row[11].number_format = "0.00"
        row[12].number_format = '0.00"%"'
    s.freeze_panes = "A2"
    s.auto_filter.ref = s.dimensions
    for col in s.columns:
        s.column_dimensions[col[0].column_letter].width = 24
    out = io.BytesIO()
    w.save(out)
    return out.getvalue()


def filter_results(qs, params):
    from datetime import datetime, time, timedelta

    from django.utils import timezone
    from rest_framework import serializers
    from rest_framework.exceptions import ValidationError

    for field in ["quiz", "student", "status"]:
        value = params.get(field)
        if value:
            if field != "status" and not str(value).isdigit():
                raise ValidationError("Filtr noto‘g‘ri.")
            qs = qs.filter(**{field: value})
    if params.get("teacher"):
        teacher = str(params["teacher"])
        if not teacher.isdigit():
            raise ValidationError("O‘qituvchi filtri noto‘g‘ri.")
        qs = qs.filter(quiz__owner_id=teacher)
    dates = {}
    for field in ["start", "end"]:
        if params.get(field):
            dates[field] = serializers.DateField().run_validation(params[field])
    if dates.get("start") and dates.get("end") and dates["start"] > dates["end"]:
        raise ValidationError("Sana oralig‘i noto‘g‘ri.")
    if dates.get("start"):
        qs = qs.filter(
            started_at__gte=timezone.make_aware(
                datetime.combine(dates["start"], time.min)
            )
        )
    if dates.get("end"):
        qs = qs.filter(
            started_at__lt=timezone.make_aware(
                datetime.combine(dates["end"] + timedelta(days=1), time.min)
            )
        )
    for key, lookup in [
        ("min_score", "percentage__gte"),
        ("max_score", "percentage__lte"),
    ]:
        if params.get(key):
            qs = qs.filter(
                **{
                    lookup: serializers.DecimalField(
                        max_digits=9, decimal_places=6, min_value=0, max_value=100
                    ).run_validation(params[key])
                }
            )
    return qs.filter(student__full_name__icontains=params.get("search", ""))


def report_data(attempts, kind):
    from django.db.models import Avg, Count, Max, Q

    final = attempts.exclude(status="in_progress")
    if kind == "leaderboard":
        return ranking(final)
    if kind == "students":
        return list(
            final.values("student_id", "student__full_name")
            .annotate(
                attempts=Count("id"),
                percentage=Avg("percentage", filter=~Q(status="in_progress")),
                last_activity=Max("finished_at"),
            )
            .order_by("student__full_name")
        )
    if kind == "teachers":
        return list(
            attempts.values(
                "quiz__owner_id", "quiz__owner__full_name", "quiz__owner__username"
            )
            .annotate(
                quizzes=Count("quiz", distinct=True),
                attempts=Count("id"),
                students=Count("student", distinct=True),
                percentage=Avg("percentage", filter=~Q(status="in_progress")),
            )
            .order_by("quiz__owner__username")
        )
    return []


def export_report(attempts, kind="results"):
    if kind == "results":
        return export_results(attempts)
    rows = report_data(attempts, kind)
    columns = {
        "leaderboard": [
            ("rank", "O‘rin"),
            ("name", "O‘quvchi"),
            ("percentage", "Foiz"),
            ("quizzes", "Testlar"),
            ("elapsed_seconds", "Vaqt (s)"),
        ],
        "students": [
            ("student__full_name", "O‘quvchi"),
            ("attempts", "Urinishlar"),
            ("percentage", "O‘rtacha foiz"),
            ("last_activity", "So‘nggi faollik"),
        ],
        "teachers": [
            ("quiz__owner__full_name", "O‘qituvchi"),
            ("quiz__owner__username", "Login"),
            ("quizzes", "Testlar"),
            ("attempts", "Urinishlar"),
            ("students", "O‘quvchilar"),
            ("percentage", "O‘rtacha foiz"),
        ],
    }[kind]
    w = Workbook()
    sheet = w.active
    sheet.title = "Hisobot"
    sheet.append([label for _, label in columns])
    for row in rows:
        values = []
        for key, _ in columns:
            value = row.get(key)
            if hasattr(value, "isoformat"):
                value = value.isoformat()
            if key == "percentage" and value is not None:
                value = float(percent_display(value))
            if isinstance(value, Decimal):
                value = float(value)
            values.append(safe_cell(value))
        sheet.append(values)
    for c in sheet[1]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="2563EB")
    for col in sheet.columns:
        sheet.column_dimensions[col[0].column_letter].width = 25
    sheet.freeze_panes = "A2"
    out = io.BytesIO()
    w.save(out)
    return out.getvalue()
