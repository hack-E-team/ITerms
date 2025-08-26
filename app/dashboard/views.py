# app/dashboard/views.py
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET
from django.shortcuts import render

@login_required
@require_GET
def home_view(request):
    """ダッシュボード画面"""
    return render(request, "dashboard/home.html")