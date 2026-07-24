import os
import json
from src.telemetry.token_tracker import TokenTracker
from src.telemetry.metrics import SessionMetrics

def test_token_tracker():
    assert TokenTracker.count_tokens("") == 0
    assert TokenTracker.count_tokens("Hello World") > 0
    assert TokenTracker.count_tokens("Hello World") == (len("Hello World") // 4) + 10

def test_session_metrics_logging_and_serialization():
    session_id = "test-telemetry-session"
    metrics = SessionMetrics(session_id)
    
    metrics.log_event("test_event", {"some_key": "some_value"})
    metrics.token_tracker.track_call(100, 50)
    
    metrics.finalize(
        final_status="SUCCESS",
        total_iterations=2,
        total_errors=0,
        critique_scores=[0.9, 1.0],
        model="gemini-2.5-pro"
    )
    
    expected_path = os.path.join(".agent", f"metrics_{session_id}.json")
    assert os.path.exists(expected_path)
    
    with open(expected_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    assert data["session_id"] == session_id
    assert data["final_status"] == "SUCCESS"
    assert data["total_iterations"] == 2
    assert len(data["critique_scores"]) == 2
    assert data["token_report"]["total_calls"] == 1
    assert data["token_report"]["input_tokens"] == 100
    assert data["token_report"]["output_tokens"] == 50
    assert len(data["events"]) == 1
    assert data["events"][0]["event"] == "test_event"
    assert data["events"][0]["some_key"] == "some_value"
    
    # Cleanup
    try:
        os.remove(expected_path)
    except OSError:
        pass
