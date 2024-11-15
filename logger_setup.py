import logging


def setup_logger(logging_level):
    # TODO - Find a way to ensure a new call to "setup_logger" is erasing the current logging configuration
    logging.basicConfig(
        level=logging_level,
        format='%(asctime)s - %(levelname)s - %(message)s - %(filename)s:%(lineno)d',
        handlers=[
            logging.StreamHandler()
        ]
    )
