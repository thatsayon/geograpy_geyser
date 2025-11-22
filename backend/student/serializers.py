# module/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Avg, Sum
from module.models import Questions, QuizAttend, Module

User = get_user_model()

class QuestionSerializer(serializers.ModelSerializer):
    options = serializers.SerializerMethodField()

    class Meta:
        model = Questions
        fields = ("id", "question_text", "options", "correct_answer")

    def get_options(self, obj):
        return {
            "option1": obj.option1,
            "option2": obj.option2,
            "option3": obj.option3,
            "option4": obj.option4
        }


class QuizAttendSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizAttend
        fields = "__all__"


class SubjectPerformanceSerializer(serializers.ModelSerializer):
    progress = serializers.SerializerMethodField()
    quiz_attempted = serializers.SerializerMethodField()
    average_score = serializers.SerializerMethodField()

    class Meta:
        model = Module
        fields = ('id', 'module_name', 'progress', 'quiz_attempted', 'average_score')

    def get_progress(self, obj):
        user = self.context.get('user')
        attend = QuizAttend.objects.filter(student=user, module=obj).first()
        if attend and attend.total_questions > 0:
            return round(attend.correct_answers / attend.total_questions * 100, 2)
        return 0.0

    def get_quiz_attempted(self, obj):
        user = self.context.get('user')
        return QuizAttend.objects.filter(student=user, module=obj).count()

    def get_average_score(self, obj):
        user = self.context.get('user')
        avg_score = QuizAttend.objects.filter(student=user, module=obj).aggregate(Avg('score'))['score__avg']
        return round(avg_score, 2) if avg_score else 0.0



class UserPerformanceSerializer(serializers.ModelSerializer):
    total_xp = serializers.SerializerMethodField()
    profile_pic = serializers.SerializerMethodField()
    subjects = serializers.SerializerMethodField()
    quiz_attempted = serializers.SerializerMethodField()
    average_score = serializers.SerializerMethodField()
    subject_covered = serializers.SerializerMethodField()  # NEW

    class Meta:
        model = User
        fields = (
            'full_name',
            'profile_pic',
            'total_xp',
            'quiz_attempted',
            'average_score',
            'subjects',
            'subject_covered',  # include new field
        )

    def get_total_xp(self, obj):
        return QuizAttend.objects.filter(student=obj).aggregate(total=Sum('xp_gained'))['total'] or 0

    def get_profile_pic(self, obj):
        if obj.profile_pic:
            return obj.profile_pic.url
        return None

    def get_subjects(self, obj):
        module_ids = QuizAttend.objects.filter(student=obj).values_list('module_id', flat=True).distinct()
        modules = Module.objects.filter(id__in=module_ids)
        serializer = SubjectPerformanceSerializer(modules, many=True, context={'user': obj})
        return serializer.data

    def get_quiz_attempted(self, obj):
        return QuizAttend.objects.filter(student=obj).count()

    def get_average_score(self, obj):
        avg_score = QuizAttend.objects.filter(student=obj).aggregate(Avg('score'))['score__avg']
        return round(avg_score, 2) if avg_score else 0.0

    # NEW FIELD: total unique subjects attempted
    def get_subject_covered(self, obj):
        return QuizAttend.objects.filter(student=obj).values('module').distinct().count()
