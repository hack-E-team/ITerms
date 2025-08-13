from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('accounts.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('terms/', include('terms.urls')),
    path('vocabularies/', include('vocabularies.urls')),
    path('quizzes/', include('quizzes.urls')),
 #   path('accounts/', include('accounts.urls', namespace='accounts')),
]
