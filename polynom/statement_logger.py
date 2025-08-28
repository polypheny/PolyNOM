import logging
from logging.handlers import RotatingFileHandler
import time
import os
import polynom.config as config
class InfiniteRotatingFileHandler(RotatingFileHandler):
    # RotatingFileHandler that does not delete old logs.
    def doRollover(self):
        if self.stream:
            self.stream.close()
            self.stream = None

        timestamp = time.strftime("%Y%m%d-%H%M%S")
        rollover_filename = f"{self.baseFilename}.{timestamp}"
        if os.path.exists(self.baseFilename):
            os.rename(self.baseFilename, rollover_filename)

        self.mode = "w"
        self.stream = self._open()


# configure global logger instance
logger = logging.getLogger("statement_logger")
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = InfiniteRotatingFileHandler(
        config.get(config.STATEMENT_LOG_FILE_NAME),
        maxBytes=1 * 1024 * 1024 * 1024,  # 1 GB per file
        backupCount=0,
        encoding="utf-8"
    )
    formatter = logging.Formatter("/*%(asctime)s*/ %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
