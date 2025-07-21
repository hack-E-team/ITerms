from django.shortcuts import render

def dummy_dashboard_view(request):
    return render(request, 'dashboard/home.html')