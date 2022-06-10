import logging
import os
import platform


class Log:
    """Class to configure logging on system"""

    def __init__(self, name: str):
        self.name = name

    def _logging(self) -> logging:
        if os.path.isdir(
            os.path.join(
                os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)),
                "Logs",
            )
        ):
            pass
        else:
            os.mkdir(
                os.path.join(
                    os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)),
                    "Logs",
                )
            )
        log_dir = os.path.join(
            os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)),
            "Logs",
            f"{self.name}.log",
        )
        log_formatter = logging.Formatter(
            "%(asctime)s - %(funcName)s:%(lineno)d - [%(levelname)s] %(message)s"
        )
        rootlogger = logging.getLogger(name="rootlogger")
        if not rootlogger.handlers:
            filehandler = logging.FileHandler(log_dir)
            filehandler.setFormatter(log_formatter)
            rootlogger.addHandler(filehandler)
        else:
            pass
        rootlogger.propagate = False

        rootlogger.setLevel(logging.DEBUG)

        return rootlogger


class StartLog(Log):
    """Class to pass logger method"""

    def __init__(self):
        super().__init__(name=platform.node())
        Log(name=platform.node())

    def start_logging(self) -> logging:
        """Method to call configured logger instance"""
        rootlogger = self._logging()

        return rootlogger
