from django.shortcuts import render

def dummy_login_view(request):
    return render(request, 'accounts/login.html')