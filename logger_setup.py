import logging


def setup_logger(logging_level):
    logging.basicConfig(
        level=logging_level,
        format='%(asctime)s - %(levelname)s - %(message)s - %(filename)s:%(lineno)d',
        handlers=[
            logging.StreamHandler()
        ]
    )
