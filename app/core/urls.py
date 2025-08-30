# app/core/urls.py
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),

    # 各アプリ
    path('accounts/', include('accounts.urls')),          # app_name="accounts"
    path('dashboard/', include('dashboard.urls')),        # app_name="dashboard"
    path('terms/', include('terms.urls')),                # app_name="terms"
    path('vocabularies/', include('vocabularies.urls')),  # app_name="vocabularies"
    path('quizzes/', include('quizzes.urls')),            # app_name="quizzes"
    path('sharing/', include('sharing.urls')),            # app_name="sharing"
    path("", RedirectView.as_view(pattern_name="accounts:login", permanent=False)),
]

