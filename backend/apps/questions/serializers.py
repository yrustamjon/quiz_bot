import io
from PIL import Image, UnidentifiedImageError
from django.core.files.base import ContentFile
from rest_framework import serializers
from .models import Question

class QuestionSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    class Meta:
        model = Question
        fields = ['id','owner','text','subject','options','correct_option','points','image','image_url','created_at']
        read_only_fields = ['owner','created_at']
        extra_kwargs = {'image':{'write_only':True,'required':False}}
    def get_image_url(self,obj): return f'/api/questions/{obj.pk}/image/' if obj.image else None
    def validate_options(self,value):
        if not isinstance(value,list) or len(value)!=4 or not all(isinstance(x,str) and x.strip() and len(x)<=2000 for x in value): raise serializers.ValidationError('To‘rtta javob variantini kiriting.')
        return value
    def validate_image(self,value):
        if not value:return value
        if value.size>5*1024*1024: raise serializers.ValidationError('Rasm 5 MB dan oshmasin.')
        try:
            im=Image.open(value)
            if im.format not in ['PNG','JPEG','WEBP'] or im.width*im.height>16000000: raise ValueError()
            im.verify(); value.seek(0); im=Image.open(value).convert('RGB'); out=io.BytesIO(); im.save(out,format='PNG')
            return ContentFile(out.getvalue(),name='image.png')
        except (UnidentifiedImageError,ValueError,OSError,Image.DecompressionBombError): raise serializers.ValidationError('Rasm formati noto‘g‘ri.')
