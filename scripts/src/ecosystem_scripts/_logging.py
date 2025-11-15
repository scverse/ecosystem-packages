from logging import basicConfig, getLogger

from rich.logging import RichHandler

log = getLogger(__name__)


def setup_logging() -> None:
    """Set up logging and rich traceback."""
    basicConfig(level="INFO", handlers=[RichHandler()])

    # Suppress httpx INFO logs to reduce verbosity
    getLogger("httpx").setLevel("WARNING")
