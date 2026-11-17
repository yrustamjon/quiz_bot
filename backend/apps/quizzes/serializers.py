from rest_framework import serializers
from .models import Quiz

class QuizSerializer(serializers.ModelSerializer):
    available_questions = serializers.IntegerField(source='question_links.count',read_only=True)
    class Meta:
        model = Quiz
        fields = '__all__'
        read_only_fields = ['owner','status','results_released','created_at','updated_at']
    def validate(self,data):
        opens=data.get('opens_at',getattr(self.instance,'opens_at',None)); closes=data.get('closes_at',getattr(self.instance,'closes_at',None))
        if opens and closes and opens>=closes:raise serializers.ValidationError('Yopilish vaqti boshlanishdan keyin bo‘lsin.')
        return data
