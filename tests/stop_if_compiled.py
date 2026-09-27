"""Guard against mypyc build output left in the package sources."""

import shlex
import sys
from pathlib import Path

_EXIT_CODE = 2
"""Exit code when compiled modules are found."""


def stop_if_compiled(package_root: Path) -> None:
    """Stop the test run when compiled modules sit next to the sources.

    Python imports a ``.so`` module before the ``.py`` file with the same
    name, so tests would run stale compiled code instead of the sources.
    It calls :func:`sys.exit` because pytest reports ``pytest.exit``
    from a conftest import as an import error.

    :param package_root: Directory with the package sources.
    :raises SystemExit: With code 2 when ``package_root`` has ``.so`` files.
    """
    if any(package_root.rglob('*.so')):
        quoted_root = shlex.quote(str(package_root))
        sys.stderr.write(
            f'compiled modules found in {package_root}, remove them with: '
            f"find {quoted_root} -name '*.so' -delete\n",
        )
        sys.exit(_EXIT_CODE)
