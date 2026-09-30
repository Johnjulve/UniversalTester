"""
Progress events and callback streaming protocol for UniversalTester.
Enables CLI spinners/bars and GUI widgets to receive execution updates in real time.
"""
from dataclasses import dataclass
from typing import Callable, Dict, Any, Optional


@dataclass
class ProgressEvent:
    """Represents a discrete progress or diagnostic notification from the test engine."""
    run_id: str
    step: str
    percent: float = -1.0
    message: str = ""
    level: str = "info"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "step": self.step,
            "percent": self.percent,
            "message": self.message,
            "level": self.level
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProgressEvent":
        return cls(
            run_id=data.get("run_id", ""),
            step=data.get("step", ""),
            percent=float(data.get("percent", -1.0)),
            message=data.get("message", ""),
            level=data.get("level", "info")
        )


EventHandler = Callable[[ProgressEvent], None]
