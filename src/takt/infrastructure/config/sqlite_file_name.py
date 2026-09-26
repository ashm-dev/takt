"""File name that SQLite opens for a SQLite URL."""

from urllib.parse import unquote, urlsplit

from sqlalchemy.engine import URL


def sqlite_file_name(url: URL) -> str:
    """Return the file name that SQLite opens for a SQLite URL.

    :param url: Parsed SQLite URL.
    :returns: The file path, ``:memory:``, or an empty string when the URL
        names no file.
    """
    database = url.database or ''
    # With uri=true SQLite reads a name that starts with file: as a URI.
    if url.query.get('uri') and database.startswith('file:'):
        return unquote(urlsplit(database).path)
    return database
