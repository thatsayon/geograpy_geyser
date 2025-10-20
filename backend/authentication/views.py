from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, status, permissions

from .serializers import (
    LoginSerializer,
    RegisterSerializer
)

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        return Response(
            {"msg": "working"},
            status=status.HTTP_200_OK
        )

class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        return Response(
            {"msg": "working"},
            status=status.HTTP_200_OK
        )
