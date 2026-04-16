from flask import jsonify, request, Response, Blueprint
from models import db, Game, Publisher, Category
from sqlalchemy.orm import Query

# Create a Blueprint for games routes
games_bp = Blueprint('games', __name__)

def get_games_base_query() -> Query:
    """Returns the base SQLAlchemy query for games with publisher and category joins."""
    return db.session.query(Game).join(
        Publisher, 
        Game.publisher_id == Publisher.id, 
        isouter=True
    ).join(
        Category, 
        Game.category_id == Category.id, 
        isouter=True
    )

@games_bp.route('/api/games', methods=['GET'])
def get_games() -> Response | tuple[Response, int]:
    """Returns all games, optionally filtered by publisher_id and/or category_id query params."""
    query = get_games_base_query()

    # Apply optional publisher_id filter
    publisher_id = request.args.get('publisher_id')
    if publisher_id is not None:
        try:
            query = query.filter(Game.publisher_id == int(publisher_id))
        except (ValueError, TypeError):
            return jsonify({"error": "publisher_id must be a valid integer"}), 400

    # Apply optional category_id filter
    category_id = request.args.get('category_id')
    if category_id is not None:
        try:
            query = query.filter(Game.category_id == int(category_id))
        except (ValueError, TypeError):
            return jsonify({"error": "category_id must be a valid integer"}), 400

    games_list = [game.to_dict() for game in query.all()]
    return jsonify(games_list)

@games_bp.route('/api/games/<int:id>', methods=['GET'])
def get_game(id: int) -> tuple[Response, int] | Response:
    # Use the base query and add filter for specific game
    game_query = get_games_base_query().filter(Game.id == id).first()
    
    # Return 404 if game not found
    if not game_query: 
        return jsonify({"error": "Game not found"}), 404
    
    # Convert the result using the model's to_dict method
    game = game_query.to_dict()
    
    return jsonify(game)
