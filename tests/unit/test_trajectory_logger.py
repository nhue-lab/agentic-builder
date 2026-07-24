import os
import json
import tempfile
from src.telemetry.trajectory import TrajectoryLogger, TrajectoryStep

def test_trajectory_logger_export():
    steps = [
        TrajectoryStep(
            iteration=1,
            thought="Analyse du besoin",
            action="call_skill",
            skill_name="researcher",
            arguments={"query": "MCP"},
            observation="Résultats MCP",
            success=True,
            timestamp="2026-07-24T22:00:00Z"
        )
    ]

    export_path = TrajectoryLogger.export("test_sess_123", "Test Task", steps, "SUCCESS")
    assert os.path.exists(export_path)

    with open(export_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        assert len(lines) == 2
        meta = json.loads(lines[0])
        step = json.loads(lines[1])
        assert meta["metadata"]["session_id"] == "test_sess_123"
        assert step["step"]["skill_name"] == "researcher"

    # Cleanup
    if os.path.exists(export_path):
        os.remove(export_path)
