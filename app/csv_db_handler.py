import asyncio
import csv
import logging
import os


class AsyncPlayerDatabase:
    def __init__(self):
        self._data = {}
        self._csv_path = None
        self._lock = asyncio.Lock()  # lock to handle concurrent read/write access
        self.total_count = 0
        self._index = {}  # index mapping playerID to position in file
        self._max_limit = 200  # set a benchmark maximum limit for page size

    async def load_players(self, csv_path='data/players.csv'):
        # resolve the db path relative to the current running point
        self._csv_path = os.path.join(os.path.dirname(__file__), '..', csv_path)
        if not os.path.exists(self._csv_path):
            raise FileNotFoundError(f"source db file '{self._csv_path}' does not exist.")

        # calc the no' of players available in the db
        await self._build_index_and_count()

    async def _build_index_and_count(self):
        """build an index of player IDs to file positions and count total records using a generator."""
        async with self._lock:
            await asyncio.sleep(0)  # yield control to the event loop
            try:
                # Use the generator to build the index and count records in one pass
                async for player_id, position in self._index_generator():
                    self._index[player_id] = position
                    self.total_count += 1
            except Exception as e:
                logging.exception(f"Error while indexing & counting player records: {e}")
                raise e

    async def _index_generator(self):
        """generator to yield player IDs and their positions in the file."""
        try:
            position = 0
            with open(self._csv_path, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    yield row['playerID'], position  # yield the playerID and its position
                    position += 1  # update position after reading the line
        except Exception as e:
            logging.exception(f"Error reading from CSV file: {e}")
            raise e

    async def get_player_by_id(self, player_id):
        """retrieve a player by ID using the index for fast access."""
        async with self._lock:
            if player_id not in self._index:
                return None
            try:
                with open(self._csv_path, newline='') as csvfile:
                    csvfile.seek(self._index[player_id])  # Go directly to the line's position
                    reader = csv.DictReader(csvfile)
                    return next(reader)  # Read the line
            except Exception as e:
                logging.exception(f"Error retrieving player by ID: {e}")
                return None

    async def get_players_paginated(self, page: int, limit: int):
        """generator that yields players in a paginated mechanism using the index"""
        if limit > self._max_limit:
            logging.error(f"Invalid 'limit' value: {limit}. set to default max: {self._max_limit}.")
            limit = self._max_limit

        # calculate the maximum possible page number based on total records and limit
        max_page = (self.total_count + limit - 1) // limit
        if page < 1 or page > max_page:
            logging.error(f"Invalid 'page' value: {page}. Total pages available: {max_page}.")
            raise ValueError(f"Invalid 'page' value. Must be between 1 and {max_page}.")

        start = (page - 1) * limit
        end = start + limit

        # fetch by player IDs from the index within the requested range
        player_ids = list(self._index.keys())[start:end]

        async with self._lock:  # ensure safe concurrent access
            await asyncio.sleep(0)  # yield control to the event loop
            with open(self._csv_path, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for player_id in player_ids:
                    # move to the correct position in the file using the index
                    csvfile.seek(self._index[player_id])
                    yield next(reader)


# AsyncPlayerDatabase instantiation only
players_db = AsyncPlayerDatabase()
