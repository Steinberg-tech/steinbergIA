import threading
from collections import defaultdict
from typing import Any

_lock = threading.Lock()
_counters: dict[str, int] = defaultdict(int)
_histograms: dict[str, list[float]] = defaultdict(list)


def increment(metric: str, value: int = 1) -> None:
    with _lock:
        _counters[metric] += value


def record(metric: str, value: float) -> None:
    with _lock:
        _histograms[metric].append(value)


def snapshot() -> dict[str, Any]:
    with _lock:
        hist_summary = {
            k: {
                "count": len(v),
                "avg_ms": round(sum(v) / len(v), 2) if v else 0,
                "min_ms": round(min(v), 2) if v else 0,
                "max_ms": round(max(v), 2) if v else 0,
            }
            for k, v in _histograms.items()
        }
        return {"counters": dict(_counters), "histograms": hist_summary}
