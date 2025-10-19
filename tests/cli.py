#!/usr/bin/env python
"""Test Helper CLI - Convenient commands for running tests.

Usage:
    python -m tests.cli run --type=unit
    python -m tests.cli coverage
    python -m tests.cli report
    python -m tests.cli benchmark
"""

import os
import subprocess
import sys
import webbrowser
from pathlib import Path

import click


@click.group()
@click.version_option(version="1.0.0", prog_name="Test Helper CLI")
def cli():
    """Billing Test Framework - Helper CLI.

    Convenient commands for running tests, generating reports, and more.
    """
    pass


@cli.command()
@click.option(
    "--type",
    type=click.Choice(
        ["unit", "integration", "contracts", "performance", "security", "all"]
    ),
    default="all",
    help="Type of tests to run",
)
@click.option(
    "--parallel", "-n", type=int, default=None, help="Number of parallel workers"
)
@click.option("--mock/--no-mock", default=True, help="Use mock server")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option("--failfast", "-x", is_flag=True, help="Stop on first failure")
@click.option("--keyword", "-k", help="Only run tests matching keyword")
def run(type, parallel, mock, verbose, failfast, keyword):
    """Run tests with smart defaults.

    Examples:
        tests run --type=unit
        tests run --type=integration --parallel=2
        tests run --type=all --failfast
    """
    click.echo(f"🚀 Running {type} tests...")

    # Build pytest command
    cmd = ["pytest"]

    # Test path
    if type == "all":
        cmd.append("tests/")
    else:
        cmd.append(f"tests/{type}/")

    # Options
    if verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")

    if failfast:
        cmd.append("-x")

    if keyword:
        cmd.extend(["-k", keyword])

    # Mock server
    if mock and type in ["integration", "contracts"]:
        cmd.append("--use-mock")

    # Parallel execution
    if parallel is not None:
        cmd.extend(["-n", str(parallel)])
    elif type == "unit":
        cmd.extend(["-n", "auto"])
    elif type == "integration":
        cmd.extend(["-n", "2"])

    # Timeout
    if type in ["integration", "contracts", "performance"]:
        cmd.append("--timeout=300")

    # Run command
    click.echo(f"Command: {' '.join(cmd)}\n")
    result = subprocess.run(cmd)

    if result.returncode == 0:
        click.echo(click.style("\n✅ Tests passed!", fg="green", bold=True))
    else:
        click.echo(click.style("\n❌ Tests failed!", fg="red", bold=True))

    sys.exit(result.returncode)


@cli.command()
@click.option("--open/--no-open", default=True, help="Open report in browser")
@click.option(
    "--format",
    type=click.Choice(["html", "term", "xml"]),
    default="html",
    help="Report format",
)
def coverage(open, format):
    """Generate and view coverage report.

    Examples:
        tests coverage
        tests coverage --no-open
        tests coverage --format=term
    """
    click.echo("📊 Generating coverage report...")

    # Build coverage command
    cmd = ["pytest", "--cov=libs", "--tb=short"]

    if format == "html":
        cmd.append("--cov-report=html")
    elif format == "term":
        cmd.append("--cov-report=term-missing")
    elif format == "xml":
        cmd.append("--cov-report=xml")

    # Run tests with coverage
    result = subprocess.run(cmd)

    if result.returncode == 0:
        click.echo(click.style("✅ Coverage report generated!", fg="green"))

        if open and format == "html":
            report_path = Path("htmlcov/index.html")
            if report_path.exists():
                click.echo(f"Opening {report_path}...")
                webbrowser.open(f"file://{report_path.absolute()}")
            else:
                click.echo(click.style("⚠️  HTML report not found", fg="yellow"))
    else:
        click.echo(click.style("❌ Coverage generation failed", fg="red"))

    sys.exit(result.returncode)


@cli.command()
@click.option("--open/--no-open", default=True, help="Open benchmark report")
def benchmark(open):
    """Run performance benchmarks and view results.

    Examples:
        tests benchmark
        tests benchmark --no-open
    """
    click.echo("⚡ Running performance benchmarks...")

    cmd = [
        "pytest",
        "tests/performance/",
        "--benchmark-only",
        "--benchmark-autosave",
        "-v",
    ]

    result = subprocess.run(cmd)

    if result.returncode == 0:
        click.echo(click.style("✅ Benchmarks complete!", fg="green"))

        # Check for benchmark results
        benchmarks_dir = Path("benchmarks")
        if benchmarks_dir.exists():
            click.echo(f"\nResults saved to: {benchmarks_dir}/")

            # Show recent results
            history_file = benchmarks_dir / "history.json"
            if history_file.exists():
                import json

                with open(history_file) as f:
                    history = json.load(f)
                    if history:
                        click.echo(f"Total runs: {len(history)}")
                        latest = history[-1]
                        click.echo(
                            f"Latest: {latest['name']} - {latest['stats']['mean']:.6f}s"
                        )
    else:
        click.echo(click.style("❌ Benchmarks failed", fg="red"))

    sys.exit(result.returncode)


@cli.command()
@click.option(
    "--type",
    type=click.Choice(["test", "coverage", "benchmark"]),
    default="test",
    help="Report type",
)
def report(type):
    """View various test reports.

    Examples:
        tests report --type=test
        tests report --type=coverage
        tests report --type=benchmark
    """
    if type == "test":
        # Look for JUnit XML reports
        report_dir = Path("report")
        if report_dir.exists():
            junit_xml = report_dir / "junit.xml"
            if junit_xml.exists():
                click.echo(f"Test report: {junit_xml}")
                webbrowser.open(f"file://{junit_xml.absolute()}")
            else:
                click.echo(click.style("⚠️  No test report found", fg="yellow"))
                click.echo("Run tests first: tests run --type=all")
        else:
            click.echo(click.style("⚠️  Report directory not found", fg="yellow"))

    elif type == "coverage":
        report_path = Path("htmlcov/index.html")
        if report_path.exists():
            click.echo(f"Opening coverage report: {report_path}")
            webbrowser.open(f"file://{report_path.absolute()}")
        else:
            click.echo(click.style("⚠️  Coverage report not found", fg="yellow"))
            click.echo("Generate coverage: tests coverage")

    elif type == "benchmark":
        from tests.performance.benchmark_tracking import BenchmarkTracker

        tracker = BenchmarkTracker()
        report_text = tracker.generate_report()
        click.echo(report_text)


@cli.command()
@click.option("--check-only", is_flag=True, help="Only check, don't fix")
def lint(check_only):
    """Lint and format code.

    Examples:
        tests lint
        tests lint --check-only
    """
    click.echo("🔍 Running linters...")

    # Ruff check
    click.echo("\n📝 Ruff:")
    ruff_cmd = ["ruff", "check", "."]
    if not check_only:
        ruff_cmd.append("--fix")

    subprocess.run(ruff_cmd)

    # Black format
    click.echo("\n🎨 Black:")
    black_cmd = ["black", "."]
    if check_only:
        black_cmd.append("--check")

    subprocess.run(black_cmd)

    # MyPy type check
    click.echo("\n🔍 MyPy:")
    subprocess.run(["mypy", "libs", "--ignore-missing-imports"])

    click.echo(click.style("\n✅ Linting complete!", fg="green"))


@cli.command()
def mock():
    """Start mock server for development.

    Examples:
        tests mock
    """
    click.echo("🚀 Starting mock server...")
    click.echo("Access Swagger UI at: http://localhost:5000/docs\n")

    try:
        subprocess.run(["python", "-m", "mock_server.run_server"])
    except KeyboardInterrupt:
        click.echo("\n\n🛑 Mock server stopped")


@cli.command()
def clean():
    """Clean generated files and caches.

    Examples:
        tests clean
    """
    click.echo("🧹 Cleaning generated files...")

    dirs_to_clean = [
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "__pycache__",
        "htmlcov",
        ".coverage",
        "*.pyc",
    ]

    for pattern in dirs_to_clean:
        if "*" in pattern:
            # Pattern matching
            for path in Path(".").rglob(pattern):
                click.echo(f"Removing: {path}")
                path.unlink()
        else:
            # Directory
            for path in Path(".").rglob(pattern):
                if path.is_dir():
                    click.echo(f"Removing: {path}")
                    import shutil

                    shutil.rmtree(path, ignore_errors=True)
                elif path.is_file():
                    path.unlink()

    click.echo(click.style("✅ Cleanup complete!", fg="green"))


@cli.command()
def info():
    """Show environment and configuration info.

    Examples:
        tests info
    """
    import platform

    click.echo("📋 Environment Information")
    click.echo("=" * 50)
    click.echo(f"Python Version: {platform.python_version()}")
    click.echo(f"Platform: {platform.platform()}")
    click.echo(f"Working Directory: {os.getcwd()}")

    # Check for key tools
    tools = ["pytest", "docker", "node"]
    click.echo("\n🔧 Available Tools:")
    for tool in tools:
        result = subprocess.run(["which", tool], capture_output=True, text=True)
        if result.returncode == 0:
            click.echo(click.style(f"  ✅ {tool}: {result.stdout.strip()}", fg="green"))
        else:
            click.echo(click.style(f"  ❌ {tool}: not found", fg="red"))

    # Test configuration
    click.echo("\n⚙️  Test Configuration:")
    click.echo(f"  Mock Server: {os.getenv('USE_MOCK_SERVER', 'not set')}")
    click.echo(f"  Python Path: {sys.executable}")


if __name__ == "__main__":
    cli()
