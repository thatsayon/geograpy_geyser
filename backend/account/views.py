from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from module.models import (
    OptionModulesPair,
    Module,
)

from .models import OptionalModule
from .serializers import OptionModulesPairSerializer, ModuleSerializer

class OptionalModulesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = OptionModulesPair.objects.all().order_by('pair_number')
        serializer = OptionModulesPairSerializer(
            data, many=True, context={'request': request}
        )
        return Response(serializer.data)

    def patch(self, request):
        user = request.user
        selections = request.data.get("selections", [])

        if not selections:
            return Response(
                {"detail": "No selections provided"},
                status=status.HTTP_400_BAD_REQUEST
            )

        for item in selections:
            pair_number = item['pair_number']
            module_id = item['selected_module']

            OptionalModule.objects.update_or_create(
                student=user,
                pair_number=pair_number,
                defaults={"selected_module_id": module_id}
            )

        return Response(
            {"detail": "Selections updated successfully"},
            status=status.HTTP_200_OK
        )
