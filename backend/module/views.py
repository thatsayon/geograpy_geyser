from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework import generics, status, permissions

from django.db.models import Q

from .models import (
    Module,
    Questions,
    CustomTime,
    QuestionQuantity,
    OptionModulesPair
)
from .serializers import (
    ModuleSerializer,
    QuestionSerializer,
    CustomTimeSerializer,
    QuestionQuantitySerializer,
    OptionModulesPairSerializer,
)

class CreateModuleView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ModuleSerializer
    queryset = Module.objects.all().order_by('module_name')

class DeleteModuleView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    serializer_class = ModuleSerializer
    queryset = Module.objects.all()
    lookup_field = 'id'

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({"msg": "module deleted"}, status=status.HTTP_200_OK)

    
class CreateQuestionView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    serializer_class = QuestionSerializer
    
    def get_queryset(self):
        module_id = self.request.query_params.get('module')
        if not module_id:
            raise ValidationError({"module": "This query parameter is required."})

        search = self.request.query_params.get('search', '')

        queryset = Questions.objects.filter(module_id=module_id)

        if search:
            queryset = queryset.filter(
                Q(question_text__icontains=search) |
                Q(option1__icontains=search) |
                Q(option2__icontains=search) |
                Q(option3__icontains=search) |
                Q(option4__icontains=search) |
                Q(correct_answer__icontains=search)
            )

        return queryset.order_by('order')
    # def get_queryset(self):
    #     module_id = self.request.query_params.get('module')
    #     if not module_id:
    #         raise ValidationError({"module": "This query parameter is required."})
    #     return Questions.objects.filter(module_id=module_id).order_by('order')

    def perform_create(self, serializer):
        module_id = self.request.data.get('module')
        if not module_id:
            raise ValidationError({"module": "You must provide a module ID to create a question."})

        try:
            module = Module.objects.get(id=module_id)
        except Module.DoesNotExist:
            raise ValidationError({"module": "Invalid module ID."})

        serializer.save(module=module)


class CustomTimeView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CustomTimeSerializer
    queryset = CustomTime.objects.all()

class QuestionQuantityView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    serializer_class = QuestionQuantitySerializer
    queryset = QuestionQuantity.objects.all()

class OptionModulesPairView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    serializer_class = OptionModulesPairSerializer
    queryset = OptionModulesPair.objects.all()
