from django.urls import path

from module.views import (
    CreateModuleView,
    DeleteModuleView,
    CreateQuestionView,
)

from .views import (
    ProfileInformationView,
    ChangePasswordView,

    CustomTimeListView,
    CustomTimeView,

    StudentManageListView,
    StudentDashboardView,
    BlockUserView,

    AdminDashboardView,
)
    
urlpatterns = [
    path('modules/', CreateModuleView.as_view(), name='Modules'),
    path('modules/<uuid:id>/delete/', DeleteModuleView.as_view(), name='Delete Module'),
    path('questions/', CreateQuestionView.as_view(), name='Questions'),

    # profile urls
    path('profile-information/', ProfileInformationView.as_view(), name='Profile Information'),
    path('update-password/', ChangePasswordView.as_view(), name='Update password'),

    # quiz duration
    path('quiz-duration/', CustomTimeListView.as_view(), name='Custom Time List'),
    path('quiz-duration/<uuid:id>/', CustomTimeView.as_view(), name='Custom Time'),

    # student management
    path('student-list/', StudentManageListView.as_view(), name='Student List'),
    path('student-detail/', StudentDashboardView.as_view(), name='student-detail'),
    path('ban-user/', BlockUserView.as_view(), name='Block User'),

    path('dashboard/', AdminDashboardView.as_view(), name='Block User'),
]
