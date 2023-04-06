class CacheKeyError(Exception):
    """A ResourceCache was asked a key it does not hold"""

    pass


class Abort(Exception):
    """The program cannot continue, but the error was caught, logged, and we can exit gracefully."""

    pass
