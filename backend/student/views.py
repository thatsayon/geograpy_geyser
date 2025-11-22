# module/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from django.shortcuts import get_object_or_404
from django.db.models import Avg, Sum, Count
from django.utils.timezone import localdate
from datetime import timedelta
from module.models import Module, Questions, QuizAttend
from module.serializers import ModuleSerializer
from .serializers import QuestionSerializer, QuizAttendSerializer, SubjectPerformanceSerializer, UserPerformanceSerializer
import random

class QuizStartView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        module_id = request.data.get("module_id")
        total_questions = int(request.data.get("quantity", 10))

        module = get_object_or_404(Module, id=module_id)

        quiz = QuizAttend.objects.create(
            student=request.user,
            module=module,
            total_questions=total_questions,
        )

        questions = Questions.objects.filter(module=module).order_by("?")[:total_questions]
        return Response({
            "quiz_id": quiz.id,
            "questions": QuestionSerializer(questions, many=True).data
        }, status=status.HTTP_200_OK)

class QuizFinishView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        quiz_id = request.data.get("quiz_id")
        correct = int(request.data.get("correct", 0))
        attempted = int(request.data.get("attempted", 0))

        if not attempted:
            return Response({
                "error": "attempted field needed"
            }, status=status.HTTP_400_BAD_REQUEST)

        quiz = get_object_or_404(QuizAttend, id=quiz_id, student=request.user)

        # Save results
        quiz.correct_answers = correct
        quiz.attempted_questions = attempted
        quiz.score = correct * 10
        quiz.xp_gained = correct * 5

        # Grade based on accuracy
        if attempted == 0:
            quiz.grade = "F"
        else:
            accuracy = correct / attempted
            if accuracy == 1.0:
                quiz.grade = "A+"
            elif accuracy >= 0.7:
                quiz.grade = "A"
            elif accuracy >= 0.5:
                quiz.grade = "B"
            else:
                quiz.grade = "F"

        quiz.save()

        # Suggest random modules to attend next
        all_modules = list(Module.objects.exclude(id=quiz.module.id))
        random_modules = random.sample(all_modules, min(len(all_modules), 3))
        modules_data = ModuleSerializer(random_modules, many=True).data

        response_data = QuizAttendSerializer(quiz).data
        response_data["attend_another_quiz"] = modules_data

        return Response(response_data, status=status.HTTP_200_OK)


class StudentStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        student = request.user

        stats = QuizAttend.objects.filter(student=student)

        if not stats.exists():
            return Response({
                "average_score": 0,
                "total_attempted_quizzes": 0,
                "total_xp": 0,
                "daily_streak": 0,
                "last_activity": None,
                "strongest_module": None
            })

        # Total XP
        total_xp = stats.aggregate(Sum("xp_gained"))["xp_gained__sum"]

        # Total quiz attempts
        total_attempted = stats.count()

        # Average score
        avg_score = stats.aggregate(Avg("score"))["score__avg"]

        # Last activity
        last_activity = stats.latest("created_at").created_at

        # Strongest module (module attempted the most)
        strongest_module_data = (
            stats.values("module__module_name")
            .annotate(count=Count("id"))
            .order_by("-count")
            .first()
        )
        strongest_module = strongest_module_data["module__module_name"]

        # Daily streak calculation
        dates = list(stats.order_by("-created_at").values_list("created_at", flat=True))
        streak = 1
        today = localdate()

        for d in dates[1:]:
            if localdate(d) == today - timedelta(days=streak):
                streak += 1
            else:
                break

        return Response({
            "average_score": round(avg_score, 2),
            "total_attempted_quizzes": total_attempted,
            "total_xp": total_xp,
            "daily_streak": streak,
            "last_activity": last_activity,
            "strongest_module": strongest_module,
        })

class DeductQuizXPView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        quizzes = QuizAttend.objects.filter(student=request.user).order_by('created_at')
        if not quizzes.exists():
            return Response({"error": "No quiz records found."}, status=status.HTTP_404_NOT_FOUND)

        xp_to_deduct = 200
        for quiz in quizzes:
            if xp_to_deduct <= 0:
                break

            if quiz.xp_gained >= xp_to_deduct:
                quiz.xp_gained -= xp_to_deduct
                xp_to_deduct = 0
            else:
                xp_to_deduct -= quiz.xp_gained
                quiz.xp_gained = 0

            quiz.save()

        return Response({
            "message": "200 XP deducted from student's quizzes",
            "remaining_to_deduct": xp_to_deduct  # should be 0 if fully deducted
        }, status=status.HTTP_200_OK)

class UserPerformanceView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserPerformanceSerializer(request.user)
        return Response(serializer.data)
