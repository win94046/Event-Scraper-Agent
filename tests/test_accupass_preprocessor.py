import unittest

from scraper.accupass_preprocessor import EVENT_SEPARATOR, preprocess_accupass_text


class AccupassPreprocessorTest(unittest.TestCase):
    def test_keeps_event_like_blocks_and_removes_counts(self):
        raw_text = """
        Login

        2026.07.19 (Sun) 13:30 - 16:30

        Gemini 3.5 + Claude AI workshop

        Online event
        #AI
        890
        21

        2026.07.05 (Sun) 13:30 - 22:00

        Random non matching title

        Taipei
        98
        0
        """

        result = preprocess_accupass_text(raw_text)

        self.assertIn("2026.07.19", result)
        self.assertIn("Gemini 3.5 + Claude AI workshop", result)
        self.assertNotIn("\n890\n", result)
        self.assertNotIn("2026.07.05", result)

    def test_splits_multiple_event_blocks(self):
        raw_text = """
        2026.07.19 13:30 - 16:30
        AI workshop
        #AI

        2026.07.21 14:00 - 16:00
        Python agent meetup
        #Python
        """

        result = preprocess_accupass_text(raw_text)

        self.assertIn(EVENT_SEPARATOR, result)
        self.assertIn("AI workshop", result)
        self.assertIn("Python agent meetup", result)


if __name__ == "__main__":
    unittest.main()
