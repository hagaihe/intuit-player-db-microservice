import unittest
from unittest.mock import patch, mock_open
from app.db_handler import AsyncPlayerDatabase


class TestAsyncPlayerDatabase(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # init the handler
        self.db = AsyncPlayerDatabase()

    @patch('builtins.open', new_callable=mock_open, read_data="playerID,name\np1,Alex\np2,Alexa")
    async def test_load_players(self, mock_file):
        # test loading players from a mocked CSV file
        await self.db.load_players()
        self.assertEqual(self.db.total_count, 2)
        self.assertIn('p1', self.db._index)
        self.assertIn('p2', self.db._index)

    @patch('builtins.open', new_callable=mock_open, read_data="playerID,name\np1,Alex\np2,Alexa")
    async def test_get_player_by_id(self, mock_file):
        # load players from a mocked CSV file
        await self.db.load_players()

        # test retrieving a player by ID
        player = await self.db.get_player_by_id('p1')
        self.assertIsNotNone(player)
        self.assertEqual(player['playerID'], 'p1')

        # test retrieving a non-existent player
        player = await self.db.get_player_by_id('p3')
        self.assertIsNone(player)

    @patch('builtins.open', new_callable=mock_open, read_data="playerID,name\np1,Alex\np2,Alexa\np3,Bob\np4,Alice")
    async def test_get_players(self, mock_file):
        # load players from a mocked CSV file
        await self.db.load_players()

        # test pagination with valid parameters
        players = []
        async for player in self.db.get_players_paginated(page=1, limit=2):
            players.append(player)
        self.assertEqual(len(players), 2)
        self.assertEqual(players[-1]['playerID'], 'p2')

    @patch('builtins.open', new_callable=mock_open, read_data="playerID,name\np1,Alex\np2,Alexa\np3,Bob\np4,Alice")
    async def test_get_players_with_invalid_page_no(self, mock_file):
        # load players from a mocked CSV file
        await self.db.load_players()

        # test pagination with page number exceeding total pages
        with self.assertRaises(ValueError):
            async for _ in self.db.get_players_paginated(page=3, limit=2):
                pass


