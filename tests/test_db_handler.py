import tempfile
import unittest
from app.csv_db_handler import AsyncPlayerCSVDatabase


class TestAsyncPlayerDatabase(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.db = AsyncPlayerCSVDatabase()

    async def test_load_players(self):
        # load players from a mocked CSV file
        with tempfile.NamedTemporaryFile('w+', delete=False) as tmpfile:
            tmpfile.write("playerID,name\np1,Alex\np2,Alexa")
            tmpfile.flush()  # Ensure the content is written

            await self.db.load_players(tmpfile.name)
            self.assertEqual(self.db.total_count, 2)
            self.assertIn('p1', self.db._index)
            self.assertIn('p2', self.db._index)

    async def test_get_player_by_id(self):
        # load players from a mocked CSV file
        with tempfile.NamedTemporaryFile('w+', delete=False) as tmpfile:
            tmpfile.write("playerID,name\np1,Alex\np2,Alexa")
            tmpfile.flush()  # Ensure the content is written

            await self.db.load_players(tmpfile.name)

            # Fetch player by ID
            player = await self.db.get_player_by_id('p1')
            self.assertIsNotNone(player)
            self.assertEqual(player['playerID'], 'p1')

            # Fetch a non-existent player
            player = await self.db.get_player_by_id('p3')
            self.assertIsNone(player)

    async def test_get_players(self):
        # load players from a mocked CSV file
        with tempfile.NamedTemporaryFile('w+', delete=False) as tmpfile:
            tmpfile.write("playerID,name\np1,Alex\np2,Alexa\np3,Bob\np4,Alice")
            tmpfile.flush()  # Ensure the content is written

            await self.db.load_players(tmpfile.name)

            # test pagination with valid parameters
            players = []
            async for player in self.db.get_players_paginated(page=1, limit=2):
                players.append(player)
            self.assertEqual(len(players), 2)
            self.assertEqual(players[-1]['playerID'], 'p2')

    async def test_get_players_with_invalid_page_no(self):
        # load players from a mocked CSV file
        with tempfile.NamedTemporaryFile('w+', delete=False) as tmpfile:
            tmpfile.write("playerID,name\np1,Alex\np2,Alexa\np3,Bob\np4,Alice")
            tmpfile.flush()  # Ensure the content is written

            await self.db.load_players(tmpfile.name)

            # test pagination with page number exceeding total pages
            with self.assertRaises(ValueError):
                async for _ in self.db.get_players_paginated(page=3, limit=2):
                    pass
