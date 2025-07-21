from django.shortcuts import render

def dummy_quizzes_view(request):
    return render(request, 'quizzes/index.html')