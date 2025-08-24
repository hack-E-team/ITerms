# app/terms/views.py
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET, require_POST
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q

from .models import Term, Tag

@require_GET
def terms_list_view(request):
    """用語一覧（検索 / タグ絞り込み / ページング）"""
    q = (request.GET.get('q') or '').strip()
    tag = (request.GET.get('tag') or '').strip()  # ← name='tag' は id を受ける想定

    qs = Term.objects.all().prefetch_related('tags').order_by('-updated_at', '-created_at')

    if q:
        qs = qs.filter(
            Q(term__icontains=q) |
            Q(definition__icontains=q) |
            Q(tags__name__icontains=q)
        ).distinct()

    current_tag_id = None
    if tag.isdigit():  # ← IDで統一
        current_tag_id = int(tag)
        qs = qs.filter(tags__id=current_tag_id).distinct()

    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'terms/terms.html', {
        'page_obj': page_obj,
        'q': q,
        'current_tag_id': current_tag_id,        # ← name変更
        'all_tags': Tag.objects.order_by('name'),
    })

# @login_required
@require_GET
def term_create_view(request):
    """用語作成ページ（表示のみ）"""
    return render(request, 'createterms/createterms.html', {
        'values': {'term': '', 'definition': '', 'tags': []},  # ← tag_names削除
        'errors': {},
        'all_tags': Tag.objects.order_by('name'),
    })

# @login_required
@require_POST
@transaction.atomic
def term_create_post(request):
    """用語作成処理（POST専用。新規タグは作らない）"""
    term = (request.POST.get('term') or '').strip()
    definition = (request.POST.get('definition') or '').strip()
    tag_ids = request.POST.getlist('tags')  # 既存タグID（複数）

    errors = {}
    if not term:
        errors['term'] = '必須です。'
    if not definition:
        errors['definition'] = '必須です。'

    # 数値のみに限定
    valid_tag_ids = [int(x) for x in tag_ids if x.isdigit()]

    if errors:
        return render(request, 'createterms/createterms.html', {
            'values': {'term': term, 'definition': definition, 'tags': valid_tag_ids},
            'errors': errors,
            'all_tags': Tag.objects.order_by('name'),
        }, status=400)

    obj = Term.objects.create(term=term, definition=definition)

    # 既存タグのみ紐付け（存在しないIDは無視）
    if valid_tag_ids:
        selected = list(Tag.objects.filter(id__in=set(valid_tag_ids)))
        if selected:
            obj.tags.add(*selected)

    messages.success(request, f'用語「{obj.term}」を作成しました。')
    return redirect('terms:list')

@require_GET
def terms_learn_view(request):
    """フラッシュカード画面"""
    return render(request, "terms/learn.html")

@require_GET
def terms_api_flashcards(request):
    """フラッシュカード用の用語JSON（?q=, ?tag=<id> に対応）"""
    q = (request.GET.get("q") or "").strip()
    tag = (request.GET.get("tag") or "").strip()

    qs = Term.objects.all().prefetch_related("tags").order_by("-updated_at", "-created_at")

    if q:
        qs = qs.filter(
            Q(term__icontains=q) |
            Q(definition__icontains=q) |
            Q(tags__name__icontains=q)
        ).distinct()

    if tag.isdigit():
        qs = qs.filter(tags__id=int(tag)).distinct()

    data = [
        {
            "id": t.id,
            "term": t.term,
            "definition": t.definition,
            "tags": [tg.name for tg in t.tags.all()],
            "updated_at": t.updated_at.isoformat(),
        }
        for t in qs
    ]
    return JsonResponse({"items": data})
