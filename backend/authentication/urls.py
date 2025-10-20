from django.urls import path
from .views import (
    LoginView,
    RegisterView,
    VerifyVerificationToken,
    VerifyOTP,
)

urlpatterns = [
    path('login/', LoginView.as_view(), name='Login'),
    path('register/', RegisterView.as_view(), name='Register'),
    path('verify-verification-token/', VerifyVerificationToken.as_view(), name='Verify Verification Token'),
    path('verify-otp/', VerifyOTP.as_view(), name='Verify OTP')
]
