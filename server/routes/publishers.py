from flask import jsonify, Response, Blueprint
from models import db, Publisher

# Create a Blueprint for publishers routes
publishers_bp = Blueprint('publishers', __name__)


@publishers_bp.route('/api/publishers', methods=['GET'])
def get_publishers() -> Response:
    """Returns all publishers as a lightweight list of {id, name} objects."""
    publishers = db.session.query(Publisher).order_by(Publisher.name).all()
    publishers_list = [{"id": p.id, "name": p.name} for p in publishers]
    return jsonify(publishers_list)
