import logging
import os


class Log:
    def __init__(self, name: str):
        self.name = name

    def logging(self) -> logging:
        log_dir = os.path.join('var', 'log', f'{self.name}.log')

        log_formatter = logging.Formatter("%(asctime)s - %(funcName)s:%(lineno)d - [%(levelname)s] %(message)s")
        rootlogger = logging.getLogger()

        filehandler = logging.FileHandler(log_dir)
        filehandler.setFormatter(log_formatter)
        rootlogger.addHandler(filehandler)

        rootlogger.setLevel(logging.DEBUG)

        return rootlogger
