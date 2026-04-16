import unittest
import json
from typing import Dict, List, Any
from flask import Flask, Response
from models import Publisher, Category, Game, db, init_db
from routes.publishers import publishers_bp

class TestPublishersRoutes(unittest.TestCase):
    """Tests for the publishers API endpoint."""

    # Shared test data
    TEST_DATA: Dict[str, Any] = {
        "publishers": [
            {"name": "DevGames Inc", "description": "A leading developer of DevOps-themed games"},
            {"name": "Scrum Masters", "description": "Board games for agile enthusiasts"},
            {"name": "Indie Studios", "description": "Independent game development collective"}
        ],
        "categories": [
            {"name": "Strategy"}
        ],
        "games": [
            {
                "title": "Pipeline Panic",
                "description": "Build your DevOps pipeline before chaos ensues",
                "publisher_index": 0,
                "category_index": 0,
                "star_rating": 4.5
            },
            {
                "title": "Agile Adventures",
                "description": "Navigate your team through sprints and releases",
                "publisher_index": 1,
                "category_index": 0,
                "star_rating": 4.2
            }
        ]
    }

    PUBLISHERS_API_PATH: str = '/api/publishers'

    def setUp(self) -> None:
        """Set up test database and seed data."""
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

        self.app.register_blueprint(publishers_bp)
        self.client = self.app.test_client()
        init_db(self.app, testing=True)

        with self.app.app_context():
            db.create_all()
            self._seed_test_data()

    def tearDown(self) -> None:
        """Clean up test database and ensure proper connection closure."""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
            db.engine.dispose()

    def _seed_test_data(self) -> None:
        """Helper method to seed test data."""
        publishers = [Publisher(**p) for p in self.TEST_DATA["publishers"]]
        db.session.add_all(publishers)

        categories = [Category(**c) for c in self.TEST_DATA["categories"]]
        db.session.add_all(categories)
        db.session.commit()

        for game_data in self.TEST_DATA["games"]:
            gd = game_data.copy()
            pi = gd.pop("publisher_index")
            ci = gd.pop("category_index")
            db.session.add(Game(**gd, publisher=publishers[pi], category=categories[ci]))
        db.session.commit()

    def _get_response_data(self, response: Response) -> Any:
        """Helper method to parse response data."""
        return json.loads(response.data)

    def test_get_publishers_success(self) -> None:
        """Test successful retrieval of all publishers."""
        response = self.client.get(self.PUBLISHERS_API_PATH)
        data = self._get_response_data(response)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), len(self.TEST_DATA["publishers"]))

        returned_names = {p['name'] for p in data}
        expected_names = {p['name'] for p in self.TEST_DATA["publishers"]}
        self.assertEqual(returned_names, expected_names)

    def test_get_publishers_structure(self) -> None:
        """Test the response structure is lightweight {id, name} only."""
        response = self.client.get(self.PUBLISHERS_API_PATH)
        data = self._get_response_data(response)

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(data, list)

        for publisher in data:
            self.assertIn('id', publisher)
            self.assertIn('name', publisher)
            # Should NOT include description or game_count (lightweight response)
            self.assertNotIn('description', publisher)
            self.assertNotIn('game_count', publisher)

    def test_get_publishers_sorted_by_name(self) -> None:
        """Test that publishers are returned sorted alphabetically by name."""
        response = self.client.get(self.PUBLISHERS_API_PATH)
        data = self._get_response_data(response)

        names = [p['name'] for p in data]
        self.assertEqual(names, sorted(names))


if __name__ == '__main__':
    unittest.main()
