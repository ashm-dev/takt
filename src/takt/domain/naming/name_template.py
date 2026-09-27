"""Run name template with placeholder substitutions."""

import string
from dataclasses import dataclass
from datetime import UTC
from pathlib import Path
from typing import NoReturn

from takt.domain.errors.invalid_run_name_error import InvalidRunNameError
from takt.domain.naming.name_values import NameValues
from takt.domain.naming.placeholder import Placeholder

_MAX_LENGTH = 255
"""Longest allowed rendered run name in characters."""

_HASH_LENGTH = 12
"""Number of suite hash characters that ``{hash}`` inserts."""

_ALLOWED = ', '.join(f'{{{placeholder}}}' for placeholder in Placeholder)
"""All placeholders, listed in the unknown placeholder error."""

_Field = str | None
"""Field name, format spec or conversion of a template chunk, or ``None``."""

_Chunk = tuple[str, _Field, _Field, _Field]
"""Literal text, field name, format spec and conversion from
``Formatter.parse``."""


@dataclass(frozen=True, kw_only=True)
class NameTemplate:
    """Parsed run name template, ready to render."""

    text: str
    """Template text as the user wrote it."""

    @classmethod
    def parse(cls, text: str) -> NameTemplate:
        """Parse and validate a run name template.

        :param text: Template text, e.g. ``"default {date}"``.
        :returns: A validated template.
        :raises InvalidRunNameError: If the template is malformed.
        """
        if text.strip() == '':
            _fail('run name must not be empty')
        try:
            chunks = list(string.Formatter().parse(text))
        except ValueError:
            _fail(f'invalid name template {text!r}: unbalanced braces')
        offset = 0
        for chunk in chunks:
            offset = _validate_chunk(text, chunk, offset)
        return cls(text=text)

    def render(self, values: NameValues) -> str:
        """Render the template with concrete values.

        :param values: Values available for substitution.
        :returns: The rendered run name.
        :raises InvalidRunNameError: If the rendered name is empty, longer
            than 255 characters, or contains ``:``.
        """
        rendered = _render_text(self.text, _substitutions(values))
        _validate_rendered(rendered)
        return rendered


def _fail(msg: str) -> NoReturn:
    raise InvalidRunNameError(msg) from None


def _validate_chunk(text: str, chunk: _Chunk, offset: int) -> int:
    literal, field, spec, conversion = chunk
    if ':' in literal:
        _fail(f"run name must not contain ':': {text!r}")
    # Formatter.parse turns each doubled brace of the text into one brace.
    offset += len(literal.replace('{', '{{').replace('}', '}}'))
    if field is None:
        return offset
    if field == '':
        _fail(f'invalid name template {text!r}: empty placeholder')
    try:
        Placeholder(field)
    except ValueError:
        _fail(
            f'invalid name template {text!r}: unknown placeholder '
            f'{{{field}}}; allowed: {_ALLOWED}',
        )
    # Formatter.parse gives the same empty spec for {date} and {date:}.
    offset += len(field) + 1
    if spec != '' or conversion is not None or text[offset] == ':':
        _fail(
            f'invalid name template {text!r}: format spec and conversion '
            f'are not allowed in {{{field}}}',
        )
    return offset + 1


def _render_text(
    text: str,
    substitutions: dict[Placeholder, str],
) -> str:
    parts: list[str] = []
    for literal, field, _spec, _conversion in string.Formatter().parse(
        text,
    ):
        parts.append(literal)
        if field is not None:
            parts.append(substitutions[Placeholder(field)])
    return ''.join(parts).strip()


def _substitutions(values: NameValues) -> dict[Placeholder, str]:
    now_utc = values.now.astimezone(UTC)
    return {
        Placeholder.DATE: now_utc.strftime('%Y-%m-%d'),
        Placeholder.DATETIME: now_utc.strftime('%Y-%m-%dT%H-%M-%SZ'),
        Placeholder.PATH: _path_stem(values.result_path),
        Placeholder.PYTHON_VERSION: values.python_version or 'unknown',
        Placeholder.HOSTNAME: values.hostname or 'unknown',
        Placeholder.HASH: values.suite_hash[:_HASH_LENGTH],
    }


def _path_stem(result_path: Path) -> str:
    name = result_path.name
    if name.endswith('.json.gz'):
        return name.removesuffix('.json.gz')
    if name.endswith('.json'):
        return name.removesuffix('.json')
    return result_path.stem


def _validate_rendered(rendered: str) -> None:
    if rendered == '':
        _fail('run name must not be empty')
    if ':' in rendered:
        _fail(f"run name must not contain ':': {rendered!r}")
    if len(rendered) > _MAX_LENGTH:
        _fail(
            f'run name must be at most {_MAX_LENGTH} characters, '
            f'got {len(rendered)}',
        )
