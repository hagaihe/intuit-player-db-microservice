import logging


def setup_logger():
    logger = logging.getLogger("PlayerDBMicroservice")
    # logging level can be set from env params
    logger.setLevel(logging.DEBUG)

    # create handlers
    console_handler = logging.StreamHandler()  # console handler
    file_handler = logging.FileHandler("player_db_microservice.log")  # file handler

    # set logging levels for handlers
    console_handler.setLevel(logging.INFO)
    file_handler.setLevel(logging.DEBUG)

    # create formatters and add them to handlers
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # add handlers to the logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


# instantiate the logger
logger = setup_logger()
