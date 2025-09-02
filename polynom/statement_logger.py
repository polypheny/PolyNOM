import logging
from logging.handlers import RotatingFileHandler
import time
import os
import threading
import polynom.config as config

class InfiniteRotatingFileHandler(RotatingFileHandler):
    """RotatingFileHandler that never deletes old log files."""
    def doRollover(self):
        if self.stream:
            self.stream.close()
            self.stream = None

        timestamp = time.strftime("%Y%m%d-%H%M%S")
        rollover_filename = f"{self.baseFilename}.{timestamp}" #self.baseFilename is set by RotatingFileHandler constructor
        if os.path.exists(self.baseFilename):
            os.rename(self.baseFilename, rollover_filename)

        self.mode = "w"
        self.stream = self._open()


class LoggerFactory:
    """Factory to provide per-application loggers."""
    _loggers = {}
    _lock = threading.Lock()

    @classmethod
    def get_logger(cls, app_uuid: str):
        if not app_uuid:
            raise ValueError("app_uuid must be provided")

        with cls._lock:
            if app_uuid not in cls._loggers:
                logger = logging.getLogger(f"statement_logger_{app_uuid}")
                logger.setLevel(logging.INFO)

                log_file = config.get(config.STATEMENT_LOG_FILE_NAME)
                # append UUID to filename
                filename = f"{os.path.splitext(log_file)[0]}_{app_uuid}.log"

                handler = InfiniteRotatingFileHandler(
                    filename,
                    maxBytes=1 * 1024 * 1024 * 1024,
                    backupCount=0,
                    encoding="utf-8"
                )
                formatter = logging.Formatter("/*%(asctime)s*/ %(message)s")
                handler.setFormatter(formatter)
                logger.addHandler(handler)

                cls._loggers[app_uuid] = logger

            return cls._loggers[app_uuid]
