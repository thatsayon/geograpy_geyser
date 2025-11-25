from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, status, permissions

from django.utils.timezone import now
from django.contrib.auth import get_user_model, authenticate
from django.shortcuts import get_object_or_404
from django.db import transaction

from account.models import OptionalModule

from .serializers import (
    LoginSerializer,
    RegisterSerializer,
    UserProfileUpdateSerializer,
    CustomTokenObtainPairSerializer,
    UpdatePasswordSerializer,
    UserProfileGetSerializer,
)

from .tasks import (
    send_password_reset_email_task,
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

        is_optional_module_selected = OptionalModule.objects.filter(student=user).exists()

        response = Response(
            {
                "access_token": str(access),
                "refresh_token": str(refresh),
                "is_optional_module_selected": is_optional_module_selected
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


  
class ForgetPassView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response(
                {"message": "email is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = get_object_or_404(User, email=email)

        otp = generate_otp()

        OTP.objects.create(
            user=user,
            otp=otp,
            created_at=now()
        )

        send_password_reset_email_task.delay(
            user.email,
            user.full_name,
            otp
        )

        passResetToken = create_otp_token(user.id)

        response = Response(
            {
                "msg": "OTP send successfully",
                "user": {
                    "id": str(user.id),
                    "email": user.email
                },
                "passResetToken": passResetToken
            }
        )
        
        return response


class ForgetPassOTPVerifyView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request): 
        otp = request.data.get("otp")
        reset_token = request.data.get("passResetToken")
        
        if not otp or not reset_token:
            return Response({"error": "OTP and reset token are required."}, status=status.HTTP_400_BAD_REQUEST)
        
        decoded = decode_otp_token(reset_token)
        if not decoded:
            return Response({"error": "Invalid or expired reset token."}, status=status.HTTP_400_BAD_REQUEST)
        
        user_id = decoded.get("user_id")

        user = get_object_or_404(User, id=user_id)

        otp_instance = user.otps.filter(otp=otp).first()
        if not otp_instance or not otp_instance.is_valid():
            return Response({"error": "Invalid or expired OTP."}, status=status.HTTP_400_BAD_REQUEST)
        
        # If OTP is valid, generate a verified token indicating that the OTP step is complete.
        verified_payload = {"user_id": str(user.id), "verified": True}
        verified_token = create_otp_token(verified_payload)
        
        # Optionally, delete the used OTP instance to prevent reuse.
        otp_instance.delete()
        
        response = Response(
            {
                "msg": "OTP verified. You can now reset your password.",
                "passwordResetVerified": verified_token
            }, 
            status=status.HTTP_200_OK
        )

        return response


class ForgettedPasswordSetView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        new_password = request.data.get("new_password")
        verified_token = request.data.get("passwordResetVerified")
        
        if not new_password or not verified_token:
            return Response({"error": "New password and verified token are required."}, status=status.HTTP_400_BAD_REQUEST)
        
        decoded = decode_otp_token(verified_token)
        if not decoded or not decoded.get("verified"):
            return Response({"error": "Invalid or expired verified token."}, status=status.HTTP_400_BAD_REQUEST)
        
        user_id = decoded.get("user_id")
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        
        # Set the new password
        user.set_password(new_password)
        user.save()
        
        response = Response({"msg": "Password reset successfully."}, status=status.HTTP_200_OK)
        # Remove the verified token (and optionally the original reset token)
        return response

class ResendForgetPassOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        reset_token = request.data.get("passResetToken")
        if not reset_token:
            return Response({"error": "No reset token found."}, status=status.HTTP_400_BAD_REQUEST)

        decoded = decode_otp_token(reset_token)
        if not decoded:
            return Response({"error": "Invalid or expired reset token."}, status=status.HTTP_400_BAD_REQUEST)

        user_id = decoded.get("user_id")
        user = get_object_or_404(User, id=user_id)

        otp = generate_otp()
        OTP.objects.create(user=user, otp=otp, created_at=now())

        send_password_reset_email_task.delay(user.email, user.full_name, otp)

        return Response(
            {"message": "Password reset OTP resent successfully to your email."},
            status=status.HTTP_200_OK
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

class UpdateUserProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserProfileGetSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        serializer = UserProfileUpdateSerializer(
            request.user,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "Profile updated successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UpdatePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request):
        serializer = UpdatePasswordSerializer(
            data=request.data,
            context={"request": request}
        )

        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Password updated successfully"}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteAccountView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        password = request.data.get("password")

        if not password:
            return Response(
                {"error": "Password is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verify the user’s password
        if not user.check_password(password):
            return Response(
                {"error": "Invalid password"},
                status=status.HTTP_403_FORBIDDEN
            )

        refresh_token = request.data.get("refresh")
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except Exception:
                pass  # token might already be invalid — that's fine

        user.delete()

        return Response(
            {"message": "Account deleted successfully"},
            status=status.HTTP_200_OK
        )


