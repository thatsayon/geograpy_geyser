from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import permissions, status, generics

from module.models import (
    CustomTime,
)

from .serializers import (
    ProfileInformationSerializer,
    ChangePasswordSerializer,

    CustomTimeSerializer,
)

class ProfileInformationView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileInformationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Password changed successfully"}, status=status.HTTP_200_OK)

class CustomTimeListView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    serializer_class = CustomTimeSerializer

    def get_queryset(self):
        return CustomTime.objects.all().order_by('duration')

class CustomTimeView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    serializer_class = CustomTimeSerializer
    queryset = CustomTime.objects.all()
    lookup_field = 'id'
