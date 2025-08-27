# Register your models here.
from django.contrib import admin
from .models import Quiz, QuizChoice, QuizHistory

class QuizChoiceInline(admin.TabularInline):
    model = QuizChoice
    extra = 0

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ("id", "term", "question_type", "created_by", "created_at")
    list_filter = ("question_type",)
    inlines = [QuizChoiceInline]

@admin.register(QuizHistory)
class QuizHistoryAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "quiz", "is_correct", "answered_at")
    list_filter = ("is_correct",)
