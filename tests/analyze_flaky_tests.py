"""Analyze test results to identify flaky tests.

This script processes multiple test run results to identify tests
that pass/fail inconsistently.
"""

import json
import sys
from collections import defaultdict
from pathlib import Path


class FlakyTestAnalyzer:
    """Analyzes test results to identify flaky tests."""

    def __init__(self):
        self.test_results: dict[str, list[bool]] = defaultdict(list)
        self.test_durations: dict[str, list[float]] = defaultdict(list)
        self.test_failures: dict[str, list[str]] = defaultdict(list)

    def process_report(self, report_path: str) -> None:
        """Process a single test report."""
        with open(report_path) as f:
            data = json.load(f)

        # Process each test
        for test in data.get("tests", []):
            test_id = f"{test['nodeid']}"
            outcome = test["outcome"]
            duration = test.get("duration", 0)

            # Record pass/fail
            self.test_results[test_id].append(outcome == "passed")
            self.test_durations[test_id].append(duration)

            # Record failure reason if failed
            if outcome == "failed":
                failure_msg = test.get("call", {}).get("longrepr", "Unknown failure")
                self.test_failures[test_id].append(str(failure_msg))

    def identify_flaky_tests(self) -> list[tuple[str, float, list[bool]]]:
        """Identify tests that have both passed and failed."""
        flaky_tests = []

        for test_id, results in self.test_results.items():
            if len(set(results)) > 1:  # Has both True and False
                failure_rate = results.count(False) / len(results)
                flaky_tests.append((test_id, failure_rate, results))

        # Sort by failure rate (most flaky first)
        return sorted(flaky_tests, key=lambda x: x[1], reverse=True)

    def identify_slow_tests(
        self, threshold: float = 5.0
    ) -> list[tuple[str, float, float]]:
        """Identify tests that are consistently slow."""
        slow_tests = []

        for test_id, durations in self.test_durations.items():
            if not durations:
                continue

            avg_duration = sum(durations) / len(durations)
            max_duration = max(durations)

            if avg_duration > threshold:
                slow_tests.append((test_id, avg_duration, max_duration))

        return sorted(slow_tests, key=lambda x: x[1], reverse=True)

    def _generate_flaky_tests_section(self, flaky_tests: list) -> list[str]:
        """Generate the flaky tests section of the report."""
        report = ["\n## Flaky Tests\n"]

        if not flaky_tests:
            report.append("No flaky tests detected! 🎉")
            return report

        report.append(f"Found {len(flaky_tests)} flaky tests:\n")
        report.append("| Test | Failure Rate | Pattern | Recent Failures |")
        report.append("|------|-------------|---------|-----------------|")

        for test_id, failure_rate, results in flaky_tests[:10]:  # Top 10
            pattern = "".join(["✓" if r else "✗" for r in results[-10:]])
            failures = self.test_failures[test_id]
            recent_failure = failures[-1][:50] + "..." if failures else "N/A"

            report.append(
                f"| `{test_id}` | {failure_rate:.1%} | {pattern} | {recent_failure} |"
            )

        if len(flaky_tests) > 10:
            report.append(f"\n... and {len(flaky_tests) - 10} more flaky tests")

        return report

    def _generate_slow_tests_section(self, slow_tests: list) -> list[str]:
        """Generate the slow tests section of the report."""
        report = ["\n## Slow Tests\n"]

        if not slow_tests:
            return report

        report.append(f"Found {len(slow_tests)} slow tests (>5s average):\n")
        report.append("| Test | Avg Duration | Max Duration |")
        report.append("|------|--------------|--------------|")

        for test_id, avg_dur, max_dur in slow_tests[:10]:  # Top 10
            report.append(f"| `{test_id}` | {avg_dur:.2f}s | {max_dur:.2f}s |")

        return report

    def _generate_statistics_section(self, flaky_tests: list) -> list[str]:
        """Generate the statistics section of the report."""
        report = ["\n## Test Stability Statistics\n"]

        total_runs = sum(len(results) for results in self.test_results.values())
        total_failures = sum(
            results.count(False) for results in self.test_results.values()
        )
        overall_pass_rate = 1 - (total_failures / total_runs) if total_runs > 0 else 0

        report.append(f"- Total test runs: {total_runs}")
        report.append(f"- Overall pass rate: {overall_pass_rate:.1%}")
        report.append(f"- Number of flaky tests: {len(flaky_tests)}")

        return report

    def _generate_recommendations(
        self, flaky_tests: list, slow_tests: list
    ) -> list[str]:
        """Generate recommendations based on findings."""
        report = ["\n## Recommendations\n"]

        if flaky_tests:
            report.append("### For Flaky Tests:")
            report.append("1. Add retry logic with `@pytest.mark.flaky(reruns=3)`")
            report.append("2. Investigate timing issues and add appropriate waits")
            report.append("3. Check for test isolation issues")
            report.append("4. Review mock/fixture setup and teardown")

        if slow_tests:
            report.append("\n### For Slow Tests:")
            report.append("1. Consider using `@pytest.mark.slow` and skip in CI")
            report.append("2. Optimize test data generation")
            report.append("3. Use test parallelization more effectively")
            report.append("4. Mock expensive operations")

        return report

    def generate_report(self) -> str:
        """Generate a markdown report of findings."""
        flaky_tests = self.identify_flaky_tests()
        slow_tests = self.identify_slow_tests()

        report = ["# Flaky Test Analysis Report\n"]
        report.append(f"Analyzed {len(self.test_results)} unique tests\n")

        # Add sections
        report.extend(self._generate_flaky_tests_section(flaky_tests))
        report.extend(self._generate_slow_tests_section(slow_tests))
        report.extend(self._generate_statistics_section(flaky_tests))
        report.extend(self._generate_recommendations(flaky_tests, slow_tests))

        return "\n".join(report)


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python analyze_flaky_tests.py report-*.json")
        sys.exit(1)

    analyzer = FlakyTestAnalyzer()

    # Process all report files
    for pattern in sys.argv[1:]:
        for report_file in Path().glob(pattern):
            print(f"Processing {report_file}...")
            try:
                analyzer.process_report(str(report_file))
            except Exception as e:
                print(f"Error processing {report_file}: {e}")

    # Generate and output report
    report = analyzer.generate_report()
    print(report)


if __name__ == "__main__":
    main()
