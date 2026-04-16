import unittest
import json
from typing import Dict, List, Any, Optional
from flask import Flask, Response
from models import Game, Publisher, Category, db, init_db
from routes.games import games_bp

class TestGamesRoutes(unittest.TestCase):
    # Test data with overlapping publisher/category combos for thorough filter testing
    TEST_DATA: Dict[str, Any] = {
        "publishers": [
            {"name": "DevGames Inc"},
            {"name": "Scrum Masters"},
            {"name": "Indie Studios"}
        ],
        "categories": [
            {"name": "Strategy"},
            {"name": "Card Game"},
            {"name": "Puzzle"}
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
                "category_index": 1,
                "star_rating": 4.2
            },
            {
                "title": "Code Quest",
                "description": "Solve programming puzzles to advance through levels",
                "publisher_index": 0,
                "category_index": 2,
                "star_rating": 3.8
            },
            {
                "title": "Sprint Showdown",
                "description": "Compete in strategic sprint planning battles",
                "publisher_index": 1,
                "category_index": 0,
                "star_rating": 4.0
            }
        ]
    }
    
    # API paths
    GAMES_API_PATH: str = '/api/games'

    def setUp(self) -> None:
        """Set up test database and seed data"""
        # Create a fresh Flask app for testing
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        # Register the games blueprint
        self.app.register_blueprint(games_bp)
        
        # Initialize the test client
        self.client = self.app.test_client()
        
        # Initialize in-memory database for testing
        init_db(self.app, testing=True)
        
        # Create tables and seed data
        with self.app.app_context():
            db.create_all()
            self._seed_test_data()

    def tearDown(self) -> None:
        """Clean up test database and ensure proper connection closure"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
            db.engine.dispose()

    def _seed_test_data(self) -> None:
        """Helper method to seed test data"""
        # Create test publishers
        publishers = [
            Publisher(**publisher_data) for publisher_data in self.TEST_DATA["publishers"]
        ]
        db.session.add_all(publishers)
        
        # Create test categories
        categories = [
            Category(**category_data) for category_data in self.TEST_DATA["categories"]
        ]
        db.session.add_all(categories)
        
        # Commit to get IDs
        db.session.commit()
        
        # Create test games
        games = []
        for game_data in self.TEST_DATA["games"]:
            game_dict = game_data.copy()
            publisher_index = game_dict.pop("publisher_index")
            category_index = game_dict.pop("category_index")
            
            games.append(Game(
                **game_dict,
                publisher=publishers[publisher_index],
                category=categories[category_index]
            ))
            
        db.session.add_all(games)
        db.session.commit()

    def _get_response_data(self, response: Response) -> Any:
        """Helper method to parse response data"""
        return json.loads(response.data)

    def test_get_games_success(self) -> None:
        """Test successful retrieval of multiple games"""
        # Act
        response = self.client.get(self.GAMES_API_PATH)
        data = self._get_response_data(response)
        
        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), len(self.TEST_DATA["games"]))
        
        # Verify all game titles are present (order-independent)
        returned_titles = {game['title'] for game in data}
        expected_titles = {game['title'] for game in self.TEST_DATA["games"]}
        self.assertEqual(returned_titles, expected_titles)
        
        # Verify each game has correct publisher/category
        for game_data in data:
            test_game = next(g for g in self.TEST_DATA["games"] if g["title"] == game_data["title"])
            test_publisher = self.TEST_DATA["publishers"][test_game["publisher_index"]]
            test_category = self.TEST_DATA["categories"][test_game["category_index"]]
            
            self.assertEqual(game_data['publisher']['name'], test_publisher["name"])
            self.assertEqual(game_data['category']['name'], test_category["name"])
            self.assertEqual(game_data['starRating'], test_game["star_rating"])

    def test_get_games_structure(self) -> None:
        """Test the response structure for games"""
        # Act
        response = self.client.get(self.GAMES_API_PATH)
        data = self._get_response_data(response)
        
        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), len(self.TEST_DATA["games"]))
        
        required_fields = ['id', 'title', 'description', 'publisher', 'category', 'starRating']
        for field in required_fields:
            self.assertIn(field, data[0])

    def test_get_game_by_id_success(self) -> None:
        """Test successful retrieval of a single game by ID"""
        # Get the first game's ID from the list endpoint
        response = self.client.get(self.GAMES_API_PATH)
        games = self._get_response_data(response)
        game_id = games[0]['id']
        
        # Act
        response = self.client.get(f'{self.GAMES_API_PATH}/{game_id}')
        data = self._get_response_data(response)
        
        # Assert
        first_game = self.TEST_DATA["games"][0]
        first_publisher = self.TEST_DATA["publishers"][first_game["publisher_index"]]
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['title'], first_game["title"])
        self.assertEqual(data['publisher']['name'], first_publisher["name"])
        
    def test_get_game_by_id_not_found(self) -> None:
        """Test retrieval of a non-existent game by ID"""
        # Act
        response = self.client.get(f'{self.GAMES_API_PATH}/999')
        data = self._get_response_data(response)
        
        # Assert
        self.assertEqual(response.status_code, 404)
        self.assertEqual(data['error'], "Game not found")

    # --- Filter tests ---

    def _get_publisher_id(self, publisher_name: str) -> int:
        """Helper to get a publisher ID by name from the games list."""
        response = self.client.get(self.GAMES_API_PATH)
        data = self._get_response_data(response)
        for game in data:
            if game['publisher'] and game['publisher']['name'] == publisher_name:
                return game['publisher']['id']
        raise ValueError(f"Publisher '{publisher_name}' not found in games response")

    def _get_category_id(self, category_name: str) -> int:
        """Helper to get a category ID by name from the games list."""
        response = self.client.get(self.GAMES_API_PATH)
        data = self._get_response_data(response)
        for game in data:
            if game['category'] and game['category']['name'] == category_name:
                return game['category']['id']
        raise ValueError(f"Category '{category_name}' not found in games response")

    def test_filter_by_publisher(self) -> None:
        """Test filtering games by publisher_id returns correct subset"""
        publisher_id = self._get_publisher_id("DevGames Inc")
        response = self.client.get(f'{self.GAMES_API_PATH}?publisher_id={publisher_id}')
        data = self._get_response_data(response)

        self.assertEqual(response.status_code, 200)
        returned_titles = {game['title'] for game in data}
        self.assertEqual(returned_titles, {"Pipeline Panic", "Code Quest"})

    def test_filter_by_category(self) -> None:
        """Test filtering games by category_id returns correct subset"""
        category_id = self._get_category_id("Strategy")
        response = self.client.get(f'{self.GAMES_API_PATH}?category_id={category_id}')
        data = self._get_response_data(response)

        self.assertEqual(response.status_code, 200)
        returned_titles = {game['title'] for game in data}
        self.assertEqual(returned_titles, {"Pipeline Panic", "Sprint Showdown"})

    def test_filter_by_publisher_and_category(self) -> None:
        """Test filtering by both publisher_id and category_id (AND logic)"""
        publisher_id = self._get_publisher_id("Scrum Masters")
        category_id = self._get_category_id("Strategy")
        response = self.client.get(
            f'{self.GAMES_API_PATH}?publisher_id={publisher_id}&category_id={category_id}'
        )
        data = self._get_response_data(response)

        self.assertEqual(response.status_code, 200)
        returned_titles = {game['title'] for game in data}
        self.assertEqual(returned_titles, {"Sprint Showdown"})

    def test_filter_nonexistent_publisher(self) -> None:
        """Test filtering with a non-existent publisher_id returns empty list"""
        response = self.client.get(f'{self.GAMES_API_PATH}?publisher_id=9999')
        data = self._get_response_data(response)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data, [])

    def test_filter_nonexistent_category(self) -> None:
        """Test filtering with a non-existent category_id returns empty list"""
        response = self.client.get(f'{self.GAMES_API_PATH}?category_id=9999')
        data = self._get_response_data(response)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data, [])

    def test_filter_invalid_publisher_id(self) -> None:
        """Test filtering with non-integer publisher_id returns 400"""
        response = self.client.get(f'{self.GAMES_API_PATH}?publisher_id=abc')
        data = self._get_response_data(response)

        self.assertEqual(response.status_code, 400)
        self.assertIn('error', data)

    def test_filter_invalid_category_id(self) -> None:
        """Test filtering with non-integer category_id returns 400"""
        response = self.client.get(f'{self.GAMES_API_PATH}?category_id=xyz')
        data = self._get_response_data(response)

        self.assertEqual(response.status_code, 400)
        self.assertIn('error', data)

    def test_filter_empty_publisher_id(self) -> None:
        """Test filtering with empty publisher_id returns 400"""
        response = self.client.get(f'{self.GAMES_API_PATH}?publisher_id=')
        data = self._get_response_data(response)

        self.assertEqual(response.status_code, 400)
        self.assertIn('error', data)

    def test_filter_empty_category_id(self) -> None:
        """Test filtering with empty category_id returns 400"""
        response = self.client.get(f'{self.GAMES_API_PATH}?category_id=')
        data = self._get_response_data(response)

        self.assertEqual(response.status_code, 400)
        self.assertIn('error', data)

    def test_filter_valid_publisher_with_invalid_category(self) -> None:
        """Test mixed valid/invalid filters returns 400 for invalid category_id"""
        publisher_id = self._get_publisher_id("DevGames Inc")
        response = self.client.get(
            f'{self.GAMES_API_PATH}?publisher_id={publisher_id}&category_id=bad-value'
        )
        data = self._get_response_data(response)

        self.assertEqual(response.status_code, 400)
        self.assertIn('error', data)

    def test_no_filter_returns_all(self) -> None:
        """Test that no filter params returns all games"""
        response = self.client.get(self.GAMES_API_PATH)
        data = self._get_response_data(response)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), len(self.TEST_DATA["games"]))

if __name__ == '__main__':
    unittest.main()
