"""Name template that renders to a given run name."""


def literal_template(name: str) -> str:
    """Escape the braces of a run name so that it renders unchanged.

    :param name: Final run name.
    :returns: Template text whose rendering is exactly ``name``.
    """
    return name.replace('{', '{{').replace('}', '}}')
