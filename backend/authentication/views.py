from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, status, permissions

from django.utils.timezone import now
from django.contrib.auth import get_user_model, authenticate
from django.db import transaction

from .serializers import (
    LoginSerializer,
    RegisterSerializer,
    CustomTokenObtainPairSerializer
)
from .models import (
    OTP
)
from .utils import (
    generate_otp,
    create_otp_token,
    decode_otp_token
)

User = get_user_model()

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(
            username=serializer.validated_data.get("email"),
            password=serializer.validated_data.get("password")
        )

        if not user:
            return Response(
                {"error": "Invalid email or password."},
                status=status.HTTP_401_UNAUTHORIZED
            ) 

        refresh = CustomTokenObtainPairSerializer.get_token(user) 
        access = refresh.access_token

        response = Response(
            {
                "access_token": str(access),
                "refresh_token": str(refresh)
            },
            status=status.HTTP_200_OK,
        )
        return response


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                user = serializer.save()
                otp = generate_otp()

                OTP.objects.create(
                    user=user,
                    otp=otp,
                    created_at=now()
                )
                verificationToken = create_otp_token(user.id)

                response = Response(
                    {
                        "success": True,
                        "message": "User registration successful. OTP will be sent to email.",
                        "user": {
                            "id": str(user.id), 
                            "email": user.email
                        },
                        "verificationToken": verificationToken,
                    },
                    status=status.HTTP_201_CREATED
                )
                return response
        except Exception as e:
            return Response(
                {"success": False, "message": "Registration failed. Please try again later."},
                status=status.HTTP_400_BAD_REQUEST
            )

"""
This view is for to check is verification token 
is valid or not. 

Just have to send the verification token
"""
class VerifyVerificationToken(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        otp_token = request.data.get('verificationToken')
        if not otp_token:
            return Response({"error": "No token found"})
        
        decode = decode_otp_token(otp_token)
        if not decode:
            return Response(
                {"error": "Invalid or expired token."},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(
            {"message": "Valid token"},
            status=status.HTTP_200_OK
        )


class VerifyOTP(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        otp = request.data.get('otp')

        # Retrieve the OTP token from cookies
        otp_token = request.data.get('verificationToken')
        if not otp_token or not otp:
            return Response({"error": "OTP token and OTP are required."}, status=status.HTTP_400_BAD_REQUEST)

        # Decode the token
        decoded = decode_otp_token(otp_token)
        if not decoded:
            return Response({"error": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)

        # Get the user ID from the token
        user_id = decoded.get("user_id")
        try:
            user = User._default_manager.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        otp_instance = user.otps.filter(otp=otp).first()
        if not otp_instance or not otp_instance.is_valid():
            return Response({"error": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)

        # Activate the user and clear OTPs
        user.is_active = True
        user.otps.all().delete()
        user.save()

        # Generate tokens
        refresh = CustomTokenObtainPairSerializer.get_token(user)
        access_token = str(refresh.access_token)

        # Set refresh token as an HttpOnly cookie
        response = Response(
            {
                "access_token": str(access_token),
                "refresh_token": str(refresh)
            },
            status=status.HTTP_200_OK
        )
        return response
