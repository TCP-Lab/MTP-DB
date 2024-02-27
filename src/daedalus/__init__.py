import logging
from logging import StreamHandler

from colorama import Back, Fore, Style

__all__ = ["DB_NAME", "SCHEMA"]
# This follows CalVer MAJOR.YEAR.WEEK[.minor][-tag]
__version__ = "1.24.09"


class ColorFormatter(logging.Formatter):
    # Change this dictionary to suit your coloring needs!
    COLORS = {
        "WARNING": Fore.YELLOW,
        "ERROR": Fore.RED,
        "DEBUG": Style.BRIGHT + Fore.MAGENTA,
        "INFO": Fore.GREEN,
        "CRITICAL": Style.BRIGHT + Fore.RED,
    }

    def format(self, record):
        reset = Fore.RESET + Back.RESET + Style.NORMAL
        color = self.COLORS.get(record.levelname, "")
        if color:
            record.name = Style.BRIGHT + Fore.CYAN + record.name + reset
            if record.levelname != "INFO":
                record.msg = color + record.msg + reset
            record.levelname = color + record.levelname + reset
        return logging.Formatter.format(self, record)


# Setup logging
log = logging.getLogger("daedalus")  # Keep this at the module level name
log.setLevel(logging.DEBUG)
log.propagate = False
# Keep this at DEBUG - set levels in handlers themselves

format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
console_formatter = ColorFormatter(format)

stream_h = StreamHandler()
stream_h.setFormatter(console_formatter)
stream_h.setLevel(logging.DEBUG)

log.addHandler(stream_h)
