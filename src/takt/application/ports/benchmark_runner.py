"""Runner of benchmarks."""

from pathlib import Path
from typing import Protocol


class BenchmarkRunner(Protocol):
    """Runner of pyperformance and pyperf scripts."""

    def run(self, arguments: tuple[str, ...]) -> Path:
        """Run benchmarks and return the result file.

        :param arguments: Arguments of ``takt run`` without takt flags.
        :returns: Path to the JSON result.
        :raises BenchmarkFailedError: If the process exits with a non-zero code.
        """
