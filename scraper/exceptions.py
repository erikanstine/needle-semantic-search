from utils.storage import TranscriptKey


class ParserInitializationError(Exception):
    """Raised when the parser cannot initialize from given HTML + context."""

    def __init__(self, message: str, key: TranscriptKey | None = None):
        super().__init__(message)
        self.key = key


class PageFormatNotImplementedException(Exception):
    "Raised when we have not implemented a page format"

    pass
