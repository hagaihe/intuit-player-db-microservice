
from unittest.mock import patch, AsyncMock
from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase
from app.api import get_all_players, get_player_by_id, health_check
from app.db_handler import players_db


class TestApiHandlers(AioHTTPTestCase):
    async def get_application(self):
        # set up minimal web application with relevant routes for testing
        app = web.Application()
        app.router.add_get('/health', health_check)
        app.router.add_get('/api/players', get_all_players)
        app.router.add_get('/api/players/{playerID}', get_player_by_id)
        return app

    async def test_health_check(self):
        # test the health check endpoint
        resp = await self.client.request('GET', '/health')
        self.assertEqual(resp.status, 200)
        text = await resp.json()
        self.assertEqual(text, {"status": "ok"})

    @patch.object(players_db, 'get_players_paginated')
    async def test_get_all_players(self, mock_paginated):
        # mock the total_count attribute directly
        players_db.total_count = 2

        # define an async generator for the mocked paginated response
        async def mock_paginated_response(*args, **kwargs):
            yield {"playerID": "p1"}
            yield {"playerID": "p2"}

        # set the return value of the mock to the async generator
        mock_paginated.side_effect = mock_paginated_response

        # test fetching all players
        resp = await self.client.request('GET', '/api/players?page=1&limit=2')
        self.assertEqual(resp.status, 200)
        data = await resp.json()
        self.assertEqual(data['total_players'], 2)
        self.assertEqual(len(data['players']), 2)

    @patch.object(players_db, 'get_player_by_id', new_callable=AsyncMock)
    async def test_get_player_by_id(self, mock_get_player):
        # mock a player response
        mock_get_player.return_value = {"playerID": "p1", "name": "Alex"}

        # test fetching player by ID
        resp = await self.client.request('GET', '/api/players/p1')
        self.assertEqual(resp.status, 200)
        data = await resp.json()
        self.assertEqual(data['playerID'], 'p1')

        # Test fetching a non-existent player
        mock_get_player.return_value = None
        resp = await self.client.request('GET', '/api/players/p3')
        self.assertEqual(resp.status, 404)


