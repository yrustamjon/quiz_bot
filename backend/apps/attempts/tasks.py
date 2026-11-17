from celery import shared_task
from django.db import transaction
from django.utils import timezone
from .models import Attempt
from .services import reconcile_one

@shared_task(autoretry_for=(OSError,),retry_backoff=True,max_retries=3)
def reconcile():
    count=0
    for pk in Attempt.objects.filter(status='in_progress',deadline__lte=timezone.now()).values_list('pk',flat=True).iterator():
        with transaction.atomic():
            a=Attempt.objects.select_for_update().get(pk=pk);reconcile_one(a);count+=1
    return count
