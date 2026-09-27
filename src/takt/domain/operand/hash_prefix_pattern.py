"""Pattern of a suite hash prefix in a compare operand."""

import re
from typing import Final

HASH_PREFIX_PATTERN: Final[re.Pattern[str]] = re.compile(r'[0-9a-f]{6,64}')
"""Suite hash prefix: 6 to 64 lowercase hex characters."""
