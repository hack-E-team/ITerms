from django.shortcuts import render

def dummy_vocabularies_view(request):
    return render(request, 'vocabularies/index.html')

def dummy_vocabularies_search_view(request):
    return render(request, 'vocabulariesSearch/vocabulariesSearch.html')