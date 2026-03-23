"""
URL configuration for prototype project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from code_evaluation import views
from contests import views
from django.conf import settings
from django.conf.urls.static import static

handler400 = 'code_evaluation.views.error_400'
handler403 = 'code_evaluation.views.error_403'
handler404 = 'code_evaluation.views.error_404'
handler405 = 'code_evaluation.views.error_405'
handler408 = 'code_evaluation.views.error_408'
handler429 = 'code_evaluation.views.error_429'
handler500 = 'code_evaluation.views.error_500'
handler502 = 'code_evaluation.views.error_502'
handler503 = 'code_evaluation.views.error_503'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('code_evaluation.urls')),
    path('contests/', include('contests.urls')),
    path("video-status/", views.video_status, name="video_status"),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
