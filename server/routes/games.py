from typing import Any
from flask import jsonify, Response, Blueprint, request
from models import db, Game, Publisher, Category
from sqlalchemy.orm import Query
from sqlalchemy.exc import SQLAlchemyError

# Create a Blueprint for games routes
games_bp = Blueprint('games', __name__)

def get_games_base_query() -> Query:
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
def get_games() -> Response:
    # Use the base query for all games
    games_query = get_games_base_query().all()
    
    # Convert the results using the model's to_dict method
    games_list = [game.to_dict() for game in games_query]
    
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

@games_bp.route('/api/games', methods=['POST'])
def create_game() -> tuple[Response, int] | Response:
    payload: dict[str, Any] | None = request.get_json(silent=True)
    if payload is None:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    required_fields = ["title", "description", "publisherId", "categoryId"]
    missing_fields = [field for field in required_fields if field not in payload]
    if missing_fields:
        return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400

    publisher = db.session.get(Publisher, payload["publisherId"])
    if not publisher:
        return jsonify({"error": "Publisher not found"}), 404

    category = db.session.get(Category, payload["categoryId"])
    if not category:
        return jsonify({"error": "Category not found"}), 404

    try:
        game = Game(
            title=payload["title"],
            description=payload["description"],
            star_rating=payload.get("starRating"),
            publisher=publisher,
            category=category
        )
        db.session.add(game)
        db.session.commit()
    except (ValueError, TypeError):
        db.session.rollback()
        return jsonify({"error": "Invalid game data"}), 400
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Failed to create game"}), 500

    return jsonify(game.to_dict()), 201

@games_bp.route('/api/games/<int:id>', methods=['PUT'])
def update_game(id: int) -> tuple[Response, int] | Response:
    payload: dict[str, Any] | None = request.get_json(silent=True)
    if payload is None:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    game = db.session.get(Game, id)
    if not game:
        return jsonify({"error": "Game not found"}), 404

    try:
        if "title" in payload:
            game.title = payload["title"]
        if "description" in payload:
            game.description = payload["description"]
        if "starRating" in payload:
            game.star_rating = payload["starRating"]
        if "publisherId" in payload:
            publisher = db.session.get(Publisher, payload["publisherId"])
            if not publisher:
                return jsonify({"error": "Publisher not found"}), 404
            game.publisher = publisher
        if "categoryId" in payload:
            category = db.session.get(Category, payload["categoryId"])
            if not category:
                return jsonify({"error": "Category not found"}), 404
            game.category = category

        db.session.commit()
    except (ValueError, TypeError):
        db.session.rollback()
        return jsonify({"error": "Invalid game data"}), 400
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Failed to update game"}), 500

    return jsonify(game.to_dict())

@games_bp.route('/api/games/<int:id>', methods=['DELETE'])
def delete_game(id: int) -> tuple[Response, int] | Response:
    game = db.session.get(Game, id)
    if not game:
        return jsonify({"error": "Game not found"}), 404

    try:
        db.session.delete(game)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Failed to delete game"}), 500

    return jsonify({"message": "Game deleted"})
