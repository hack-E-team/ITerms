# app/quizzes/views.py
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from quizzes.models import Quiz, QuizChoice, QuizHistory
from terms.models import Term
from random import shuffle

@login_required
def index(request):
    # 最小のダミー（フロントが一覧を作るまでのプレースホルダ）
    return render(request, "quizzes/index.html")

@login_required
@require_http_methods(["GET", "POST"])
def play(request, term_id, qtype="DT"):
    term = get_object_or_404(Term, id=term_id)

    quiz = term.quizzes.filter(question_type=qtype).first()
    if not quiz:
        if hasattr(Quiz, "make_from_term"):
            quiz = Quiz.make_from_term(term, created_by=request.user,
                                       question_type=qtype, choices=4)
        else:
            quiz = Quiz.objects.create(
                term=term, question_type=qtype, question_text=term.word,
                created_by=request.user
            )
            distractors = list(
                Term.objects.filter(vocabulary=term.vocabulary)
                    .exclude(id=term.id)
                    .values_list("word", flat=True)[:3]
            )
            answers = [term.word] + distractors
            shuffle(answers)
            for i, ans in enumerate(answers, start=1):
                QuizChoice.objects.create(
                    quiz=quiz, text=ans, is_correct=(ans == term.word), order=i
                )

    if request.method == "POST":
        choice_id = request.POST.get("choice_id")
        if not choice_id:
            request.session["last_result"] = "invalid"
            return redirect("quizzes:play", term_id=term.id, qtype=qtype)
        try:
            choice_id = int(choice_id)
        except ValueError:
            request.session["last_result"] = "invalid"
            return redirect("quizzes:play", term_id=term.id, qtype=qtype)

        choice = get_object_or_404(QuizChoice, id=choice_id, quiz=quiz)
        QuizHistory.objects.create(
            user=request.user, quiz=quiz,
            selected_choice=choice, is_correct=choice.is_correct
        )
        request.session["last_result"] = "correct" if choice.is_correct else "wrong"
        return redirect("quizzes:play", term_id=term.id, qtype=qtype)

    choices_qs = getattr(quiz, "choices", None) or getattr(quiz, "quizchoice_set", None)
    last = request.session.pop("last_result", None)
    return render(request, "quizzes/play.html", {
        "quiz": quiz,
        "choices": choices_qs.order_by("order") if hasattr(choices_qs, "order_by") else [],
        "last": last,
    })
