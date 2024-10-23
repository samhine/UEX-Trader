import logging

def setup_logger(logging_level=logging.INFO):
    # Configure the root logger
    logging.basicConfig(
        format='%(asctime)s - %(levelname)s - %(message)s - %(filename)s:%(lineno)d',
        level=logging_level
    )
    # Get the logger for the current module
    logger = logging.getLogger(__name__)
    logger.setLevel(logging_level)
    return logger
