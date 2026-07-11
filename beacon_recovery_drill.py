#!/usr/bin/env python3
"""Local-first Beacon recovery drill.

This example uses a temporary directory and never contacts a public relay.
Tested with beacon-skill 2.16.1.
"""

import json
import tempfile
from pathlib import Path

from beacon_skill import AgentIdentity, HeartbeatManager
from beacon_skill.codec import decode_envelopes, encode_envelope, verify_envelope
from beacon_skill.goals import GoalManager
from beacon_skill.journal import JournalManager
from beacon_skill.mayday import MaydayManager
from beacon_skill.values import ValuesManager


def require(condition: bool, label: str) -> None:
    """Print a useful result and stop immediately when a check fails."""
    if not condition:
        raise RuntimeError(f"FAIL: {label}")
    print(f"PASS: {label}")


def main() -> None:
    state_dir = Path(tempfile.mkdtemp(prefix="destino_beacon_drill_"))
    worker = AgentIdentity.generate()

    # 1. Emit a local proof-of-life record.
    heartbeats = HeartbeatManager(data_dir=state_dir)
    result = heartbeats.beat(
        worker,
        status="alive",
        health={"queue_depth": 0, "recovery_ready": True},
    )
    heartbeat = result["heartbeat"]
    require(heartbeat["agent_id"] == worker.agent_id, "heartbeat belongs to worker")
    require(heartbeat["status"] == "alive", "worker reports alive")

    # 2. Sign a small checkpoint announcement and verify it before accepting it.
    checkpoint = {
        "kind": "checkpoint",
        "text": "Recovery drill checkpoint is ready",
        "heartbeat_count": heartbeat["beat_count"],
    }
    encoded = encode_envelope(
        checkpoint,
        version=2,
        identity=worker,
        include_pubkey=True,
    )
    decoded = decode_envelopes(encoded)[0]
    require(verify_envelope(decoded), "checkpoint signature verifies")

    # 3. Prepare continuity state. This is data for a controlled handoff, not
    #    permission for another process to spend funds or impersonate the agent.
    goals = GoalManager(data_dir=state_dir)
    values = ValuesManager(data_dir=state_dir)
    journal = JournalManager(data_dir=state_dir)

    goals.dream(
        title="Recover safely",
        description="Restore the worker only after its signed checkpoint is verified.",
        category="connection",
    )
    values.set_principle("verification", 1.0, text="Verify before acting")
    values.add_boundary("Never place a private key or seed phrase in a Mayday bundle")
    journal.write(
        "Local recovery drill completed: heartbeat and signed checkpoint verified.",
        tags=["recovery", "local-test"],
    )

    mayday = MaydayManager(data_dir=state_dir)
    bundle = mayday.build_bundle(
        identity=worker,
        reason="Planned local recovery drill",
        goal_mgr=goals,
        values_mgr=values,
        journal_mgr=journal,
    )
    require(bundle["agent_id"] == worker.agent_id, "Mayday bundle keeps agent identity")
    require(len(json.dumps(bundle)) > 100, "Mayday bundle contains continuity data")

    print(f"agent_id={worker.agent_id}")
    print(f"temporary_state={state_dir}")
    print("DRILL COMPLETE: no public relay or wallet was contacted")


if __name__ == "__main__":
    main()
