from django.shortcuts import render

def dummy_terms_view(request):
    return render(request, 'terms/terms.html')

def dummy_create_terms_view(request):
    return render(request, 'createterms/createterms.html')