"""Database models for uploaded documents and their generated study assets."""

from __future__ import annotations

from django.db import models


class Document(models.Model):
    """An uploaded PDF and the lifecycle of its generated study materials."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    title = models.CharField(max_length=255)
    file = models.FileField(upload_to="pdfs/")
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    error = models.TextField(blank=True, default="")

    # Pipeline statistics (pages, chunks, counts...).
    statistics = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.title} ({self.status})"

    def reset_assets(self) -> None:
        """Delete all previously generated assets before a re-run."""
        self.summaries.all().delete()
        self.flashcards.all().delete()
        self.quiz_questions.all().delete()
        self.concepts.all().delete()
        self.definitions.all().delete()
        self.notes.all().delete()
        MindMap.objects.filter(document=self).delete()
        AudioScript.objects.filter(document=self).delete()


class Summary(models.Model):
    document = models.ForeignKey(
        Document, related_name="summaries", on_delete=models.CASCADE
    )
    chunk_id = models.PositiveIntegerField()
    summary_short = models.TextField(blank=True, default="")
    summary_long = models.TextField(blank=True, default="")
    takeaways = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["chunk_id"]


class Flashcard(models.Model):
    document = models.ForeignKey(
        Document, related_name="flashcards", on_delete=models.CASCADE
    )
    chunk_id = models.PositiveIntegerField()
    question = models.TextField()
    answer = models.TextField()

    class Meta:
        ordering = ["chunk_id", "id"]


class QuizQuestion(models.Model):
    class QType(models.TextChoices):
        MCQ = "mcq", "Multiple choice"
        TRUE_FALSE = "true_false", "True / False"
        SHORT_ANSWER = "short_answer", "Short answer"

    document = models.ForeignKey(
        Document, related_name="quiz_questions", on_delete=models.CASCADE
    )
    chunk_id = models.PositiveIntegerField()
    question = models.TextField()
    type = models.CharField(max_length=20, choices=QType.choices)
    options = models.JSONField(default=list, blank=True)
    correct_answer = models.TextField()
    explanation = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["chunk_id", "id"]


class Concept(models.Model):
    document = models.ForeignKey(
        Document, related_name="concepts", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["name"]


class Definition(models.Model):
    document = models.ForeignKey(
        Document, related_name="definitions", on_delete=models.CASCADE
    )
    term = models.CharField(max_length=255)
    definition = models.TextField()

    class Meta:
        ordering = ["term"]


class MindMap(models.Model):
    document = models.OneToOneField(
        Document, related_name="mindmap", on_delete=models.CASCADE
    )
    data = models.JSONField(default=dict, blank=True)


class AudioScript(models.Model):
    document = models.OneToOneField(
        Document, related_name="audio_script", on_delete=models.CASCADE
    )
    content = models.TextField(blank=True, default="")


class Notes(models.Model):
    document = models.ForeignKey(
        Document, related_name="notes", on_delete=models.CASCADE
    )
    topic = models.CharField(max_length=255)
    content = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["id"]
