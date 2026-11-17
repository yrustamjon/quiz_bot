import uuid
from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class Quiz(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='quizzes')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    subject = models.CharField(max_length=100)
    duration_minutes = models.PositiveIntegerField(default=30, validators=[MinValueValidator(1), MaxValueValidator(1440)])
    question_count = models.PositiveIntegerField(default=10, validators=[MinValueValidator(1), MaxValueValidator(500)])
    passing_score = models.DecimalField(max_digits=5, decimal_places=2, default=60, validators=[MinValueValidator(0),MaxValueValidator(100)])
    max_attempts = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1),MaxValueValidator(100)])
    shuffle_questions = models.BooleanField(default=False)
    shuffle_options = models.BooleanField(default=False)
    navigation = models.CharField(max_length=16, choices=[('sequential','Ketma-ket'),('free','Erkin')], default='sequential')
    access = models.CharField(max_length=8, choices=[('public','Ochiq'),('private','Yopiq')], default='public')
    status = models.CharField(max_length=12, choices=[(s,s) for s in ['draft','published','closed','archived']], default='draft', db_index=True)
    opens_at = models.DateTimeField(null=True,blank=True)
    closes_at = models.DateTimeField(null=True,blank=True)
    show_score = models.BooleanField(default=True)
    show_percentage = models.BooleanField(default=True)
    show_correct_count = models.BooleanField(default=True)
    show_incorrect_count = models.BooleanField(default=True)
    show_detailed_answers = models.BooleanField(default=False)
    show_ranking = models.BooleanField(default=True)
    result_release_mode = models.CharField(max_length=12, choices=[('instant','Darhol'),('after_close','Yopilgach'),('manual','Qo‘lda')], default='instant')
    results_released = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        constraints = [models.CheckConstraint(condition=models.Q(duration_minutes__gte=1),name='quiz_positive_duration'),models.CheckConstraint(condition=models.Q(question_count__gte=1),name='quiz_positive_count')]

class QuizAccessCode(models.Model):
    quiz = models.OneToOneField(Quiz,on_delete=models.CASCADE,related_name='access_code')
    code = models.CharField(max_length=32,unique=True)
    expires_at = models.DateTimeField(null=True,blank=True)
    active = models.BooleanField(default=True)
