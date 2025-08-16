from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),  # 管理画面
    path('dashboard/', include('dashboard.urls')),  # ダッシュボード
    path('terms/', include('terms.urls')),  # 用語一覧
    path('vocabularies/', include('vocabularies.urls')),  # 用語帳一覧
    path('quizzes/', include('quizzes.urls')),  # クイズ
    path("health/", include("health.urls")), # ヘルスチェック
    # path('quizzes/api/dashboard/', include('dashboard.urls')), 
    path('sharing/', include('sharing.urls', namespace='sharing')), # 共有
    path('accounts/', include('accounts.urls', namespace='accounts')), # アカウント
]

