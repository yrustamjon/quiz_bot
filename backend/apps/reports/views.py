from datetime import timedelta
from django.utils import timezone
from django.db.models import Count,Avg
from django.db.models.functions import TruncDate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from apps.accounts.permissions import owned
from apps.quizzes.models import Quiz
from apps.attempts.models import Attempt

class DashboardView(APIView):
    def get(self,request):
        try:days=int(request.query_params.get('days','30'))
        except ValueError:raise ValidationError('Davr noto‘g‘ri.')
        if days not in [1,7,30,90]:raise ValidationError('Davr noto‘g‘ri.')
        quizzes=owned(Quiz.objects.all(),request.user)
        attempts=Attempt.objects.filter(quiz__in=quizzes,started_at__gte=timezone.now()-timedelta(days=days))
        final=attempts.exclude(status='in_progress')
        return Response({'quizzes':quizzes.count(),'published':quizzes.filter(status='published').count(),'participants':attempts.values('student').distinct().count(),'completed':final.count(),'average':final.aggregate(value=Avg('percentage'))['value'] or 0,'activity':list(attempts.annotate(date=TruncDate('started_at')).values('date').annotate(attempts=Count('id')).order_by('date')),'recent_quizzes':list(quizzes.order_by('-created_at').values('id','title','subject','status')[:5])})
