import logging


class ConsoleFormatter(logging.Formatter):
    """Human-readable formatter for local development."""

    def __init__(self) -> None:
        super().__init__("%(asctime)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

    COLORS = {
        "DEBUG": "\033[37m",  # gray
        "INFO": "\033[36m",  # cyan
        "WARNING": "\033[33m",  # yellow
        "ERROR": "\033[31m",  # red
        "CRITICAL": "\033[41m",  # red background
    }

    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        if self.usesTime():
            record.asctime = self.formatTime(record, self.datefmt)

        color = self.COLORS.get(record.levelname, "")

        log_msg = " | ".join(
            [
                record.asctime,
                record.levelname.ljust(8),
                record.name,
                record.correlation_id,  # ty: ignore[unresolved-attribute]
                record.getMessage(),
            ]
        )

        return f"{color}{log_msg}{self.RESET}"
