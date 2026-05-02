"""Lightweight in-process metrics registry."""

from collections import Counter
from threading import Lock


class MetricsRegistry:
    """Minimal metrics collector for counters and latency aggregates."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._counters: Counter[str] = Counter()
        self._timings: dict[str, list[float]] = {}

    def increment(self, metric_name: str, value: int = 1) -> None:
        """Increment a counter metric."""
        with self._lock:
            self._counters[metric_name] += value

    def observe(self, metric_name: str, value: float) -> None:
        """Record a timing or numeric observation."""
        with self._lock:
            samples = self._timings.setdefault(metric_name, [])
            samples.append(value)

    def snapshot(self) -> dict[str, object]:
        """Return a serializable snapshot of current metrics."""
        with self._lock:
            timings = {
                metric_name: {
                    "count": len(samples),
                    "avg": round(sum(samples) / len(samples), 2)
                    if samples
                    else 0.0,
                }
                for metric_name, samples in self._timings.items()
            }
            return {
                "counters": dict(self._counters),
                "timings": timings,
            }


metrics_registry = MetricsRegistry()
