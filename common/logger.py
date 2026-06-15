import os
from datetime import datetime

class LogLevel:
    DEBUG = 0
    INFO = 1
    WARN = 2
    ERROR = 3
    CRIT = 4

class Logger:
    def __init__(self, file=None, loglevel=LogLevel.INFO):
        self.file = file
        self.loglevel = loglevel

    def _message(self, tty_level, file_level, message):
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{date_str}][{tty_level}] {message}")
        if self.file:
            folder = os.path.dirname(self.file)
            if not os.path.exists(folder):
                os.makedirs(folder)
            with open(self.file, "a") as f:
                f.write(f"[{date_str}][{file_level}] {message}\n")

    def debug(self, message):
        if self.loglevel <= LogLevel.DEBUG:
            self._message("DBUG", "DBUG", message)

    def info(self, message):
        if self.loglevel <= LogLevel.INFO:
            self._message("INFO", "INFO", message)

    def warn(self, message):
        if self.loglevel <= LogLevel.WARN:
            self._message("WARN", "WARN", message)

    def error(self, message):
        if self.loglevel <= LogLevel.ERROR:
            self._message("ERR ", "ERR ", message)

    def critical(self, message):
        if self.loglevel <= LogLevel.CRIT:
            self._message("CRIT", "CRIT", message)
