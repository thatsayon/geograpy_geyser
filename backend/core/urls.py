from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('admin-api/', include('administration.urls')),
    path('auth/', include('authentication.urls')),
    path('module/', include('module.urls')),
    path('student/', include('student.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
