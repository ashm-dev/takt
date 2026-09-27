from pathlib import Path

import pyperf

from takt.infrastructure.pyperf.metadata_flattener import flatten_metadata

FULL = Path(__file__).parent / 'fixtures' / 'full.json'
"""pyperf result file in format 1.0 with all metadata filled."""


def test_run_gets_root_and_benchmark_keys() -> None:
    suite = pyperf.BenchmarkSuite.load(str(FULL))
    run = suite.get_benchmark('nbody').get_runs()[1]

    metadata = flatten_metadata(run)

    assert metadata['hostname'] == 'bench-host'
    assert metadata['name'] == 'nbody'
    assert metadata['loops'] == 4
    assert metadata['date'] == '2026-09-25 10:00:02'
    assert metadata['my_label'] == 'baseline'
