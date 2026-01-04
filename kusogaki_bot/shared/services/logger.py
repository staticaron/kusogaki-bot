import logging


class KusoLogFormatter(logging.Formatter):
    grey = '\x1b[38;20m'
    yellow = '\x1b[33;20m'
    red = '\x1b[31;20m'
    bold_red = '\x1b[31;1m'
    reset = '\x1b[0m'

    custom_format = (
        '%(asctime)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)'
    )

    FORMATS = {
        logging.DEBUG: grey + custom_format + reset,
        logging.INFO: grey + custom_format + reset,
        logging.WARNING: yellow + custom_format + reset,
        logging.ERROR: red + custom_format + reset,
        logging.CRITICAL: bold_red + custom_format + reset,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


logger = logging.Logger('KusoLogger')
logger.setLevel(logging.DEBUG)

handler = logging.StreamHandler()
handler.setFormatter(KusoLogFormatter())

logger.addHandler(handler)
