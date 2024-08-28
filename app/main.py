import logging

from aiohttp import web
from app.routes import setup_routes
from app.db_handler import players_db


async def init_app():
    app = web.Application()

    # Configure the global logger
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),  # Logs to console
            logging.FileHandler("player_db_microservice.log")  # Logs to a file
        ]
    )
    logger = logging.getLogger("PlayerDBMicroservice")
    logger.info("Logger initialized.")

    # load the players data to memory
    try:
        await players_db.load_players('data/players.csv')
    except Exception as e:
        logger.critical(f"Failed to load players data: {e}")
        raise SystemExit(1)

    # verify we have successfully managed to load players to memory
    if players_db.total_count > 0:
        logger.info(f"{players_db.total_count} players exists in source csv file.")
    else:
        logger.critical("Error: players db is empty. Service is aborted.")
        raise SystemExit(1)

    # setup routes only after data is loaded
    setup_routes(app)

    return app


def main():
    app = init_app()
    web.run_app(app, host='0.0.0.0', port=8080)


if __name__ == '__main__':
    main()
