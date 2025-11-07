from django.urls import path
from module.views import (
    CreateModuleView,
    CustomTimeView,
    OptionModulesPairView,
)
from .views import QuizStartView, QuizFinishView, StudentStatsView, DeductQuizXPView, UserPerformanceView

urlpatterns = [
    path('module-list/', CreateModuleView.as_view()),
    path('time-list/', CustomTimeView.as_view()),
    path('optional-module/', OptionModulesPairView.as_view()),
    path("quiz-start/", QuizStartView.as_view()),
    path("quiz-finish/", QuizFinishView.as_view()),
    path("student-state/", StudentStatsView.as_view()),
    path("delete-xp/", DeductQuizXPView.as_view()),
    path("user-performance/", UserPerformanceView.as_view()),
]
