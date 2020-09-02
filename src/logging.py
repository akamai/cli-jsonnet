import logging

_console_formatter = logging.Formatter("%(message)s")

_console_handler = logging.StreamHandler()
_console_handler.setFormatter(_console_formatter)

logger = logging.getLogger()

logger.addHandler(_console_handler)
# Set Log Level to DEBUG, INFO, WARNING, ERROR, CRITICAL
logger.setLevel(logging.INFO)