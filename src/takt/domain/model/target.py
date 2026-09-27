"""Database where takt stores results."""

from dataclasses import dataclass

from sqlalchemy.engine import make_url


@dataclass(frozen=True, kw_only=True)
class Target:
    """Database where takt stores results."""

    name: str | None
    """Target name from ``takt.toml`` or ``None``."""

    url: str
    """SQLAlchemy URL as the user wrote it."""

    dialect: str
    """Supported dialect name."""

    def display(self) -> str:
        """Return a label that is safe to print.

        :returns: The target name, or the URL with a hidden password.
        """
        if self.name is not None:
            return self.name
        return make_url(self.url).render_as_string(hide_password=True)
