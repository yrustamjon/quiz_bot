from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from apps.accounts.permissions import owned
from apps.questions.models import Question, QuizQuestion
from apps.questions.serializers import QuestionSerializer
from .models import Quiz
from .serializers import QuizSerializer
from .services import transition,duplicate,regenerate_code

class QuizViewSet(viewsets.ModelViewSet):
    serializer_class=QuizSerializer
    def get_queryset(self):
        qs=owned(Quiz.objects.all(),self.request.user)
        for field in ['status','subject','access']:
            if self.request.query_params.get(field):qs=qs.filter(**{field:self.request.query_params[field]})
        return qs.filter(title__icontains=self.request.query_params.get('search','')).order_by('-created_at')
    def perform_create(self,serializer):serializer.save(owner=self.request.user)
    def perform_update(self,serializer):
        if serializer.instance.status!='draft':raise ValidationError('Faol testni o‘zgartirish uchun nusxa yarating.')
        serializer.save()
    def perform_destroy(self,obj):
        if obj.status!='draft' or obj.attempts.exists():raise ValidationError('Faqat qatnashuvchisiz qoralamani o‘chirish mumkin.')
        obj.delete()
    @action(detail=True,methods=['post'])
    def publish(self,request,pk=None):return Response(self.get_serializer(transition(self.get_object(),'published')).data)
    @action(detail=True,methods=['post'])
    def close(self,request,pk=None):return Response(self.get_serializer(transition(self.get_object(),'closed')).data)
    @action(detail=True,methods=['post'])
    def archive(self,request,pk=None):return Response(self.get_serializer(transition(self.get_object(),'archived')).data)
    @action(detail=True,methods=['post'])
    def duplicate(self,request,pk=None):return Response(self.get_serializer(duplicate(self.get_object(),request.user)).data,status=201)
    @action(detail=True,methods=['post'],url_path='regenerate-code')
    def code(self,request,pk=None):return Response({'code':regenerate_code(self.get_object())})
    @action(detail=True,methods=['post'],url_path='release-results')
    def release(self,request,pk=None):
        q=self.get_object();q.results_released=True;q.save(update_fields=['results_released']);return Response({'released':True})
    @action(detail=True,methods=['get','put'])
    def questions(self,request,pk=None):
        quiz=self.get_object()
        if request.method=='PUT':
            if quiz.status!='draft':raise ValidationError('Faqat qoralamani o‘zgartirish mumkin.')
            ids=request.data.get('question_ids',[])
            if not isinstance(ids,list) or len(ids)>500 or any(type(x)!=int for x in ids) or len(set(ids))!=len(ids):raise ValidationError('Savollar ro‘yxati noto‘g‘ri.')
            qs=Question.objects.filter(pk__in=ids,owner=quiz.owner)
            if qs.count()!=len(ids):raise ValidationError('Savollarga ruxsat yo‘q.')
            with transaction.atomic():
                quiz.question_links.all().delete()
                QuizQuestion.objects.bulk_create([QuizQuestion(quiz=quiz,question_id=q,position=i) for i,q in enumerate(ids)])
        return Response(QuestionSerializer([x.question for x in quiz.question_links.select_related('question')],many=True).data)
