
# Create your models here.
from django.conf import settings
from django.db import models
import random

class Quiz(models.Model):
    class QuestionType(models.TextChoices):
        DEF_TO_TERM = "DT", "定義→用語名"
        TERM_TO_DEF = "TD", "用語名→定義"

    term = models.ForeignKey("terms.Term", on_delete=models.CASCADE, related_name="quizzes")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    question_type = models.CharField(max_length=2, choices=QuestionType.choices, default=QuestionType.DEF_TO_TERM)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Quiz#{self.id} ({self.get_question_type_display()})"

    # ---- AIなしの選択肢生成（ヘルパーをこの中に持たせる）----
    @staticmethod
    def _pick_distractors(pool_qs, correct_term, k):
        cand = [t for t in pool_qs if t.id != correct_term.id]
        random.shuffle(cand)
        seen, res = set(), []
        c_name = (correct_term.term_name or "").strip().lower()
        for t in cand:
            name = (t.term_name or "").strip().lower()
            if not name or name == c_name or name in seen:
                continue
            seen.add(name)
            res.append(t)
            if len(res) >= k:
                break
        return res[:k]

    @classmethod
    def make_from_term(cls, term, *, created_by=None, question_type="DT", choices=4):
       
        if choices < 2:
            raise ValueError("choices must be >= 2")
        quiz = cls.objects.create(term=term, created_by=created_by, question_type=question_type)

        # 正解文字列 & プール
        if question_type == cls.QuestionType.DEF_TO_TERM:
            correct_text = term.term_name
        else:
            correct_text = (term.description or "")[:255]

        pool = term.__class__.objects.filter(term_book=term.term_book)
        distract_terms = cls._pick_distractors(pool, term, k=choices - 1)
        if len(distract_terms) < choices - 1:
            # 全体から補充
            extra = cls._pick_distractors(term.__class__.objects.all(), term, k=(choices - 1) - len(distract_terms))
            distract_terms.extend(extra)

        items = [QuizChoice(quiz=quiz, text=correct_text, is_correct=True, order=0)]
        for i, t in enumerate(distract_terms, start=1):
            text = t.term_name if question_type == cls.QuestionType.DEF_TO_TERM else (t.description or "")[:255]
            items.append(QuizChoice(quiz=quiz, text=text, is_correct=False, order=i))
        random.shuffle(items)
        for idx, ch in enumerate(items):
            ch.order = idx
        QuizChoice.objects.bulk_create(items)
        return quiz


class QuizChoice(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="choices")
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        unique_together = ("quiz", "order")
        indexes = [models.Index(fields=["quiz", "is_correct"])]

    def __str__(self):
        return f"[{'○' if self.is_correct else '×'}] {self.text}"


class QuizHistory(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="quiz_histories")
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="histories")
    selected_choice = models.ForeignKey(QuizChoice, on_delete=models.SET_NULL, null=True, blank=True)
    is_correct = models.BooleanField()
    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "answered_at"]),
            models.Index(fields=["quiz"]),
        ]

    def __str__(self):
        return f"{self.user_id}-{self.quiz_id}-{'OK' if self.is_correct else 'NG'}"
