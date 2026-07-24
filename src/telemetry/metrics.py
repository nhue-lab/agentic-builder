import os
import json
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("agentic_builder.telemetry.metrics")

class MetricsTracker:
    def __init__(self):
        self.input_tokens = 0
        self.output_tokens = 0
        self.total_calls = 0

    def track_call(self, input_tokens: int, output_tokens: int):
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.total_calls += 1

    def get_estimated_cost(self, model: str) -> float:
        is_gpt = "gpt" in model.lower()
        input_rate = 5.00 if is_gpt else 1.25
        output_rate = 15.00 if is_gpt else 5.00
        
        cost = (self.input_tokens / 1_000_000) * input_rate + (self.output_tokens / 1_000_000) * output_rate
        return round(cost, 5)

    def get_report(self, model: str) -> dict:
        return {
            "total_calls": self.total_calls,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "estimated_cost_usd": self.get_estimated_cost(model)
        }

class SessionMetrics:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.start_time = datetime.now(timezone.utc).isoformat()
        self.end_time = None
        self.final_status = "UNKNOWN"
        self.total_iterations = 0
        self.total_errors = 0
        self.critique_scores = []
        self.token_tracker = MetricsTracker()
        self.events = []

    def log_event(self, event_name: str, payload: dict[str, Any] = None):
        event = {
            "event": event_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **(payload or {})
        }
        self.events.append(event)
        logger.info(f"[SessionMetrics Event] {event_name}: {payload}")

    def finalize(self, final_status: str, total_iterations: int, total_errors: int, critique_scores: list[float], model: str):
        self.end_time = datetime.now(timezone.utc).isoformat()
        self.final_status = final_status
        self.total_iterations = total_iterations
        self.total_errors = total_errors
        self.critique_scores = critique_scores
        
        start = datetime.fromisoformat(self.start_time)
        end = datetime.fromisoformat(self.end_time)
        duration = (end - start).total_seconds()

        report = {
            "session_id": self.session_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_seconds": round(duration, 2),
            "final_status": self.final_status,
            "total_iterations": self.total_iterations,
            "total_errors": self.total_errors,
            "critique_scores": self.critique_scores,
            "token_report": self.token_tracker.get_report(model),
            "events": self.events
        }

        os_dir = ".agent"
        os.makedirs(os_dir, exist_ok=True)
        file_path = os.path.join(os_dir, f"metrics_{self.session_id}.json")
        
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2)
            logger.info(f"Saved session metrics to {file_path}")
        except Exception as e:
            logger.error(f"Failed to save metrics to file: {str(e)}")

