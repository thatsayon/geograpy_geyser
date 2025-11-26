from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import get_user_model

User = get_user_model()

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            'email',
            'full_name',
            'password'
        )

    def create(self, validated_data):
        email = validated_data.get("email")
        full_name = validated_data.get("full_name", "").strip()
        password = validated_data.get("password")


        user = User.objects.create_user(
            email=email,
            full_name=full_name,
            password=password,
            is_active=False,  
        )
        return user


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    profile_pic = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("full_name", "profile_pic")

    def get_profile_pic(self, obj):
        if obj.profile_pic:
            return obj.profile_pic.url    
        return None


class UserProfileGetSerializer(serializers.ModelSerializer):
    profile_pic = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("full_name", "email", "profile_pic")

    def get_profile_pic(self, obj):
        return obj.profile_pic.url if obj.profile_pic else None


class UpdatePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = self.context['request'].user

        if not user.check_password(attrs['old_password']):
            raise serializers.ValidationError({"old_password": "Wrong password"})

        validate_password(attrs["new_password"])  # uses Django password validators

        return attrs

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data["new_password"])  # <-- Proper hashing
        user.save()
        return user

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token['full_name'] = user.full_name
        token['email'] = user.email
        if getattr(user, 'profile_pic', None):
            try:
                token['profile_pic'] = str(user.profile_pic.url)
            except:
                token['profile_pic'] = 'https://cdn.pixabay.com/photo/2015/10/05/22/37/blank-profile-picture-973460_1280.png'
        else:
            token['profile_pic'] = 'https://cdn.pixabay.com/photo/2015/10/05/22/37/blank-profile-picture-973460_1280.png'

        return token
