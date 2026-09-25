"""Full metadata of one pyperf run."""

import pyperf


def flatten_metadata(run: pyperf.Run) -> dict[str, object]:
    """Return the full metadata of a pyperf run.

    pyperf merges the file, benchmark and run metadata itself, and a key of
    a lower level overrides the same key of a higher level.

    :param run: Run loaded by pyperf.
    :returns: A new dictionary with every metadata key of the run.
    """
    return dict(run.get_metadata())
