from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError
from rest_framework import generics, status, permissions

from .models import (
    Module,
    Questions,
    CustomTime,
    QuestionQuantity,
)
from .serializers import (
    ModuleSerializer,
    QuestionSerializer,
    CustomTimeSerializer,
    QuestionQuantitySerializer,
)

class CreateModuleView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    serializer_class = ModuleSerializer
    queryset = Module.objects.all()

class CreateQuestionView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    serializer_class = QuestionSerializer
    
    def get_queryset(self):
        module_id = self.request.query_params.get('module')
        if not module_id:
            raise ValidationError({"module": "This query parameter is required."})
        return Questions.objects.filter(module_id=module_id).order_by('order')

    def perform_create(self, serializer):
        module_id = self.request.data.get('module')
        if not module_id:
            raise ValidationError({"module": "You must provide a module ID to create a question."})
        serializer.save()

class CustomTimeView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    serializer_class = CustomTimeSerializer
    queryset = CustomTime.objects.all()

class QuestionQuantityView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    serializer_class = QuestionQuantitySerializer
    queryset = QuestionQuantity.objects.all()
