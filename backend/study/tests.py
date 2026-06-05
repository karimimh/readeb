from django.test import TestCase

from study.offline import concepts, flashcards, quiz, summarise

SAMPLE = (
    "Photosynthesis is the process by which green plants convert light energy "
    "into chemical energy. Chlorophyll absorbs sunlight in the chloroplast. "
    "The Calvin Cycle fixes carbon dioxide into glucose. Cellular Respiration "
    "then releases this stored energy for the cell to use."
)


class OfflineGeneratorTests(TestCase):
    def test_summarise_has_fields(self):
        result = summarise(1, SAMPLE)
        self.assertEqual(result["chunk_id"], 1)
        self.assertTrue(result["summary_short"])
        self.assertTrue(result["summary_long"])

    def test_flashcards_generated(self):
        result = flashcards(1, SAMPLE)
        self.assertTrue(len(result["flashcards"]) >= 1)
        for card in result["flashcards"]:
            self.assertTrue(card["question"])
            self.assertTrue(card["answer"])

    def test_quiz_types_valid(self):
        result = quiz(1, SAMPLE)
        for q in result["questions"]:
            self.assertIn(q["type"], {"mcq", "true_false", "short_answer"})

    def test_concepts_extracted(self):
        result = concepts(1, SAMPLE)
        self.assertIn("concepts", result)
        self.assertIn("definitions", result)
