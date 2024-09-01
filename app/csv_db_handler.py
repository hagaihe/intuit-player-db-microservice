import asyncio
import logging
import os
from app.abstract_db_handler import AbstractAsyncPlayerDatabase


class AsyncPlayerCSVDatabase(AbstractAsyncPlayerDatabase):
    def __init__(self):
        super().__init__()
        self._csv_path = None
        self._index = {}

    async def load_players(self, csv_path='data/players.csv'):
        """Loads players from a CSV file and build an index"""
        self._csv_path = os.path.join(os.path.dirname(__file__), '..', csv_path)
        logging.info(f"build players index from {self._csv_path}")
        if not os.path.exists(self._csv_path):
            raise FileNotFoundError(f"Source db file '{self._csv_path}' does not exist.")
        await self._build_index_and_count()

    async def _build_index_and_count(self):
        """build an index of player IDs to file positions and count total records"""
        async with self._lock:
            await asyncio.sleep(0)  # yield control to the event loop
            try:
                with open(self._csv_path, mode='r', encoding='utf-8') as csvfile:
                    # Read the header and clean each element
                    raw_header = csvfile.readline().strip()
                    self.header = [col.strip() for col in raw_header.split(',')]
                    while True:
                        # store the start position of each line
                        line_start_pos = csvfile.tell()
                        line = csvfile.readline().strip()
                        if not line:  # end of file
                            break
                        row = [value.strip() for value in line.split(',')]
                        player_id = row[self.header.index('playerID')]
                        self._index[player_id] = line_start_pos
                        self.total_count += 1
            except Exception as e:
                logging.exception(f"Error while indexing & counting player records: {e}")
                raise e

    async def _get_player_by_id(self, player_id):
        """retrieve a player by ID using the index for fast access"""
        if player_id not in self._index:
            return None
        try:
            with open(self._csv_path, mode='r', encoding='utf-8') as csvfile:
                # Seek to the position in the file where the record starts
                csvfile.seek(self._index[player_id])
                line = csvfile.readline().strip()
                row = [value.strip() for value in line.split(',')]
                return dict(zip(self.header, row))
        except Exception as e:
            logging.exception(f"Error while fetching player by ID: {e}")
            raise e

    async def _get_players_paginated(self, start: int, end: int):
        """fetch player records within the specified range"""
        try:
            with open(self._csv_path, mode='r', encoding='utf-8') as csvfile:
                # skip the header
                csvfile.readline()

                for i in range(self.total_count):
                    line_start_pos = csvfile.tell()
                    line = csvfile.readline().strip()
                    if start <= i < end:
                        row = [value.strip() for value in line.split(',')]
                        yield dict(zip(self.header, row))  # yield each player record as a dict
                    if i >= end:
                        break
        except Exception as e:
            logging.exception(f"Error retrieving {end - start} players from index {start} to {end}: {e}")
            raise e


players_db = AsyncPlayerCSVDatabase()
