from django.http import FileResponse
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError,NotFound
from apps.accounts.permissions import owned
from .models import Question
from .serializers import QuestionSerializer

class QuestionViewSet(viewsets.ModelViewSet):
    serializer_class=QuestionSerializer
    def get_queryset(self):return owned(Question.objects.all(),self.request.user).filter(text__icontains=self.request.query_params.get('search','')).order_by('-id')
    def perform_create(self,s):s.save(owner=self.request.user)
    def perform_update(self,s):
        if s.instance.quizquestion_set.exclude(quiz__status='draft').exists():raise ValidationError('Faol testdagi savolni o‘zgartirish mumkin emas. Nusxa yarating.')
        s.save()
    def perform_destroy(self,obj):
        if obj.quizquestion_set.exists():raise ValidationError('Savol testga biriktirilgan.')
        obj.delete()
    @action(detail=True,methods=['get'])
    def image(self,request,pk=None):
        q=self.get_object()
        if not q.image:raise NotFound()
        try:return FileResponse(q.image.open('rb'),content_type='image/png')
        except OSError:raise NotFound()
