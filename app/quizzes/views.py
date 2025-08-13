# quizzes/views.py
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from .models import Quiz, QuizChoice, QuizHistory
from terms.models import Term

def dummy_quizzes_view(request):
    
    return render(request, 'quizzes/index.html')


@login_required
@require_http_methods(["GET", "POST"])
def play(request, term_id, qtype="DT"):
    """
    用語に紐づくクイズをプレイするビュー
    qtype: Question Type（デフォルト "DT"）
    """
    term = get_object_or_404(Term, id=term_id)

    # クイズを取得、無ければ作成
    quiz = term.quizzes.filter(question_type=qtype).first()
    if not quiz:
        if hasattr(Quiz, "make_from_term"):
            quiz = Quiz.make_from_term(
                term, created_by=request.user, question_type=qtype, choices=4
            )
        else:
            # フェールセーフ: make_from_termが未実装の場合、簡易生成
            quiz = Quiz.objects.create(
                term=term,
                question_type=qtype,
                question_text=term.word,
                created_by=request.user
            )
            # 誤選択肢を同じ用語帳から取得
            distractors = list(
                Term.objects.filter(vocabulary=term.vocabulary)
                .exclude(id=term.id)
                .values_list("word", flat=True)[:3]
            )
            from random import shuffle
            answers = [term.word] + distractors
            shuffle(answers)
            for i, ans in enumerate(answers, start=1):
                QuizChoice.objects.create(
                    quiz=quiz,
                    text=ans,
                    is_correct=(ans == term.word),
                    order=i
                )

    # POST処理
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
            user=request.user,
            quiz=quiz,
            selected_choice=choice,
            is_correct=choice.is_correct
        )

        request.session["last_result"] = "correct" if choice.is_correct else "wrong"
        return redirect("quizzes:play", term_id=term.id, qtype=qtype)

    # GET時
    last = request.session.pop("last_result", None)
    choices_qs = getattr(quiz, "choices", None) or getattr(quiz, "quizchoice_set", None)

    return render(
        request,
        "quizzes/play.html",
        {
            "quiz": quiz,
            "choices": choices_qs.order_by("order") if hasattr(choices_qs, "order_by") else [],
            "last": last
        }
    )
