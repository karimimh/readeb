"""API views for uploading documents and retrieving generated study assets."""

from __future__ import annotations

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Document
from .pipeline import process_document_async
from .serializers import (
    AudioScriptSerializer,
    ConceptSerializer,
    DefinitionSerializer,
    DocumentDetailSerializer,
    DocumentListSerializer,
    DocumentUploadSerializer,
    FlashcardSerializer,
    MindMapSerializer,
    NotesSerializer,
    QuizQuestionSerializer,
    SummarySerializer,
)


class DocumentViewSet(viewsets.ModelViewSet):
    """CRUD for documents plus processing trigger and per-asset endpoints."""

    queryset = Document.objects.all()

    def get_serializer_class(self):
        if self.action == "create":
            return DocumentUploadSerializer
        if self.action == "list":
            return DocumentListSerializer
        return DocumentDetailSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        document = serializer.save()
        # Kick off processing immediately in the background.
        process_document_async(document.id)
        document.refresh_from_db()
        output = DocumentDetailSerializer(document, context=self.get_serializer_context())
        return Response(output.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def process(self, request, pk=None):
        """(Re)trigger processing for a document."""
        document = self.get_object()
        if document.status == Document.Status.PROCESSING:
            return Response(
                {"detail": "Document is already being processed."},
                status=status.HTTP_409_CONFLICT,
            )
        document.status = Document.Status.PENDING
        document.error = ""
        document.save(update_fields=["status", "error", "updated_at"])
        process_document_async(document.id)
        return Response({"status": document.status})

    @action(detail=True, methods=["get"])
    def status(self, request, pk=None):
        """Lightweight polling endpoint for processing progress."""
        document = self.get_object()
        return Response(
            {
                "id": document.id,
                "status": document.status,
                "error": document.error,
                "statistics": document.statistics,
            }
        )

    @action(detail=True, methods=["get"])
    def summaries(self, request, pk=None):
        document = self.get_object()
        return Response(SummarySerializer(document.summaries.all(), many=True).data)

    @action(detail=True, methods=["get"])
    def flashcards(self, request, pk=None):
        document = self.get_object()
        return Response(FlashcardSerializer(document.flashcards.all(), many=True).data)

    @action(detail=True, methods=["get"], url_path="quiz")
    def quiz(self, request, pk=None):
        document = self.get_object()
        return Response(
            QuizQuestionSerializer(document.quiz_questions.all(), many=True).data
        )

    @action(detail=True, methods=["get"])
    def concepts(self, request, pk=None):
        document = self.get_object()
        return Response(
            {
                "concepts": ConceptSerializer(document.concepts.all(), many=True).data,
                "definitions": DefinitionSerializer(
                    document.definitions.all(), many=True
                ).data,
            }
        )

    @action(detail=True, methods=["get"])
    def mindmap(self, request, pk=None):
        document = self.get_object()
        mindmap = getattr(document, "mindmap", None)
        return Response(MindMapSerializer(mindmap).data if mindmap else {"data": None})

    @action(detail=True, methods=["get"], url_path="audio")
    def audio(self, request, pk=None):
        document = self.get_object()
        audio = getattr(document, "audio_script", None)
        return Response(
            AudioScriptSerializer(audio).data if audio else {"content": ""}
        )

    @action(detail=True, methods=["get"])
    def notes(self, request, pk=None):
        document = self.get_object()
        return Response(NotesSerializer(document.notes.all(), many=True).data)
