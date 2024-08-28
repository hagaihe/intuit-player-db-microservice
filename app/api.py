
from aiohttp import web

from app.db_handler import players_db


async def health_check(request):
    """simple health check endpoint to verify service status."""
    return web.json_response({"status": "ok"})


async def get_all_players(request):
    """handler to fetch paginated player data"""
    try:
        # extract pagination parameters or use default if they are not exists
        # default params can be loaded from env params when service is starting
        page = int(request.query.get('page', 1))
        limit = int(request.query.get('limit', 100))

        # validate parameters
        if page < 1 or limit < 1:
            return web.json_response({'error': 'Page and limit must be greater than 0'}, status=400)

        # fetch paginated players
        players = []
        async for player in players_db.get_players_paginated(page, limit):
            players.append(player)

        # build response with pagination metadata
        response = {
            'total_players': players_db.total_count,
            'page': page,
            'limit': limit,
            'players': players
        }
        return web.json_response(response)

    except Exception as e:
        return web.json_response({'error': str(e)}, status=400)


async def get_player_by_id(request):
    """handler to fetch specific player data"""
    try:
        player_id = request.match_info['playerID']
        player = await players_db.get_player_by_id(player_id)
        if player:
            return web.json_response(player)
        return web.json_response({"error": f"Requested player={player_id} is not found"}, status=404)
    except Exception as e:
        return web.json_response({'error': str(e)}, status=400)