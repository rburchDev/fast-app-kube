import logging
import os


class Log:
    def __init__(self, name: str):
        self.name = name

    def logging(self) -> logging:
        if os.path.isdir(os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)), 'Logs')):
            pass
        else:
            os.mkdir(os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)), 'Logs'))
        log_dir = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)),
                               'Logs', f'{self.name}.log')
        log_formatter = logging.Formatter("%(asctime)s - %(funcName)s:%(lineno)d - [%(levelname)s] %(message)s")
        rootlogger = logging.getLogger()

        filehandler = logging.FileHandler(log_dir)
        filehandler.setFormatter(log_formatter)
        rootlogger.addHandler(filehandler)

        rootlogger.setLevel(logging.DEBUG)

        return rootlogger
