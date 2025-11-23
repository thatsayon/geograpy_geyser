from django.contrib.auth import get_user_model
from django.db.models import Count, Sum, Q, Value, IntegerField, Avg, FloatField
from django.db.models.functions import Coalesce

from rest_framework import serializers

from module.models import (
    CustomTime,
)

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
        )

    def get_profile_pic(self, obj):
        request = self.context.get('request')
        if obj.profile_pic and hasattr(obj.profile_pic, 'url'):
            return request.build_absolute_uri(obj.profile_pic.url)
        return None
