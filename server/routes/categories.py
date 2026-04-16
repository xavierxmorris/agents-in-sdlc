from flask import jsonify, Response, Blueprint
from models import db, Category

# Create a Blueprint for categories routes
categories_bp = Blueprint('categories', __name__)


@categories_bp.route('/api/categories', methods=['GET'])
def get_categories() -> Response:
    """Returns all categories as a lightweight list of {id, name} objects."""
    categories = db.session.query(Category).order_by(Category.name).all()
    categories_list = [{"id": c.id, "name": c.name} for c in categories]
    return jsonify(categories_list)
