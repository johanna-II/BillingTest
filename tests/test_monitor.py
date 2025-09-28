"""Test Performance Monitor and Reporter.

This script analyzes test execution times and provides insights
for optimization opportunities.
"""

import json
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


class TestMonitor:
    """Monitor and analyze test performance."""

    def __init__(self):
        self.results_dir = Path("test-results")
        self.results_dir.mkdir(exist_ok=True)

    def run_with_profiling(self, test_path: str = "tests/") -> Dict:
        """Run tests with detailed profiling information."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        durations_file = self.results_dir / f"durations_{timestamp}.json"

        # Run pytest with durations and json report
        cmd = [
            "python",
            "-m",
            "pytest",
            test_path,
            "--durations=50",  # Show 50 slowest tests
            "--durations-min=0.1",  # Only show tests > 0.1s
            f"--json-report-file={durations_file}",
            "--json-report-indent=2",
            "-v",
        ]

        print("Running tests with profiling...")
        result = subprocess.run(cmd, capture_output=True, text=True)

        # Parse the JSON report
        if durations_file.exists():
            with open(durations_file) as f:
                report_data = json.load(f)
            return self._analyze_report(report_data)

        return {}

    def _analyze_report(self, report_data: Dict) -> Dict:
        """Analyze test report and extract insights."""
        analysis: Dict[str, Any] = {
            "summary": {},
            "slow_tests": [],
            "test_categories": defaultdict(list),
            "recommendations": [],
        }

        # Extract summary
        summary = report_data.get("summary", {})
        analysis["summary"] = {
            "total": summary.get("total", 0),
            "passed": summary.get("passed", 0),
            "failed": summary.get("failed", 0),
            "skipped": summary.get("skipped", 0),
            "duration": report_data.get("duration", 0),
        }

        # Analyze individual tests
        tests = report_data.get("tests", [])
        for test in tests:
            duration = test.get("duration", 0)
            nodeid = test.get("nodeid", "")
            outcome = test.get("outcome", "")

            # Categorize by test type
            if "unit" in nodeid:
                category = "unit"
            elif "integration" in nodeid:
                category = "integration"
            elif "contract" in nodeid:
                category = "contract"
            else:
                category = "other"

            test_info = {"nodeid": nodeid, "duration": duration, "outcome": outcome}

            analysis["test_categories"][category].append(test_info)

            # Track slow tests
            if duration > 1.0:  # Tests taking more than 1 second
                analysis["slow_tests"].append(test_info)

        # Sort slow tests by duration
        analysis["slow_tests"].sort(key=lambda x: x["duration"], reverse=True)

        # Generate recommendations
        analysis["recommendations"] = self._generate_recommendations(analysis)

        return analysis

    def _generate_recommendations(self, analysis: Dict) -> List[str]:
        """Generate optimization recommendations based on analysis."""
        recommendations = []

        # Check for slow unit tests
        slow_unit_tests = [t for t in analysis["test_categories"]["unit"] if t["duration"] > 0.5]
        if slow_unit_tests:
            recommendations.append(
                f"⚠️  {len(slow_unit_tests)} unit tests take > 0.5s. "
                "Consider optimizing or moving to integration tests."
            )

        # Check for very slow tests
        very_slow = [t for t in analysis["slow_tests"] if t["duration"] > 5.0]
        if very_slow:
            recommendations.append(
                f"🐌 {len(very_slow)} tests take > 5s. "
                "Consider splitting or optimizing these tests."
            )

        # Check test distribution
        total_tests = analysis["summary"]["total"]
        unit_count = len(analysis["test_categories"]["unit"])
        int_count = len(analysis["test_categories"]["integration"])

        if total_tests > 0:
            unit_ratio = unit_count / total_tests
            if unit_ratio < 0.6:
                recommendations.append(
                    f"📊 Unit test ratio is {unit_ratio:.1%} (target: 70%). "
                    "Consider adding more unit tests."
                )

        # Check overall duration
        total_duration = analysis["summary"]["duration"]
        if total_duration > 300:  # 5 minutes
            recommendations.append(
                f"⏱️  Total test duration is {total_duration:.1f}s. "
                "Consider parallelization or test optimization."
            )

        return recommendations

    def generate_report(self, analysis: Dict) -> None:
        """Generate a detailed performance report."""
        print("\n" + "=" * 80)
        print("📊 TEST PERFORMANCE REPORT")
        print("=" * 80)

        # Summary
        summary = analysis["summary"]
        print("\n📈 Summary:")
        print(f"  Total Tests: {summary['total']}")
        print(f"  Passed: {summary['passed']} ✅")
        print(f"  Failed: {summary['failed']} ❌")
        print(f"  Duration: {summary['duration']:.2f}s")

        # Category breakdown
        print("\n📂 Test Categories:")
        for category, tests in analysis["test_categories"].items():
            if tests:
                total_duration = sum(t["duration"] for t in tests)
                avg_duration = total_duration / len(tests)
                print(f"  {category.capitalize()}:")
                print(f"    Count: {len(tests)}")
                print(f"    Total Duration: {total_duration:.2f}s")
                print(f"    Average Duration: {avg_duration:.3f}s")

        # Slow tests
        if analysis["slow_tests"]:
            print("\n🐌 Slowest Tests (>1s):")
            for i, test in enumerate(analysis["slow_tests"][:10], 1):
                print(f"  {i}. {test['duration']:.2f}s - {test['nodeid']}")

        # Recommendations
        if analysis["recommendations"]:
            print("\n💡 Recommendations:")
            for rec in analysis["recommendations"]:
                print(f"  {rec}")

        print("\n" + "=" * 80)

    def save_historical_data(self, analysis: Dict) -> None:
        """Save analysis data for historical tracking."""
        history_file = self.results_dir / "performance_history.json"

        # Load existing history
        history = []
        if history_file.exists():
            with open(history_file) as f:
                history = json.load(f)

        # Add current data
        history_entry = {
            "timestamp": datetime.now().isoformat(),
            "summary": analysis["summary"],
            "slow_test_count": len(analysis["slow_tests"]),
            "category_counts": {
                cat: len(tests) for cat, tests in analysis["test_categories"].items()
            },
        }
        history.append(history_entry)

        # Keep last 100 entries
        history = history[-100:]

        # Save back
        with open(history_file, "w") as f:
            json.dump(history, f, indent=2)

    def compare_with_baseline(self, current: Dict, baseline_file: str) -> Dict:
        """Compare current performance with a baseline."""
        if not Path(baseline_file).exists():
            print(f"Baseline file {baseline_file} not found")
            return {}

        with open(baseline_file) as f:
            baseline = json.load(f)

        comparison = {
            "duration_change": current["summary"]["duration"] - baseline["summary"]["duration"],
            "new_slow_tests": [],
            "improved_tests": [],
        }

        # Compare individual tests
        current_tests = {
            t["nodeid"]: t["duration"]
            for cat_tests in current["test_categories"].values()
            for t in cat_tests
        }

        baseline_tests = {
            t["nodeid"]: t["duration"]
            for cat_tests in baseline["test_categories"].values()
            for t in cat_tests
        }

        for nodeid, duration in current_tests.items():
            if nodeid in baseline_tests:
                baseline_duration = baseline_tests[nodeid]
                change = duration - baseline_duration

                if change > 0.5:  # Slower by > 0.5s
                    comparison["new_slow_tests"].append(
                        {
                            "nodeid": nodeid,
                            "current": duration,
                            "baseline": baseline_duration,
                            "change": change,
                        }
                    )
                elif change < -0.5:  # Faster by > 0.5s
                    comparison["improved_tests"].append(
                        {
                            "nodeid": nodeid,
                            "current": duration,
                            "baseline": baseline_duration,
                            "change": change,
                        }
                    )

        return comparison


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Monitor test performance")
    parser.add_argument("--path", default="tests/", help="Path to tests to monitor")
    parser.add_argument(
        "--save-baseline", action="store_true", help="Save current results as baseline"
    )
    parser.add_argument("--compare-baseline", help="Compare with baseline file")
    parser.add_argument("--history", action="store_true", help="Show historical trends")

    args = parser.parse_args()

    monitor = TestMonitor()

    # Run tests with profiling
    analysis = monitor.run_with_profiling(args.path)

    if not analysis:
        print("Failed to generate analysis")
        return 1

    # Generate report
    monitor.generate_report(analysis)

    # Save historical data
    monitor.save_historical_data(analysis)

    # Save baseline if requested
    if args.save_baseline:
        baseline_file = monitor.results_dir / "baseline.json"
        with open(baseline_file, "w") as f:
            json.dump(analysis, f, indent=2)
        print(f"\n✅ Baseline saved to {baseline_file}")

    # Compare with baseline if requested
    if args.compare_baseline:
        comparison = monitor.compare_with_baseline(analysis, args.compare_baseline)
        if comparison:
            print("\n📊 Baseline Comparison:")
            print(f"  Duration change: {comparison['duration_change']:+.2f}s")
            if comparison["new_slow_tests"]:
                print(f"  New slow tests: {len(comparison['new_slow_tests'])}")
            if comparison["improved_tests"]:
                print(f"  Improved tests: {len(comparison['improved_tests'])}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
