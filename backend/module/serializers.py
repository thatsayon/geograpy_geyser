from rest_framework import serializers
from .models import (
    Module,
    Questions,
    CustomTime,
    QuestionQuantity
)

class ModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Module
        fields = (
            'id',
            'module_name'
        )

class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Questions
        fields = (
            'id',
            'module',
            'question_text',
            'option1',
            'option2',
            'option3',
            'option4',
            'order'
        )

class CustomTimeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomTime
        fields = (
            'id',
            'duration'
        )

class QuestionQuantitySerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionQuantity
        fields = (
            'id',
            'quantity'
        )
