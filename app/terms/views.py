# app/terms/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_GET
from .models import Term

# @login_required
@require_GET
def term_list(request):
    qs = (Term.objects
          .select_related("vocabulary")
          .order_by("vocabulary__name", "word"))
    return render(request, "terms/terms.html", {"terms": qs})

# @login_required
@require_GET
def term_detail(request, term_id: int):
    term = get_object_or_404(Term.objects.select_related("vocabulary"), id=term_id)
    return render(request, "terms/term_detail.html", {"term": term})
