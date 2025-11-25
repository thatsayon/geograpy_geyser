from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import permissions, status, generics
from rest_framework.exceptions import ValidationError

from django.contrib.auth import get_user_model
from django.db.models import Count, Sum, Q, Value, IntegerField, Avg, FloatField, Max, ExpressionWrapper, F
from django.db.models.functions import Coalesce, ExtractMonth
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.http import FileResponse
from django.conf import settings
from django.db import transaction

from datetime import timedelta
from calendar import month_abbr

from module.models import (
    CustomTime,
    QuizAttend,
    Module,
    Questions,
    OptionModulesPair,
)

from .serializers import (
    ProfileInformationSerializer,
    ChangePasswordSerializer,

    CustomTimeSerializer,

    StudentManageSerializer,

    ModuleStatsSerializer,
    ModuleUpdateSerializer,

    QuestionUpdateSerializer,

    OptionModulesPairSerializer,

    SynopticModuleSerializer,
)

from .models import SynopticModule

import os
import csv

User = get_user_model()

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


# quiz duration views

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


# student management views
class StudentManageListView(generics.ListAPIView):
    permission_classes = [permissions.IsAdminUser]
    serializer_class = StudentManageSerializer

    def get_queryset(self):
        qs = User.objects.all()
        now = timezone.now()

        duration = self.request.query_params.get('duration')
        order_by = self.request.query_params.get('order_by')
        search = self.request.query_params.get('search')

        # Filter by name search if provided
        if search:
            qs = qs.filter(full_name__icontains=search)

        # compute start_date for duration filters
        if duration in ['daily', 'weekly', 'monthly', 'yearly']:
            if duration == 'daily':
                start_date = now - timedelta(days=1)
            elif duration == 'weekly':
                start_date = now - timedelta(weeks=1)
            elif duration == 'monthly':
                start_date = now - timedelta(days=30)
            else:  # yearly
                start_date = now - timedelta(days=365)

            count_filter = Q(quizattend__created_at__gte=start_date)
            sum_filter = Q(quizattend__created_at__gte=start_date)
            module_filter = Q(quizattend__created_at__gte=start_date)
        else:
            # all-time (no time filter)
            count_filter = Q()
            sum_filter = Q()
            module_filter = Q()

        # Annotate with coalesced values so nulls become 0
        qs = qs.annotate(
            quiz_attempts=Coalesce(
                Count('quizattend', filter=count_filter, distinct=True),
                Value(0),
                output_field=IntegerField()
            ),
            xp=Coalesce(
                Sum('quizattend__xp_gained', filter=sum_filter),
                Value(0),
                output_field=IntegerField()
            ),
            active_subjects=Coalesce(
                Count('quizattend__module', filter=module_filter, distinct=True),
                Value(0),
                output_field=IntegerField()
            ),
        )

        # Allowed order fields map -> annotated names (descending)
        allowed = {
            'xp': '-xp',
            'quiz_attempts': '-quiz_attempts',
            'active_subjects': '-active_subjects'
        }

        if order_by in allowed:
            qs = qs.order_by(allowed[order_by])
        else:
            qs = qs.order_by('-xp')  # top XP by default

        return qs


class BlockUserView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        user_id = request.data.get('user_id')

        if not user_id:
            return Response({
                "error": "user_id field required"
            }, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(id=user_id).first()
        user.is_active = False
        user.save()
        return Response({
            "msg": "User is banned"
        }, status=status.HTTP_200_OK)

class UnblockUserView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        user_id = request.data.get('user_id')

        if not user_id:
            return Response({
                "error": "user_id field required"
            }, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(id=user_id).first()
        user.is_active = True
        user.save()
        return Response({
            "msg": "User is unbanned"
        }, status=status.HTTP_200_OK)

class StudentDashboardView(APIView):
    """
    API View to get complete student dashboard data including:
    - User profile (name, XP, rank, profile picture)
    - Average accuracy over time (monthly chart data)
    - Subject performance by module
    - Quiz statistics (total attempted, average score, subjects covered)
    """
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        user_id = request.query_params.get('user_id')

        user = User.objects.filter(id=user_id).first()
        
        try:
            # Get user profile data
            profile_data = self.get_profile_data(user)
            
            # Get monthly average accuracy for chart
            monthly_accuracy = self.get_monthly_accuracy(user)
            
            # Get subject performance
            subject_performance = self.get_subject_performance(user)
            
            # Get quiz statistics
            quiz_statistics = self.get_quiz_statistics(user)
            
            dashboard_data = {
                'profile': profile_data,
                'monthly_accuracy': monthly_accuracy,
                'subject_performance': subject_performance,
                'quiz_statistics': quiz_statistics
            }
            
            return Response(dashboard_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def get_profile_data(self, user):
        """Get user profile including XP and rank"""
        # Get total XP
        total_xp = QuizAttend.objects.filter(student=user).aggregate(
            total_xp=Sum('xp_gained')
        )['total_xp'] or 0
        
        # Calculate rank (users with more XP + 1)
        users_with_more_xp = QuizAttend.objects.values('student').annotate(
            student_xp=Sum('xp_gained')
        ).filter(student_xp__gt=total_xp).count()
        
        rank = users_with_more_xp + 1
        
        return {
            'full_name': user.full_name,
            'email': user.email,
            'profile_pic': user.profile_pic.url if user.profile_pic else None,
            'xp': total_xp,
            'rank': rank
        }
    
    def get_monthly_accuracy(self, user):
        """Get average accuracy data for the last 12 months"""
        monthly_data = []
        current_date = timezone.now()
        
        for i in range(11, -1, -1):  # Last 12 months
            # Calculate month boundaries
            target_date = current_date - timedelta(days=30 * i)
            month_start = target_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            # Get next month's first day
            if month_start.month == 12:
                month_end = month_start.replace(year=month_start.year + 1, month=1, day=1)
            else:
                month_end = month_start.replace(month=month_start.month + 1, day=1)
            
            # Query quizzes for this month
            month_quizzes = QuizAttend.objects.filter(
                student=user,
                created_at__gte=month_start,
                created_at__lt=month_end
            ).aggregate(
                total_correct=Sum('correct_answers'),
                total_attempted=Sum('attempted_questions')
            )
            
            # Calculate accuracy (scaled to match chart values ~700-1300)
            if month_quizzes['total_attempted'] and month_quizzes['total_attempted'] > 0:
                accuracy_percent = (month_quizzes['total_correct'] / 
                                  month_quizzes['total_attempted'])
                accuracy_value = int(accuracy_percent * 1000)  # Scale to chart range
            else:
                accuracy_value = 0
            
            monthly_data.append({
                'month': month_abbr[month_start.month],
                'value': accuracy_value
            })
        
        return monthly_data
    
    def get_subject_performance(self, user):
        """Get performance percentage for each subject/module"""
        subject_performance = []
        modules = Module.objects.all()
        
        for module in modules:
            # Get all quizzes for this module
            module_quizzes = QuizAttend.objects.filter(
                student=user,
                module=module
            ).aggregate(
                total_correct=Sum('correct_answers'),
                total_attempted=Sum('attempted_questions')
            )
            
            # Calculate accuracy percentage
            if module_quizzes['total_attempted'] and module_quizzes['total_attempted'] > 0:
                accuracy = int(
                    (module_quizzes['total_correct'] / 
                     module_quizzes['total_attempted']) * 100
                )
            else:
                accuracy = 0
            
            subject_performance.append({
                'subject': module.module_name,
                'accuracy': accuracy
            })
        
        # Sort by accuracy (optional)
        subject_performance.sort(key=lambda x: x['accuracy'], reverse=True)
        
        return subject_performance
    
    def get_quiz_statistics(self, user):
        """Get overall quiz statistics"""
        # Get quiz stats
        stats = QuizAttend.objects.filter(student=user).aggregate(
            total_quizzes=Count('id'),
            average_score=Avg('score'),
            unique_modules=Count('module', distinct=True)
        )
        
        return {
            'quiz_attempted': stats['total_quizzes'] or 0,
            'average_score': int(stats['average_score']) if stats['average_score'] else 0,
            'subject_covered': stats['unique_modules'] or 0
        }


class AdminDashboardView(APIView):
    """
    Admin dashboard with overall statistics:
    - Student counts (total, new, active, inactive)
    - Subject and quiz stats
    - Average accuracy chart
    - Subject performance across all students
    """
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        try:
            # Get filter period (day/month/year)
            period = request.query_params.get('period', 'month')
            
            dashboard_data = {
                'student_stats': self.get_student_stats(period),
                'quiz_stats': self.get_quiz_stats(period),
                'average_accuracy': self.get_average_accuracy(period),
                'subject_performance': self.get_subject_performance()
            }
            
            return Response(dashboard_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def get_student_stats(self, period):
        """Get student statistics"""
        # Calculate date range based on period
        now = timezone.now()
        if period == 'day':
            date_from = now - timedelta(days=1)
        elif period == 'year':
            date_from = now - timedelta(days=365)
        else:  # month
            date_from = now - timedelta(days=30)
        
        # Total students
        total_students = User.objects.count()
        
        # New students (joined in period)
        new_students = User.objects.filter(
            date_joined__gte=date_from
        ).count()
        
        # Active students (took quiz in period)
        active_students = User.objects.filter(
            quizattend__created_at__gte=date_from
        ).distinct().count()
        
        # Inactive students
        inactive_students = total_students - active_students
        
        return {
            'total_students': total_students,
            'new_students': new_students,
            'active_students': active_students,
            'inactive_students': inactive_students
        }
    
    def get_quiz_stats(self, period):
        """Get quiz statistics"""
        # Total subjects
        total_subjects = Module.objects.count()
        
        # Calculate date range
        now = timezone.now()
        if period == 'day':
            date_from = now - timedelta(days=1)
        else:
            date_from = now - timedelta(days=30)
        
        # Quiz participants in period
        quiz_participants = QuizAttend.objects.filter(
            created_at__gte=date_from
        ).values('student').distinct().count()
        
        return {
            'total_subjects': total_subjects,
            'quiz_participants': quiz_participants
        }
    
    def get_average_accuracy(self, period):
        """Get average accuracy based on period (day/month/year)"""
        accuracy_data = []
        current_date = timezone.now()
        
        if period == 'day':
            # Last 24 hours, hourly breakdown
            for i in range(23, -1, -1):
                hour_start = current_date - timedelta(hours=i)
                hour_end = hour_start + timedelta(hours=1)
                
                hour_quizzes = QuizAttend.objects.filter(
                    created_at__gte=hour_start,
                    created_at__lt=hour_end
                ).aggregate(
                    total_correct=Sum('correct_answers'),
                    total_attempted=Sum('attempted_questions')
                )
                
                if hour_quizzes['total_attempted'] and hour_quizzes['total_attempted'] > 0:
                    accuracy_value = int((hour_quizzes['total_correct'] / 
                                        hour_quizzes['total_attempted']) * 1000)
                else:
                    accuracy_value = 0
                
                accuracy_data.append({
                    'month': f"{hour_start.hour}:00",
                    'value': accuracy_value
                })
        
        elif period == 'year':
            # Last 12 months
            for i in range(11, -1, -1):
                target_date = current_date - timedelta(days=30 * i)
                month_start = target_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                
                if month_start.month == 12:
                    month_end = month_start.replace(year=month_start.year + 1, month=1, day=1)
                else:
                    month_end = month_start.replace(month=month_start.month + 1, day=1)
                
                month_quizzes = QuizAttend.objects.filter(
                    created_at__gte=month_start,
                    created_at__lt=month_end
                ).aggregate(
                    total_correct=Sum('correct_answers'),
                    total_attempted=Sum('attempted_questions')
                )
                
                if month_quizzes['total_attempted'] and month_quizzes['total_attempted'] > 0:
                    accuracy_value = int((month_quizzes['total_correct'] / 
                                        month_quizzes['total_attempted']) * 1000)
                else:
                    accuracy_value = 0
                
                accuracy_data.append({
                    'label': month_abbr[month_start.month],
                    'value': accuracy_value
                })
        
        else:  # month (default) - last 30 days
            for i in range(29, -1, -1):
                day_start = (current_date - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
                day_end = day_start + timedelta(days=1)
                
                day_quizzes = QuizAttend.objects.filter(
                    created_at__gte=day_start,
                    created_at__lt=day_end
                ).aggregate(
                    total_correct=Sum('correct_answers'),
                    total_attempted=Sum('attempted_questions')
                )
                
                if day_quizzes['total_attempted'] and day_quizzes['total_attempted'] > 0:
                    accuracy_value = int((day_quizzes['total_correct'] / 
                                        day_quizzes['total_attempted']) * 1000)
                else:
                    accuracy_value = 0
                
                accuracy_data.append({
                    'label': day_start.strftime('%d'),
                    'value': accuracy_value
                })
        
        return accuracy_data
    
    def get_subject_performance(self):
        """Get overall subject performance across all students"""
        subject_performance = []
        modules = Module.objects.all()
        
        for module in modules:
            # Get all quizzes for this module
            module_quizzes = QuizAttend.objects.filter(
                module=module
            ).aggregate(
                total_correct=Sum('correct_answers'),
                total_attempted=Sum('attempted_questions')
            )
            
            # Calculate accuracy
            if module_quizzes['total_attempted'] and module_quizzes['total_attempted'] > 0:
                accuracy = int(
                    (module_quizzes['total_correct'] / 
                     module_quizzes['total_attempted']) * 100
                )
            else:
                accuracy = 0
            
            subject_performance.append({
                'subject': module.module_name,
                'accuracy': accuracy
            })
        
        return subject_performance


class ModuleUpdateView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAdminUser]
    serializer_class = ModuleUpdateSerializer
    lookup_field = 'id'
    queryset = Module.objects.all()

class ModuleStatsView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ModuleStatsSerializer
    lookup_field = 'id'

    def get_queryset(self):
        return Module.objects.all()

    def retrieve(self, request, *args, **kwargs):
        module = self.get_object()
        student = request.user

        queryset = QuizAttend.objects.filter(module=module, student=student)

        quiz_attempted = queryset.count()
        average_score = queryset.aggregate(avg=Avg('score'))['avg'] or 0
        top_score = queryset.aggregate(max=Max('score'))['max'] or 0

        # Monthly accuracy: (correct / attempted * 100)
        monthly_data = (
            queryset
            .annotate(month=ExtractMonth('created_at'))
            .values('month')
            .annotate(
                accuracy=Avg(
                    ExpressionWrapper(
                        F('correct_answers') * 100.0 / F('attempted_questions'),
                        output_field=FloatField()
                    )
                )
            )
            .order_by('month')
        )

        month_names = [
            "Jan","Feb","Mar","Apr","May","Jun",
            "Jul","Aug","Sep","Oct","Nov","Dec"
        ]

        monthly_accuracy = [
            {
                "month": month_names[m['month']-1],
                "accuracy": round(m['accuracy'], 2)
            }
            for m in monthly_data if m['month']
        ]

        data = {
            "module_name": module.module_name,
            "quiz_attempted": quiz_attempted,
            "average_score": round(average_score, 2),
            "top_score": top_score,
            "monthly_accuracy": monthly_accuracy
        }

        serializer = self.get_serializer(data)
        return Response(serializer.data)

class QuestionUpdateView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    queryset = Questions.objects.all()
    serializer_class = QuestionUpdateSerializer
    lookup_field = 'id'

    def perform_update(self, serializer):
        validated_data = serializer.validated_data

        # correct_answer is one of: option1, option2, option3, option4
        correct_key = validated_data.get('correct_answer')

        # # But still ensure the actual option text exists
        # option_value = validated_data.get(correct_key)
        # if not option_value:
        #     raise ValidationError({
        #         "correct_answer": "The selected option has no value."
        #     })

        serializer.save()


class OptionModulesPairView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    serializer_class = OptionModulesPairSerializer

    def get_queryset(self):
        module_id = self.request.query_params.get('module')
        queryset = OptionModulesPair.objects.all()
        if module_id:
            queryset = queryset.filter(module_a__id=module_id) | queryset.filter(module_b__id=module_id)
        return queryset.order_by('pair_number')

class OptionModulesPairDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    queryset = OptionModulesPair.objects.all()
    serializer_class = OptionModulesPairSerializer
    lookup_field = 'id'

class DownloadDemoCSVView(APIView):
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        file_path = os.path.join(settings.BASE_DIR, 'demo.csv')

        if not os.path.exists(file_path):
            return HttpResponse("File not found", status=404)

        return FileResponse(
            open(file_path, 'rb'),
            as_attachment=True,
            filename='demo.csv'
        )


class UploadQuestionsCSVView(APIView):
    permission_classes = [permissions.IsAdminUser] 

    def post(self, request, module_id):
        module = get_object_or_404(Module, id=module_id)

        csv_file = request.FILES.get('file')
        if not csv_file:
            return Response({"error": "CSV file is required"}, status=status.HTTP_400_BAD_REQUEST)

        if not csv_file.name.endswith('.csv'):
            return Response({"error": "File must be a .csv"}, status=status.HTTP_400_BAD_REQUEST)

        decoded_file = csv_file.read().decode('utf-8').splitlines()
        reader = csv.DictReader(decoded_file)

        created_count = 0

        with transaction.atomic():
            for idx, row in enumerate(reader, start=1):

                # Skip empty rows
                if not row.get("question") or row.get("question").strip() == "":
                    continue

                correct = row.get("correct_answer")
                if correct not in ["option1", "option2", "option3", "option4"]:
                    return Response(
                        {"error": f"Invalid correct_answer at row {idx}: {correct}"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                Questions.objects.create(
                    module=module,
                    question_text=row.get("question").strip(),
                    option1=row.get("option1", "").strip(),
                    option2=row.get("option2", "").strip(),
                    option3=row.get("option3", "").strip(),
                    option4=row.get("option4", "").strip(),
                    correct_answer=correct
                )

                created_count += 1

        return Response({"message": f"{created_count} questions imported successfully."},
                        status=status.HTTP_201_CREATED)


class CreateSynopticModuleView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    serializer_class = SynopticModuleSerializer
    queryset = SynopticModule.objects.all()
