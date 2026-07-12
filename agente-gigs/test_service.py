import json
import os
import unittest
from unittest.mock import patch

from service import ServiceError, call_anthropic, normalize_request, proposal_prompt


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


class ProposalServiceTests(unittest.TestCase):
    def job(self):
        return normalize_request(
            {
                "title": "Convert JSON records to CSV",
                "description": "Convert the attached customer records and preserve every field.",
                "platform": "Escrow Marketplace",
                "budget": "$50",
                "skills": ["Python", "data validation"],
                "language": "Spanish",
            }
        )

    def test_rejects_missing_required_fields(self):
        with self.assertRaisesRegex(ServiceError, "title"):
            normalize_request({"description": "work"})

    def test_prompt_forbids_invented_claims(self):
        prompt = proposal_prompt(self.job())
        self.assertIn("Do not invent", prompt)
        self.assertIn("Convert JSON records to CSV", prompt)

    def test_requires_anthropic_key(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ServiceError, "ANTHROPIC_API_KEY"):
                call_anthropic(self.job())

    def test_calls_messages_api_and_returns_draft(self):
        captured = {}

        def opener(request, timeout):
            captured["url"] = request.full_url
            captured["headers"] = dict(request.header_items())
            captured["body"] = json.loads(request.data)
            captured["timeout"] = timeout
            return FakeResponse(
                {
                    "id": "msg_test",
                    "model": "claude-haiku-4-5-20251001",
                    "content": [{"type": "text", "text": "Propuesta verificada"}],
                }
            )

        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-secret", "ANTHROPIC_MODEL": "claude-haiku-4-5"}, clear=True):
            result = call_anthropic(self.job(), opener=opener)

        self.assertEqual(result["proposal"], "Propuesta verificada")
        self.assertFalse(result["submitted"])
        self.assertEqual(captured["body"]["model"], "claude-haiku-4-5")
        self.assertEqual(captured["url"], "https://api.anthropic.com/v1/messages")
        self.assertEqual(captured["timeout"], 45)


if __name__ == "__main__":
    unittest.main()
