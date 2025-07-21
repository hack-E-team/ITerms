from django.shortcuts import render

def dummy_terms_view(request):
    return render(request, 'terms/index.html')