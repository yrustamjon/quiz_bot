import io
from collections import defaultdict

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

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
                float(a.percentage),
                a.status,
            ]
        )
    for c in s[1]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="2563EB")
    s.freeze_panes = "A2"
    s.auto_filter.ref = s.dimensions
    for col in s.columns:
        s.column_dimensions[col[0].column_letter].width = 24
    out = io.BytesIO()
    w.save(out)
    return out.getvalue()
