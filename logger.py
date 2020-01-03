import sys
import logging
import logging.handlers

APP_NAME = "wbscan"


class ShortLevelNameFilter(logging.Filter):
    short_names = ('--', '--', 'II', 'WW', 'EE', 'CC')

    def filter(self, record):
        record.shortlevelname = self.short_names[int(record.levelno / 10)]
        return True


def init(level, path, stdout=None):
    lo = logging.getLogger(APP_NAME)
    lo.propagate = True
    lo.setLevel(str_to_level(level))
    log_format = "%(asctime)s.%(msecs)03d - %(name)18s - %(shortlevelname)2s - %(message)s"
    date_format = "%Y-%m-%dT%H:%M:%S"

    if path:
        file_handler = logging.handlers.WatchedFileHandler(path)
        file_handler.addFilter(ShortLevelNameFilter())
        file_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))
        lo.addHandler(file_handler)

    if stdout:
        stdout_handler = logging.StreamHandler(stream=sys.stdout)
        stdout_handler.addFilter(ShortLevelNameFilter())
        stdout_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))
        lo.addHandler(stdout_handler)


def new_sublogger(name):
    logger = logging.getLogger(APP_NAME)
    return logger.getChild(name)


def str_to_level(value):
    if not isinstance(value, str):
        return value

    if str(value).lower() == "critical":
        return logging.CRITICAL
    elif str(value).lower() in ("error", "err"):
        return logging.ERROR
    elif str(value).lower() in ("warning", "warn"):
        return logging.WARNING
    elif str(value).lower() == "info":
        return logging.INFO
    elif str(value).lower() in ("dbg", "debug"):
        return logging.DEBUG
    else:
        return logging.DEBUG
