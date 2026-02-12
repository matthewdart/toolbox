import unittest

from capabilities.media_analyze_video.implementation import _dedupe_slides


class MediaDedupeTests(unittest.TestCase):
    def test_dedupe_formatting_variation_same_title(self):
        slides = [
            {
                "timestamp": 100.0,
                "title": "Document-Driven: Overview Talking to your Architecture",
                "extracted_text": "Document-Driven: Overview Talking to your Architecture\n• Line one\n• Line two",
                "summary": "a",
                "confidence": 0.9,
                "frame_path": "/tmp/a.png",
            },
            {
                "timestamp": 120.0,
                "title": "Document-Driven: Overview Talking to your Architecture",
                "extracted_text": "Document-Driven: Overview Talking to your Architecture\n- Line one\n- Line two",
                "summary": "b",
                "confidence": 0.9,
                "frame_path": "/tmp/b.png",
            },
        ]

        deduped = _dedupe_slides(slides, window_seconds=180)
        self.assertEqual(len(deduped), 1)

    def test_dedupe_title_mismatch_same_content(self):
        slides = [
            {
                "timestamp": 2400.0,
                "title": "Beware 'Vanity Metrics'",
                "extracted_text": 'Analysis-driven: Best Practice Beware "Vanity Metrics" How many applications do we have?',
                "summary": "a",
                "confidence": 0.9,
                "frame_path": "/tmp/a.png",
            },
            {
                "timestamp": 2430.0,
                "title": "Analysis-driven: Best Practice Beware 'Vanity Metrics'",
                "extracted_text": 'Analysis-driven: Best Practice Beware "Vanity Metrics" How many applications do we have?',
                "summary": "b",
                "confidence": 0.9,
                "frame_path": "/tmp/b.png",
            },
        ]

        deduped = _dedupe_slides(slides, window_seconds=180)
        self.assertEqual(len(deduped), 1)
        self.assertEqual(deduped[0]["title"], "Beware 'Vanity Metrics'")

    def test_dedupe_prefers_cleaner_subset_text(self):
        clean = (
            "Applying generative AI to enterprise architecture processes is a nascent area.\n"
            "There is some guidance.\n"
            "EA teams and vendors are busy experimenting."
        )
        noisy = (
            "Positioning AI for EA\nWhat do the Experts Say?\n"
            + clean
            + "\nCopilot\nYou\nHi. I'm an enterprise architect."
        )
        slides = [
            {
                "timestamp": 810.0,
                "title": "Positioning AI for EA: What do the Experts Say?",
                "extracted_text": noisy,
                "summary": "noisy",
                "confidence": 0.9,
                "frame_path": "/tmp/noisy.png",
            },
            {
                "timestamp": 840.0,
                "title": None,
                "extracted_text": clean,
                "summary": "clean",
                "confidence": 0.9,
                "frame_path": "/tmp/clean.png",
            },
        ]

        deduped = _dedupe_slides(slides, window_seconds=180)
        self.assertEqual(len(deduped), 1)
        self.assertEqual(deduped[0]["title"], "Positioning AI for EA: What do the Experts Say?")
        self.assertEqual(deduped[0]["extracted_text"], clean)


if __name__ == "__main__":
    unittest.main()

