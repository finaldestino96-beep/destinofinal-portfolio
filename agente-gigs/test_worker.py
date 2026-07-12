import json
import tempfile
import unittest
from pathlib import Path

from worker import JobBlocked, run_job


class WorkerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        (self.root / "input").mkdir()
        (self.root / "input/data.json").write_text(
            json.dumps([{"name": "Ada", "tags": ["python"]}, {"name": "Linus", "active": True}]),
            encoding="utf-8",
        )
        self.config = self.root / "config.json"
        self.config.write_text(
            json.dumps({"rules": {"minimum_reward_usd": 5, "require_verified_escrow_before_execution": True}}),
            encoding="utf-8",
        )

    def tearDown(self):
        self.temporary.cleanup()

    def job(self, **changes):
        payload = {
            "job_id": "json-csv-001",
            "task_type": "json_to_csv",
            "reward_usd": 50,
            "approved_by_owner": True,
            "payment": {"escrow_verified": True, "reference": "escrow-demo-123", "verified_by": "owner"},
            "input_path": "input/data.json",
            "output_path": "deliverables/data.csv",
            "evidence_dir": "evidence",
        }
        payload.update(changes)
        path = self.root / "job.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_executes_approved_funded_job_and_writes_evidence(self):
        result = run_job(self.job(), self.config, self.root)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["output"]["rows"], 2)
        self.assertTrue((self.root / "deliverables/data.csv").is_file())
        self.assertTrue((self.root / "evidence/json-csv-001.json").is_file())
        self.assertTrue((self.root / "evidence/json-csv-001-delivery.md").is_file())

    def test_blocks_unfunded_job(self):
        with self.assertRaisesRegex(JobBlocked, "Verified escrow"):
            run_job(self.job(payment={"escrow_verified": False}), self.config, self.root)

    def test_blocks_job_without_owner_approval(self):
        with self.assertRaisesRegex(JobBlocked, "Owner approval"):
            run_job(self.job(approved_by_owner=False), self.config, self.root)

    def test_blocks_low_reward(self):
        with self.assertRaisesRegex(JobBlocked, "below"):
            run_job(self.job(reward_usd=1), self.config, self.root)

    def test_blocks_path_traversal(self):
        with self.assertRaisesRegex(JobBlocked, "escapes"):
            run_job(self.job(output_path="../outside.csv"), self.config, self.root)


if __name__ == "__main__":
    unittest.main()
