from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

class QuizTestView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        time = request.GET.get('time')

        if not time:
            return Response({
                "error": "time is required"
            }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "msg": "working"
        }, status=status.HTTP_200_OK)
