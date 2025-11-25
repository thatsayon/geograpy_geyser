from django.contrib.auth import get_user_model
from django.db.models import Count, Sum, Q, Value, IntegerField, Avg, FloatField
from django.db.models.functions import Coalesce

from rest_framework import serializers

from module.models import (
    CustomTime,
    Module,
    Questions,
    OptionModulesPair,
)

from .models import SynopticModule

User = get_user_model()

class ProfileInformationSerializer(serializers.ModelSerializer):
    profile_pic = serializers.ImageField(required=False)

    class Meta:
        model = User
        fields = (
            'id',
            'profile_pic',
            'email',
            'full_name'
        )
        read_only_fields = ('id',)

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True, min_length=6)

    def validate(self, attrs):
        user = self.context['request'].user
        old_password = attrs.get('old_password')
        new_password = attrs.get('new_password')

        if not old_password:
            raise serializers.ValidationError({"old_password": "This field is required."})
        if not new_password:
            raise serializers.ValidationError({"new_password": "This field is required."})
        if not user.check_password(old_password):
            raise serializers.ValidationError({"old_password": "Old password is incorrect"})
        if old_password == new_password:
            raise serializers.ValidationError({"new_password": "New password must be different from old password"})
        return attrs

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class CustomTimeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomTime
        fields = (
            'id',
            'duration'
        )
        read_only_fields = ('id',)

class StudentManageSerializer(serializers.ModelSerializer):
    profile_pic = serializers.SerializerMethodField()
    quiz_attempts = serializers.IntegerField(read_only=True)
    xp = serializers.IntegerField(read_only=True)
    active_subjects = serializers.IntegerField(read_only=True)
    is_banned = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'profile_pic',
            'full_name',
            'quiz_attempts',
            'xp',
            'active_subjects',
            'is_banned',
        )

    def get_profile_pic(self, obj):
        request = self.context.get('request')
        if obj.profile_pic and hasattr(obj.profile_pic, 'url'):
            return request.build_absolute_uri(obj.profile_pic.url)
        return None

    def get_is_banned(self, obj):
        if obj.is_active:
            return False
        return True


class ModuleUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Module
        fields = (
            'id',
            'module_name'
        )
        read_only_fields = (
            'id',
        )

class ModuleStatsSerializer(serializers.Serializer):
    module_name = serializers.CharField()
    quiz_attempted = serializers.IntegerField()
    average_score = serializers.FloatField()
    top_score = serializers.IntegerField()
    monthly_accuracy = serializers.ListField()


class QuestionUpdateSerializer(serializers.ModelSerializer):
    correct_answer = serializers.ChoiceField(
        choices=["option1", "option2", "option3", "option4"]
    )

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
            'correct_answer',
            'order',
        )
        read_only_fields = (
            'id', 
            'module'
        )

class OptionModulesPairSerializer(serializers.ModelSerializer):
    pair_number = serializers.IntegerField(read_only=True)  # auto-assigned

    class Meta:
        model = OptionModulesPair
        fields = ['id', 'module_a', 'module_b', 'pair_number']

    def validate(self, data):
        module_a = data.get('module_a')
        module_b = data.get('module_b')

        if module_a == module_b:
            raise serializers.ValidationError("Module A and Module B cannot be the same.")

        # Ensure the pair doesn't already exist in either order
        if OptionModulesPair.objects.filter(module_a=module_a, module_b=module_b).exists() or \
           OptionModulesPair.objects.filter(module_a=module_b, module_b=module_a).exists():
            raise serializers.ValidationError("This module pair already exists.")

        return data

    def create(self, validated_data):
        # Assign next available pair_number automatically
        last_pair = OptionModulesPair.objects.order_by('-pair_number').first()
        next_pair_number = (last_pair.pair_number if last_pair else 0) + 1
        validated_data['pair_number'] = next_pair_number
        return super().create(validated_data)


class SynopticModuleSerializer(serializers.ModelSerializer):
    module_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True
    )
    modules = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = SynopticModule
        fields = ['id', 'modules', 'module_ids']

    def get_modules(self, obj):
        return [{"id": m.id, "module_name": m.module_name} for m in obj.modules.all()]

    def validate_module_ids(self, value):
        if not (2 <= len(value) <= 4):
            raise serializers.ValidationError("You must select 3 or 4 modules for the Synoptic module.")
        return value

    def create(self, validated_data):
        module_ids = validated_data.pop('module_ids')
        synoptic_module = SynopticModule.objects.create()
        synoptic_module.modules.set(Module.objects.filter(id__in=module_ids))
        return synoptic_module
