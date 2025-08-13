from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('dashboard/', include('dashboard.urls')),
    path('terms/', include('terms.urls')),
    path('vocabularies/', include('vocabularies.urls')),
    path('quizzes/', include('quizzes.urls')),
    path("health/", include("health.urls")),
    path('quizzes/api/dashboard/', include('dashboard.urls')), 
    path('sharing/', include('sharing.urls', namespace='sharing')),
    path('accounts/', include('accounts.urls', namespace='accounts')),
]

