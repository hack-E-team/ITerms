from django.shortcuts import render

#def dummy_dashboard_view(request):
    #return render(request, 'dashboard/home.html')

from datetime import timedelta
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Case, When, IntegerField
from django.db.models.functions import TruncDate
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_GET

from quizzes.models import QuizHistory
from terms.models import Term
from vocabularies.models import Vocabulary


# --------- helpers ---------
def _as_int(value, default, min_value=None, max_value=None):
    try:
        n = int(value)
    except (TypeError, ValueError):
        return default
    if min_value is not None and n < min_value:
        n = min_value
    if max_value is not None and n > max_value:
        n = max_value
    return n

def _period_qs(user, days):
    """ユーザーの直近days日分の履歴QSを返す（answered_at降順）。"""
    now = timezone.now()
    since = now - timedelta(days=days)
    return (
        QuizHistory.objects
        .filter(user=user, answered_at__gte=since)
        .select_related('quiz', 'quiz__term', 'quiz__term__vocabulary', 'selected_choice')
        .order_by('-answered_at')
    )


# --------- 1) summary ---------
@login_required
@require_GET
def summary(request):
    days = _as_int(request.GET.get('days'), default=30, min_value=1, max_value=365)
    qs = _period_qs(request.user, days)

    # 集計：件数と正解数
    total = qs.count()
    correct = qs.filter(is_correct=True).count()
    accuracy = (correct / total) if total else 0.0

    data = {
        "range_days": days,
        "total_answers": total,
        "correct_answers": correct,
        "accuracy": round(accuracy, 4),
    }
    return JsonResponse(data)


# --------- 2) recent ---------
@login_required
@require_GET
def recent(request):
    days = _as_int(request.GET.get('days'), default=30, min_value=1, max_value=365)
    limit = _as_int(request.GET.get('limit'), default=20, min_value=1, max_value=200)
    offset = _as_int(request.GET.get('offset'), default=0, min_value=0)

    qs = _period_qs(request.user, days)
    items = []
    for h in qs[offset:offset+limit]:
        term = h.quiz.term
        vocab = term.vocabulary if term else None
        items.append({
            "id": h.id,
            "term_id": term.id if term else None,
            "term_word": term.word if term else None,
            "vocabulary_id": vocab.id if vocab else None,
            "vocabulary_name": getattr(vocab, "name", None),
            "question_type": h.quiz.question_type,
            "selected_choice": getattr(h.selected_choice, "text", None),
            "is_correct": bool(h.is_correct),
            "answered_at": h.answered_at.isoformat(),
        })

    return JsonResponse({
        "range_days": days,
        "offset": offset,
        "limit": limit,
        "count": qs.count(),
        "results": items,
    })


# --------- 3) vocabs ---------
@login_required
@require_GET
def vocabs(request):
    days = _as_int(request.GET.get('days'), default=90, min_value=1, max_value=365)
    qs = _period_qs(request.user, days)

    # Vocabulary単位の集計
    agg = (
        qs.values(
            'quiz__term__vocabulary_id',
            'quiz__term__vocabulary__name',
        )
        .annotate(
            answers=Count('id'),
            corrects=Sum(Case(When(is_correct=True, then=1), default=0, output_field=IntegerField())),
        )
        .order_by('-answers')
    )

    rows = []
    for row in agg:
        answers = row['answers']
        corrects = row['corrects'] or 0
        acc = (corrects / answers) if answers else 0.0
        rows.append({
            "vocabulary_id": row['quiz__term__vocabulary_id'],
            "vocabulary_name": row['quiz__term__vocabulary__name'],
            "answers": answers,
            "corrects": corrects,
            "accuracy": round(acc, 4),
        })

    return JsonResponse({
        "range_days": days,
        "vocabs": rows,
    })


# --------- 4) daily ---------
@login_required
@require_GET
def daily(request):
    days = _as_int(request.GET.get('days'), default=30, min_value=1, max_value=365)
    qs = _period_qs(request.user, days)

    daily_agg = (
        qs.annotate(day=TruncDate('answered_at'))
          .values('day')
          .annotate(
              answers=Count('id'),
              corrects=Sum(Case(When(is_correct=True, then=1), default=0, output_field=IntegerField())),
          )
          .order_by('day')
    )

    series = []
    for d in daily_agg:
        answers = d['answers']
        corrects = d['corrects'] or 0
        acc = (corrects / answers) if answers else 0.0
        # 日付はISO形式（YYYY-MM-DD）
        day_str = d['day'].isoformat() if hasattr(d['day'], 'isoformat') else str(d['day'])
        series.append({
            "date": day_str,
            "answers": answers,
            "corrects": corrects,
            "accuracy": round(acc, 4),
        })

    return JsonResponse({
        "range_days": days,
        "series": series,
    })

