from celery import shared_task
from django.utils import timezone

from apps.questions.models import ImportSession


@shared_task
def cleanup():
    from datetime import timedelta

    from .models import ReportExport

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

from apps.accounts.permissions import owned
from apps.attempts.models import Attempt

from .models import ReportExport
from .services import export_results


@shared_task(autoretry_for=(OSError,), retry_backoff=True, max_retries=3)
def generate_export(export_id):
    with transaction.atomic():
        job = (
            ReportExport.objects.select_for_update()
            .select_related("owner")
            .get(pk=export_id)
        )
        if job.status == "ready":
            return str(job.pk)
        if not job.owner.is_active or job.owner.must_change_password:
            job.status = "failed"
            job.error = "Hisobga kirish cheklangan."
            job.save()
            return
        qs = owned(Attempt.objects.all(), job.owner, "quiz__owner")
        for key, value in job.filters.items():
            if value and key in ["quiz", "student", "status"]:
                qs = qs.filter(**{key: value})
        if job.filters.get("search"):
            qs = qs.filter(student__full_name__icontains=job.filters["search"])
        job.file.save(
            str(job.pk) + ".xlsx", ContentFile(export_results(qs)), save=False
        )
        job.status = "ready"
        job.finished_at = timezone.now()
        job.save()
    return str(job.pk)
