"""Formatting of a changed-to-base mean ratio."""


def format_normalized_mean(norm_mean: float) -> str:
    """Format the ratio of a changed mean to the base mean.

    :param norm_mean: Changed mean divided by the base mean.
    :returns: ``no change``, ``N.NNx faster`` or ``N.NNx slower``.
    """
    if norm_mean == 1:
        return 'no change'
    if norm_mean < 1:
        speedup = 1 / norm_mean
        return f'{speedup:.2f}x faster'
    return f'{norm_mean:.2f}x slower'
