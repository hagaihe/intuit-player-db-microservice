import abc
import asyncio
import logging


class AbstractAsyncPlayerDatabase(abc.ABC):
    def __init__(self):
        self._lock = asyncio.Lock()  # lock to handle concurrent read/write access
        self._max_limit = 200  # set a benchmark maximum limit for page size
        self.total_count = 0  # initialize total_count for consistency

    @abc.abstractmethod
    async def load_players(self, *args, **kwargs):
        pass

    @abc.abstractmethod
    async def _get_player_by_id(self, player_id):
        pass

    @abc.abstractmethod
    async def _get_players_paginated(self, start: int, end: int):
        pass

    async def get_player_by_id(self, player_id):
        """Retrieve a player by ID"""
        async with self._lock:
            return await self._get_player_by_id(player_id)

    async def get_players_paginated(self, page: int, limit: int):
        """Generator that yields players in a paginated mechanism"""
        if limit > self._max_limit:
            logging.error(f"Invalid 'limit' value: {limit}. Set to default max: {self._max_limit}.")
            limit = self._max_limit

        max_page = (self.total_count + limit - 1) // limit
        if page < 1 or page > max_page:
            logging.error(f"Invalid 'page' value: {page}. Total pages available: {max_page}.")
            raise ValueError(f"Invalid 'page' value. Must be between 1 and {max_page}.")

        start = (page - 1) * limit
        end = start + limit

        async with self._lock:
            async for player in self._get_players_paginated(start, end):
                yield player
