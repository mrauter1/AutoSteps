import logging
import os
import datetime

class Logger:
    _logger = None
    _is_setup = False

    @classmethod
    def setup_logging(cls):
        logger = logging.getLogger("auto_steps")
        if not os.path.exists("logs"):
            os.makedirs("logs")

        log_filename = datetime.datetime.now().strftime("process_%Y%m%d_%H%M%S.log")
        log_file_path = os.path.join("logs", log_filename)

        logger.setLevel(logging.INFO)

        # Clear any existing handlers
        while logger.handlers:
            logger.removeHandler(logger.handlers[0])

        file_handler = logging.FileHandler(log_file_path)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        logger.info("=== New Process Started ===")

        cls._is_setup = True
        cls._logger = logger

    @classmethod
    def get_logger(cls):
        if cls._logger is None:
            if not cls._is_setup:
                cls.setup_logging()
            else:
                cls._logger = logging.getLogger("auto_steps")
        return cls._logger

