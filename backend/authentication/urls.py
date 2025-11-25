from django.urls import path
from .views import (
    LoginView,
    RegisterView,
    VerifyVerificationToken,
    VerifyOTP,
    UpdateUserProfileView,
    UpdatePasswordView,
    DeleteAccountView,
    ForgetPassView,
    ForgetPassOTPVerifyView,
    ForgettedPasswordSetView,
    ResendForgetPassOTPView,
)

urlpatterns = [
    path('login/', LoginView.as_view(), name='Login'),
    path('register/', RegisterView.as_view(), name='Register'),
    path('verify-verification-token/', VerifyVerificationToken.as_view(), name='Verify Verification Token'),
    path('verify-otp/', VerifyOTP.as_view(), name='Verify OTP'),
    path('profile-update/', UpdateUserProfileView.as_view(), name='Profile Update'),
    path('password-update/', UpdatePasswordView.as_view(), name='Profile Update'),
    path('delete-account/', DeleteAccountView.as_view(), name='Delete Account'),
    path('forget-password/', ForgetPassView.as_view(), name='Forget Password'),
    path('forget-password-otp-verify/', ForgetPassOTPVerifyView.as_view(), name='Forget Password OTP'),
    path('forget-password-set/', ForgettedPasswordSetView.as_view(), name='Forget Password Set'),
    path('forget-password-resend/', ResendForgetPassOTPView.as_view(), name='Resend Forget Password'),
]
