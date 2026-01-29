import json
import tempfile
import unittest
from pathlib import Path

from core.dispatch import dispatch


class OpenAICalculateUsageCostTests(unittest.TestCase):
    def test_calculate_usage_cost_with_pricing(self):
        events = [
            {
                "type": "openai_call",
                "ts": "2026-01-29T12:00:00Z",
                "kind": "vision_slide",
                "status": "ok",
                "model": "gpt-4.1",
                "usage": {"input_tokens": 1000, "output_tokens": 100, "total_tokens": 1100},
                "meta": {"frame_path": "/tmp/a.png"},
            },
            {
                "type": "openai_call",
                "ts": "2026-01-29T12:00:01Z",
                "kind": "vision_slide",
                "status": "ok",
                "model": "gpt-4.1",
                "usage": {"input_tokens": 1000, "output_tokens": 100, "total_tokens": 1100},
                "meta": {"frame_path": "/tmp/b.png"},
            },
            {
                "type": "openai_call",
                "ts": "2026-01-29T12:00:02Z",
                "kind": "audio_transcription",
                "status": "ok",
                "model": "whisper-1",
                "usage": None,
                "meta": {"audio_seconds": 300},
            },
            {
                "type": "openai_call",
                "ts": "2026-01-29T12:00:03Z",
                "kind": "audio_transcription",
                "status": "ok",
                "model": "whisper-1",
                "usage": None,
                "meta": {"audio_seconds": 60},
            },
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "openai_usage.jsonl"
            log_path.write_text("\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8")

            payload = {
                "usage_log_path": str(log_path),
                "pricing": {
                    "currency": "USD",
                    "token_models": {"gpt-4.1": {"input_per_1m": 2.0, "output_per_1m": 8.0}},
                    "audio_models": {"whisper-1": {"per_minute": 0.006}},
                },
            }

            res = dispatch("openai.calculate_usage_cost", payload)
            self.assertTrue(res["ok"], res)
            out = res["result"]

            self.assertEqual(out["currency"], "USD")
            self.assertAlmostEqual(out["summary"]["total_audio_minutes"], 6.0, places=6)
            self.assertEqual(out["summary"]["total_input_tokens"], 2000)
            self.assertEqual(out["summary"]["total_output_tokens"], 200)
            self.assertEqual(out["summary"]["total_tokens"], 2200)

            # Token cost: (2000/1e6)*2.0 + (200/1e6)*8.0 = 0.0056
            # Audio cost: (360s/60)*0.006 = 0.036
            # Total = 0.0416
            self.assertAlmostEqual(out["total_cost"], 0.0416, places=6)


if __name__ == "__main__":
    unittest.main()

