from celery import Task, shared_task
from django.utils import timezone

from apps.questions.models import ImportSession


@shared_task
def cleanup():
    from datetime import timedelta

    from apps.accounts.models import RateLimitBucket

    from .models import ReportExport

    RateLimitBucket.objects.filter(expires_at__lt=timezone.now()).delete()
    count = ImportSession.objects.filter(expires_at__lt=timezone.now()).delete()[0]
    for job in ReportExport.objects.filter(
        created_at__lt=timezone.now() - timedelta(days=7)
    ):
        if job.file:
            job.file.delete(save=False)
        job.delete()
        count += 1
    return count


from django.core.files.base import ContentFile
from django.db import transaction

from apps.accounts.permissions import is_admin, owned
from apps.attempts.models import Attempt

from .models import ReportExport
from .services import export_report, filter_results


class ExportTask(Task):
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        if args:
            ReportExport.objects.filter(pk=args[0]).update(
                status="failed", error="Hisobot tayyorlashda xatolik yuz berdi."
            )
        import logging

        logging.getLogger(__name__).error(
            "Report generation failed task=%s type=%s", task_id, type(exc).__name__
        )


@shared_task(
    base=ExportTask, autoretry_for=(OSError,), retry_backoff=True, max_retries=3
)
def generate_export(export_id):
    with transaction.atomic():
        job = (
            ReportExport.objects.select_for_update()
            .select_related("owner")
            .get(pk=export_id)
        )
        if job.status == "ready":
            return str(job.pk)
        if (
            not job.owner.is_active
            or job.owner.must_change_password
            or (
                job.filters.get("report_type") == "teachers" and not is_admin(job.owner)
            )
        ):
            job.status = "failed"
            job.error = "Hisobga kirish cheklangan."
            job.save()
            return
        qs = owned(Attempt.objects.all(), job.owner, "quiz__owner")
        qs = filter_results(qs, job.filters)
        job.file.save(
            str(job.pk) + ".xlsx",
            ContentFile(export_report(qs, job.filters.get("report_type", "results"))),
            save=False,
        )
        job.status = "ready"
        job.finished_at = timezone.now()
        job.save()
    return str(job.pk)
