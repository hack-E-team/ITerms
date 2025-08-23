# app/dashboard/views.py
from datetime import timedelta
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Case, When, IntegerField
from django.db.models.functions import TruncDate
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_GET

from quizzes.models import QuizHistory

# ---- 共通ヘルパ ----
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
    now = timezone.now()
    since = now - timedelta(days=days)
    return (
        QuizHistory.objects
        .filter(user=user, answered_at__gte=since)
        .select_related('quiz', 'quiz__term', 'quiz__term__vocabulary', 'selected_choice')
        .order_by('-answered_at')
    )

# ---- ページ ----
@login_required
@require_GET
def home_page(request):
    days = _as_int(request.GET.get('days'), 30, 1, 365)
    qs = _period_qs(request.user, days)

    total = qs.count()
    correct = qs.filter(is_correct=True).count()
    accuracy = round((correct / total) if total else 0.0, 4)

    # 直近20件
    recent = []
    for h in qs[:20]:
        term = h.quiz.term
        vocab = term.vocabulary if term else None
        recent.append({
            "answered_at": h.answered_at,
            "question_type": h.quiz.question_type,
            "term_word": getattr(term, "word", None),
            "vocabulary_name": getattr(vocab, "name", None),
            "selected_choice": getattr(h.selected_choice, "text", None),
            "is_correct": bool(h.is_correct),
        })

    # 日別
    daily_qs = (
        qs.annotate(day=TruncDate('answered_at'))
          .values('day')
          .annotate(
              answers=Count('id'),
              corrects=Sum(Case(When(is_correct=True, then=1), default=0, output_field=IntegerField())),
          )
          .order_by('day')
    )
    daily = [
        {
            "date": d["day"],
            "answers": d["answers"],
            "corrects": d["corrects"] or 0,
            "accuracy": round(((d["corrects"] or 0) / d["answers"]) if d["answers"] else 0.0, 4),
        }
        for d in daily_qs
    ]

    ctx = {
        "summary": {
            "range_days": days,
            "total_answers": total,
            "correct_answers": correct,
            "accuracy": accuracy,
        },
        "recent": recent,
        "daily": daily,
    }
    return render(request, "dashboard/home.html", ctx)

# ---- API ----
@login_required
@require_GET
def summary(request):
    days = _as_int(request.GET.get('days'), 30, 1, 365)
    qs = _period_qs(request.user, days)
    total = qs.count()
    correct = qs.filter(is_correct=True).count()
    accuracy = (correct / total) if total else 0.0
    return JsonResponse({
        "range_days": days,
        "total_answers": total,
        "correct_answers": correct,
        "accuracy": round(accuracy, 4),
    })

@login_required
@require_GET
def recent(request):
    days = _as_int(request.GET.get('days'), 30, 1, 365)
    limit = _as_int(request.GET.get('limit'), 20, 1, 200)
    offset = _as_int(request.GET.get('offset'), 0, 0)
    qs = _period_qs(request.user, days)
    items = []
    for h in qs[offset:offset+limit]:
        term = h.quiz.term
        vocab = term.vocabulary if term else None
        items.append({
            "id": h.id,
            "term_id": term.id if term else None,
            "term_word": getattr(term, "word", None),
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

@login_required
@require_GET
def vocabs(request):
    days = _as_int(request.GET.get('days'), 90, 1, 365)
    qs = _period_qs(request.user, days)
    agg = (
        qs.values('quiz__term__vocabulary_id', 'quiz__term__vocabulary__name')
          .annotate(
              answers=Count('id'),
              corrects=Sum(Case(When(is_correct=True, then=1), default=0, output_field=IntegerField())),
          )
          .order_by('-answers')
    )
    rows = []
    for r in agg:
        answers = r['answers']
        corrects = r['corrects'] or 0
        rows.append({
            "vocabulary_id": r['quiz__term__vocabulary_id'],
            "vocabulary_name": r['quiz__term__vocabulary__name'],
            "answers": answers,
            "corrects": corrects,
            "accuracy": round((corrects / answers) if answers else 0.0, 4),
        })
    return JsonResponse({"range_days": days, "vocabs": rows})

@login_required
@require_GET
def daily(request):
    days = _as_int(request.GET.get('days'), 30, 1, 365)
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
        series.append({
            "date": d['day'].isoformat() if hasattr(d['day'], 'isoformat') else str(d['day']),
            "answers": answers,
            "corrects": corrects,
            "accuracy": round(acc, 4),
        })
    return JsonResponse({"range_days": days, "series": series})
