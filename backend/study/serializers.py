"""DRF serializers for documents and generated study assets."""

from __future__ import annotations

from rest_framework import serializers

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


class SummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Summary
        fields = ["id", "chunk_id", "summary_short", "summary_long", "takeaways"]


class FlashcardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flashcard
        fields = ["id", "chunk_id", "question", "answer"]


class QuizQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizQuestion
        fields = [
            "id",
            "chunk_id",
            "question",
            "type",
            "options",
            "correct_answer",
            "explanation",
        ]


class ConceptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Concept
        fields = ["id", "name", "description"]


class DefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Definition
        fields = ["id", "term", "definition"]


class MindMapSerializer(serializers.ModelSerializer):
    class Meta:
        model = MindMap
        fields = ["data"]


class AudioScriptSerializer(serializers.ModelSerializer):
    class Meta:
        model = AudioScript
        fields = ["content"]


class NotesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notes
        fields = ["id", "topic", "content"]


class DocumentListSerializer(serializers.ModelSerializer):
    """Compact representation used for the documents list view."""

    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = [
            "id",
            "title",
            "status",
            "error",
            "statistics",
            "file_url",
            "created_at",
            "updated_at",
            "processed_at",
        ]

    def get_file_url(self, obj: Document) -> str | None:
        if not obj.file:
            return None
        request = self.context.get("request")
        url = obj.file.url
        return request.build_absolute_uri(url) if request else url


class DocumentDetailSerializer(DocumentListSerializer):
    """Full representation including every generated asset."""

    summaries = SummarySerializer(many=True, read_only=True)
    flashcards = FlashcardSerializer(many=True, read_only=True)
    quiz_questions = QuizQuestionSerializer(many=True, read_only=True)
    concepts = ConceptSerializer(many=True, read_only=True)
    definitions = DefinitionSerializer(many=True, read_only=True)
    notes = NotesSerializer(many=True, read_only=True)
    mindmap = serializers.SerializerMethodField()
    audio_script = serializers.SerializerMethodField()

    class Meta(DocumentListSerializer.Meta):
        fields = DocumentListSerializer.Meta.fields + [
            "summaries",
            "flashcards",
            "quiz_questions",
            "concepts",
            "definitions",
            "notes",
            "mindmap",
            "audio_script",
        ]

    def get_mindmap(self, obj: Document):
        mindmap = MindMap.objects.filter(document=obj).first()
        return mindmap.data if mindmap else None

    def get_audio_script(self, obj: Document):
        audio = AudioScript.objects.filter(document=obj).first()
        return audio.content if audio else None


class DocumentUploadSerializer(serializers.ModelSerializer):
    """Validates and creates a Document from a multipart upload."""

    class Meta:
        model = Document
        fields = ["id", "title", "file"]
        extra_kwargs = {"title": {"required": False, "allow_blank": True}}

    def validate_file(self, value):
        from django.conf import settings

        name = (value.name or "").lower()
        if not name.endswith(".pdf"):
            raise serializers.ValidationError("Only PDF files are accepted.")
        if value.size and value.size > settings.MAX_PDF_UPLOAD_BYTES:
            limit_mb = settings.MAX_PDF_UPLOAD_BYTES // (1024 * 1024)
            raise serializers.ValidationError(
                f"File too large. Maximum size is {limit_mb} MB."
            )
        return value

    def create(self, validated_data):
        if not validated_data.get("title"):
            filename = validated_data["file"].name
            validated_data["title"] = filename.rsplit("/", 1)[-1].rsplit(".", 1)[0]
        return super().create(validated_data)
