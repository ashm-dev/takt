"""Factory of target sessions."""

from typing import Protocol

from takt.application.ports.target_session import TargetSession
from takt.domain.model.target import Target


class TargetConnector(Protocol):
    """Factory of target sessions."""

    def open(self, target: Target) -> TargetSession:
        """Open a session with a started transaction.

        :param target: Target database.
        :returns: Session with an open transaction.
        """
