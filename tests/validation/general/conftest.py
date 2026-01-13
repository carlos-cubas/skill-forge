"""
Shared fixtures for general validation tests.

This module provides fixtures used across general validation tests,
particularly for CLI performance benchmarking.
"""

import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

import pytest


@dataclass
class BenchmarkResult:
    """Result of a benchmark measurement."""

    command: str
    elapsed_ms: float
    stdout: str
    stderr: str
    return_code: int
    iteration: int
    is_warm: bool

    @property
    def success(self) -> bool:
        """Whether the command succeeded."""
        return self.return_code == 0


@dataclass
class BenchmarkSummary:
    """Summary statistics for a benchmark run."""

    command: str
    iterations: int
    min_ms: float
    max_ms: float
    avg_ms: float
    median_ms: float
    cold_start_ms: Optional[float]
    warm_avg_ms: Optional[float]
    all_results: list[BenchmarkResult]

    def meets_threshold(self, threshold_ms: float, use_warm: bool = False) -> bool:
        """Check if the benchmark meets the given threshold."""
        if use_warm and self.warm_avg_ms is not None:
            return self.warm_avg_ms <= threshold_ms
        return self.avg_ms <= threshold_ms


class CLIBenchmark:
    """
    Utility class for benchmarking CLI command execution time.

    This class provides methods to measure the execution time of CLI commands,
    distinguishing between cold starts (first run) and warm starts (subsequent runs).

    Usage:
        benchmark = CLIBenchmark()
        result = benchmark.run("skillforge --version")
        summary = benchmark.run_multiple("skillforge read test-skill", iterations=5)
    """

    def __init__(
        self,
        shell: bool = True,
        cwd: Optional[Path] = None,
        env: Optional[dict] = None,
    ):
        """
        Initialize the benchmark utility.

        Args:
            shell: Whether to run commands through shell
            cwd: Working directory for commands
            env: Environment variables to set
        """
        self.shell = shell
        self.cwd = cwd or Path.cwd()
        self.env = env or os.environ.copy()

    def run(
        self,
        command: str,
        iteration: int = 0,
        is_warm: bool = False,
    ) -> BenchmarkResult:
        """
        Run a single benchmark measurement.

        Args:
            command: The CLI command to run
            iteration: The iteration number (for tracking)
            is_warm: Whether this is considered a warm start

        Returns:
            BenchmarkResult with timing and output information
        """
        start_time = time.perf_counter()

        try:
            result = subprocess.run(
                command,
                shell=self.shell,
                capture_output=True,
                text=True,
                cwd=self.cwd,
                env=self.env,
                timeout=30,  # 30 second timeout
            )
            elapsed_ms = (time.perf_counter() - start_time) * 1000

            return BenchmarkResult(
                command=command,
                elapsed_ms=elapsed_ms,
                stdout=result.stdout,
                stderr=result.stderr,
                return_code=result.returncode,
                iteration=iteration,
                is_warm=is_warm,
            )
        except subprocess.TimeoutExpired:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            return BenchmarkResult(
                command=command,
                elapsed_ms=elapsed_ms,
                stdout="",
                stderr="Command timed out after 30 seconds",
                return_code=-1,
                iteration=iteration,
                is_warm=is_warm,
            )

    def run_multiple(
        self,
        command: str,
        iterations: int = 5,
        warmup_runs: int = 1,
    ) -> BenchmarkSummary:
        """
        Run multiple benchmark iterations and compute statistics.

        Args:
            command: The CLI command to run
            iterations: Total number of iterations (including warmup)
            warmup_runs: Number of initial runs to consider as warmup

        Returns:
            BenchmarkSummary with statistics across all runs
        """
        results: list[BenchmarkResult] = []

        for i in range(iterations):
            is_warm = i >= warmup_runs
            result = self.run(command, iteration=i, is_warm=is_warm)
            results.append(result)

        # Calculate statistics
        all_times = [r.elapsed_ms for r in results]
        warm_times = [r.elapsed_ms for r in results if r.is_warm]

        sorted_times = sorted(all_times)
        median_idx = len(sorted_times) // 2
        median_ms = (
            sorted_times[median_idx]
            if len(sorted_times) % 2 == 1
            else (sorted_times[median_idx - 1] + sorted_times[median_idx]) / 2
        )

        return BenchmarkSummary(
            command=command,
            iterations=iterations,
            min_ms=min(all_times),
            max_ms=max(all_times),
            avg_ms=sum(all_times) / len(all_times),
            median_ms=median_ms,
            cold_start_ms=results[0].elapsed_ms if results else None,
            warm_avg_ms=(sum(warm_times) / len(warm_times)) if warm_times else None,
            all_results=results,
        )


@pytest.fixture
def cli_benchmark() -> CLIBenchmark:
    """Provide a CLIBenchmark instance for tests."""
    return CLIBenchmark()


@pytest.fixture
def project_root() -> Path:
    """Return the project root directory."""
    # Navigate up from tests/validation/general to project root
    return Path(__file__).parent.parent.parent.parent


@pytest.fixture
def fixtures_dir() -> Path:
    """Return the fixtures directory path."""
    return Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def test_skill_path(fixtures_dir: Path) -> Path:
    """Return the path to the test skill fixture."""
    return fixtures_dir / "test-skill.md"


# Performance thresholds (in milliseconds)
# These are the acceptance criteria for CLI performance
COLD_START_THRESHOLD_MS = 500  # First run should be < 500ms
WARM_START_THRESHOLD_MS = 200  # Subsequent runs should be < 200ms
READ_COMMAND_THRESHOLD_MS = 300  # Read + parse + output should be < 300ms


@pytest.fixture
def cold_start_threshold() -> float:
    """Return the cold start performance threshold in milliseconds."""
    return COLD_START_THRESHOLD_MS


@pytest.fixture
def warm_start_threshold() -> float:
    """Return the warm start performance threshold in milliseconds."""
    return WARM_START_THRESHOLD_MS


@pytest.fixture
def read_command_threshold() -> float:
    """Return the read command performance threshold in milliseconds."""
    return READ_COMMAND_THRESHOLD_MS
