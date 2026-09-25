from takt.domain.model.measurement_kind import MeasurementKind
from takt.domain.model.suite_source import SuiteSource


def test_measurement_kind_values() -> None:
    assert [kind.value for kind in MeasurementKind] == ['value', 'warmup']


def test_suite_source_values() -> None:
    assert [source.value for source in SuiteSource] == ['run', 'import']
