from pathlib import Path

from takt.infrastructure.config.config_sources import ConfigSources

FULL_FILE = """\
name_template = "default {date}"

[targets.local]
url = "sqlite:///bench.sqlite"

[targets.maria_ci]
url = "mariadb+pymysql://user:pass@db.local:3306/bench"
"""


def sources(cwd: Path) -> ConfigSources:
    return ConfigSources(
        db_flags=(),
        target_flags=(),
        config_path=None,
        name_flag=None,
        environ={},
        cwd=cwd,
    )
