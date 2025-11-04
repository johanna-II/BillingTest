"""Performance benchmark tracking and comparison.

This module tracks benchmark results over time and compares against baselines
to detect performance regressions.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest


class BenchmarkTracker:
    """Track and compare benchmark results over time."""

    def __init__(self, results_dir: Path = None):
        """Initialize benchmark tracker.

        Args:
            results_dir: Directory to store benchmark results
        """
        if results_dir is None:
            results_dir = Path(__file__).parent.parent.parent / "benchmarks"

        self.results_dir = results_dir
        self.results_dir.mkdir(exist_ok=True)

        self.history_file = self.results_dir / "history.json"
        self.baseline_file = self.results_dir / "baseline.json"

    def load_history(self) -> List[Dict[str, Any]]:
        """Load benchmark history from file.

        Returns:
            List of historical benchmark results
        """
        if not self.history_file.exists():
            return []

        with open(self.history_file, "r") as f:
            return json.load(f)

    def load_baseline(self) -> Dict[str, Any]:
        """Load baseline benchmark results.

        Returns:
            Baseline benchmark results
        """
        if not self.baseline_file.exists():
            return {}

        with open(self.baseline_file, "r") as f:
            return json.load(f)

    def save_result(
        self, name: str, stats: Dict[str, float], metadata: Dict[str, Any] = None
    ):
        """Save a benchmark result.

        Args:
            name: Benchmark name
            stats: Benchmark statistics (mean, min, max, stddev, etc.)
            metadata: Additional metadata
        """
        history = self.load_history()

        result = {
            "timestamp": datetime.now().isoformat(),
            "name": name,
            "stats": stats,
            "metadata": metadata or {},
        }

        history.append(result)

        with open(self.history_file, "w") as f:
            json.dump(history, f, indent=2)

    def save_baseline(self, name: str, stats: Dict[str, float]):
        """Save a benchmark result as baseline.

        Args:
            name: Benchmark name
            stats: Benchmark statistics
        """
        baseline = self.load_baseline()
        baseline[name] = {
            "timestamp": datetime.now().isoformat(),
            "stats": stats,
        }

        with open(self.baseline_file, "w") as f:
            json.dump(baseline, f, indent=2)

    def compare_with_baseline(
        self, name: str, current_mean: float, threshold: float = 1.5
    ) -> bool:
        """Compare current result with baseline.

        Args:
            name: Benchmark name
            current_mean: Current benchmark mean time
            threshold: Regression threshold (e.g., 1.5 = 50% slower)

        Returns:
            True if performance is acceptable, False if regression detected
        """
        baseline = self.load_baseline()

        if name not in baseline:
            # No baseline, save current as baseline
            self.save_baseline(name, {"mean": current_mean})
            return True

        baseline_mean = baseline[name]["stats"]["mean"]

        if current_mean > baseline_mean * threshold:
            regression_pct = ((current_mean / baseline_mean) - 1) * 100
            print(f"\n⚠️  Performance regression detected for {name}:")
            print(f"  Baseline: {baseline_mean:.6f}s")
            print(f"  Current:  {current_mean:.6f}s")
            print(f"  Regression: {regression_pct:.1f}% slower")
            return False

        improvement_pct = ((baseline_mean / current_mean) - 1) * 100
        if improvement_pct > 10:
            print(
                f"\n✅ Performance improvement for {name}: {improvement_pct:.1f}% faster"
            )

        return True

    def get_trend(self, name: str, window: int = 10) -> Optional[str]:
        """Analyze performance trend for a benchmark.

        Args:
            name: Benchmark name
            window: Number of recent results to analyze

        Returns:
            Trend direction: "improving", "degrading", "stable", or None
        """
        history = self.load_history()

        # Filter results for this benchmark
        results = [r for r in history if r["name"] == name]

        if len(results) < 2:
            return None

        # Get recent results
        recent = results[-window:] if len(results) > window else results

        # Calculate linear trend
        means = [r["stats"]["mean"] for r in recent]
        n = len(means)

        # Simple linear regression
        x_sum = sum(range(n))
        y_sum = sum(means)
        xy_sum = sum(i * y for i, y in enumerate(means))
        xx_sum = sum(i * i for i in range(n))

        slope = (n * xy_sum - x_sum * y_sum) / (n * xx_sum - x_sum * x_sum)

        # Determine trend based on slope
        if abs(slope) < 0.0001:  # Threshold for stable
            return "stable"
        elif slope < 0:
            return "improving"  # Getting faster (lower times)
        else:
            return "degrading"  # Getting slower (higher times)

    def generate_report(self) -> str:
        """Generate a human-readable performance report.

        Returns:
            Performance report as string
        """
        history = self.load_history()
        baseline = self.load_baseline()

        if not history:
            return "No benchmark history found."

        # Group by benchmark name
        benchmarks: Dict[str, List[Dict[str, Any]]] = {}
        for result in history:
            name = result["name"]
            if name not in benchmarks:
                benchmarks[name] = []
            benchmarks[name].append(result)

        report = ["", "=" * 60, "PERFORMANCE BENCHMARK REPORT", "=" * 60, ""]

        for name, results in benchmarks.items():
            report.append(f"\n{name}:")
            report.append("-" * 40)

            # Latest result
            latest = results[-1]
            report.append(f"  Latest:     {latest['stats']['mean']:.6f}s")

            # Baseline comparison
            if name in baseline:
                baseline_mean = baseline[name]["stats"]["mean"]
                diff_pct = ((latest["stats"]["mean"] / baseline_mean) - 1) * 100
                symbol = "📈" if diff_pct > 0 else "📉"
                report.append(
                    f"  Baseline:   {baseline_mean:.6f}s ({symbol} {abs(diff_pct):.1f}%)"
                )

            # Trend
            trend = self.get_trend(name)
            if trend:
                trend_emoji = {"improving": "✅", "degrading": "⚠️", "stable": "➡️"}
                report.append(f"  Trend:      {trend_emoji[trend]} {trend}")

            # Statistics from all runs
            all_means = [r["stats"]["mean"] for r in results]
            report.append(f"  Min:        {min(all_means):.6f}s")
            report.append(f"  Max:        {max(all_means):.6f}s")
            report.append(f"  Runs:       {len(results)}")

        report.append("\n" + "=" * 60)

        return "\n".join(report)


@pytest.fixture(scope="function")
def benchmark_tracker(benchmark):
    """Pytest fixture for benchmark tracking.

    Automatically saves benchmark results and compares with baseline.
    """
    tracker = BenchmarkTracker()

    yield benchmark

    # Save result after benchmark completes
    if hasattr(benchmark, "stats"):
        stats = {
            "mean": benchmark.stats.mean,
            "min": benchmark.stats.min,
            "max": benchmark.stats.max,
            "stddev": benchmark.stats.stddev,
            "median": benchmark.stats.median,
        }

        tracker.save_result(
            name=benchmark.name,
            stats=stats,
            metadata={
                "rounds": benchmark.stats.rounds,
                "iterations": benchmark.stats.iterations,
            },
        )

        # Compare with baseline
        tracker.compare_with_baseline(benchmark.name, benchmark.stats.mean)


def pytest_configure(config):
    """Configure pytest with benchmark tracking."""
    # Add custom markers
    config.addinivalue_line(
        "markers", "benchmark_baseline: mark test as performance baseline"
    )


def pytest_sessionfinish(session):
    """Generate performance report at end of test session."""
    if hasattr(session.config, "getoption"):
        if session.config.getoption("--benchmark-only", default=False):
            tracker = BenchmarkTracker()
            print(tracker.generate_report())
