from django.urls import path
from .views import (
    LoginView,
    RegisterView,
    VerifyVerificationToken,
    VerifyOTP,
    UpdateUserProfileView,
    UpdatePasswordView,
    DeleteAccountView,
)

urlpatterns = [
    path('login/', LoginView.as_view(), name='Login'),
    path('register/', RegisterView.as_view(), name='Register'),
    path('verify-verification-token/', VerifyVerificationToken.as_view(), name='Verify Verification Token'),
    path('verify-otp/', VerifyOTP.as_view(), name='Verify OTP'),
    path('profile-update/', UpdateUserProfileView.as_view(), name='Profile Update'),
    path('password-update/', UpdatePasswordView.as_view(), name='Profile Update'),
    path('delete-account/', DeleteAccountView.as_view(), name='Delete Account'),
]
