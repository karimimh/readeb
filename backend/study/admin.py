from django.contrib import admin

from .models import (
    AudioScript,
    Concept,
    Definition,
    Document,
    Flashcard,
    MindMap,
    Notes,
    QuizQuestion,
    Summary,
)


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "status", "created_at", "processed_at")
    list_filter = ("status",)
    search_fields = ("title",)


admin.site.register(
    [Summary, Flashcard, QuizQuestion, Concept, Definition, MindMap, AudioScript, Notes]
)
