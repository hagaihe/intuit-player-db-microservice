
from app.api import get_all_players, get_player_by_id, health_check


def setup_routes(app):
    app.router.add_get('/api/players', get_all_players)
    app.router.add_get('/api/players/{playerID}', get_player_by_id)
    app.router.add_get('/health', health_check)
