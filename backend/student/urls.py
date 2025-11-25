from django.urls import path
from module.views import (
    CreateModuleView,
    CustomTimeView,
    OptionModulesPairView,
)
from account.views import (
    OptionalModulesView,
)
from .views import (
    QuizStartView, 
    SynopticQuizStartView,
    QuizFinishView, 
    StudentStatsView, 
    DeductQuizXPView, 
    UserPerformanceView,
)

urlpatterns = [
    path('module-list/', CreateModuleView.as_view()),
    path('time-list/', CustomTimeView.as_view()),
    path('optional-module/', OptionalModulesView.as_view()),
    path("quiz-start/", QuizStartView.as_view()),
    path("synoptic-quiz-start/", SynopticQuizStartView.as_view()),
    path("quiz-finish/", QuizFinishView.as_view()),
    path("student-state/", StudentStatsView.as_view()),
    path("delete-xp/", DeductQuizXPView.as_view()),
    path("user-performance/", UserPerformanceView.as_view()),
]
