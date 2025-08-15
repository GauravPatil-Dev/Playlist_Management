#!/usr/bin/env python3
"""
Unit tests for the Playlist API
"""

import pytest
import sqlite3
import json
from fastapi.testclient import TestClient
from app.main import app
import tempfile
import os

# Test client
client = TestClient(app)

class TestRootEndpoint:
    def test_root_endpoint(self):
        """Test root endpoint returns API information"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "endpoints" in data

class TestHealthEndpoint:
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

class TestSongsEndpoint:
    def test_get_all_songs_pagination(self):
        """Test getting all songs with pagination"""
        response = client.get("/songs?page=1&per_page=2")
        assert response.status_code == 200
        data = response.json()
        
        assert "songs" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
        assert "total_pages" in data
        
        assert len(data["songs"]) == 2
        assert data["page"] == 1
        assert data["per_page"] == 2
    
    def test_get_songs_default_pagination(self):
        """Test getting songs with default pagination"""
        response = client.get("/songs")
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["songs"]) <= 10  # Default per_page
        assert data["page"] == 1
    
    def test_get_songs_invalid_page(self):
        """Test getting songs with invalid page number"""
        response = client.get("/songs?page=0")
        assert response.status_code == 422  # Validation error
    
    def test_get_songs_invalid_per_page(self):
        """Test getting songs with invalid per_page"""
        response = client.get("/songs?per_page=101")
        assert response.status_code == 422  # Validation error
    
    def test_get_songs_page_beyond_total(self):
        """Test getting songs with page number beyond total pages"""
        response = client.get("/songs?page=999&per_page=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["songs"]) == 0  # Should return empty list
        assert data["page"] == 999
        assert data["total_pages"] >= 1
    
    def test_get_songs_large_page_number(self):
        """Test getting songs with very large page number"""
        response = client.get("/songs?page=999999&per_page=1")
        assert response.status_code == 200
        data = response.json()
        assert len(data["songs"]) == 0  # Should handle gracefully
    
    def test_get_songs_per_page_boundaries(self):
        """Test per_page at boundary values"""
        # Test minimum per_page
        response = client.get("/songs?per_page=1")
        assert response.status_code == 200
        data = response.json()
        assert data["per_page"] == 1
        assert len(data["songs"]) <= 1
        
        # Test maximum per_page
        response = client.get("/songs?per_page=100")
        assert response.status_code == 200
        data = response.json()
        assert data["per_page"] == 100
        assert len(data["songs"]) <= 100
    
    def test_get_songs_pagination_metadata(self):
        """Test pagination metadata is correct"""
        response = client.get("/songs?page=1&per_page=5")
        assert response.status_code == 200
        data = response.json()
        
        # Verify metadata consistency
        assert data["total"] >= 0
        assert data["page"] == 1
        assert data["per_page"] == 5
        assert data["total_pages"] >= 1
        assert len(data["songs"]) <= 5
        
        # Verify total_pages calculation
        expected_total_pages = (data["total"] + data["per_page"] - 1) // data["per_page"]
        assert data["total_pages"] == expected_total_pages

class TestSearchEndpoint:
    def test_search_songs_by_title(self):
        """Test searching songs by title"""
        response = client.get("/songs/search?title=3AM")
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) >= 1  # Should find at least "3AM"
        assert any("3AM" in song["title"] for song in data)
        # Check that all songs have all attributes
        for song in data:
            assert "id" in song
            assert "title" in song
            assert "danceability" in song
            assert "energy" in song
            assert "star_rating" in song
    
    def test_search_songs_case_insensitive(self):
        """Test case-insensitive search"""
        response = client.get("/songs/search?title=3am")
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) >= 1  # Should find songs regardless of case
    
    def test_search_songs_no_results(self):
        """Test search with no results"""
        response = client.get("/songs/search?title=NonExistentSong12345")
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 0
    
    def test_search_songs_missing_title(self):
        """Test search without title parameter"""
        response = client.get("/songs/search")
        assert response.status_code == 422  # Validation error



class TestRatingEndpoints:
    def test_rate_song_valid_rating(self):
        """Test rating a song with valid rating"""
        # Use a song ID from the actual database
        response = client.get("/songs?per_page=1")
        assert response.status_code == 200
        song_id = response.json()["songs"][0]["id"]
        
        response = client.post(
            f"/songs/{song_id}/rate",
            json={"rating": 4}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["song_id"] == song_id
        assert "average_rating" in data
        assert "total_ratings" in data
        assert data["total_ratings"] >= 1
    
    def test_rate_song_invalid_rating(self):
        """Test rating a song with invalid rating"""
        response = client.get("/songs?per_page=1")
        assert response.status_code == 200
        song_id = response.json()["songs"][0]["id"]
        
        response = client.post(
            f"/songs/{song_id}/rate",
            json={"rating": 6}
        )
        assert response.status_code == 422  # Validation error
    
        response = client.post(
            f"/songs/{song_id}/rate",
            json={"rating": 0}
        )
        assert response.status_code == 422  # Validation error
    
    def test_rate_nonexistent_song(self):
        """Test rating a song that doesn't exist"""
        response = client.post(
            "/songs/nonexistent_song_id_12345/rate",
            json={"rating": 5}
        )
        assert response.status_code == 404
    
    def test_get_song_rating(self):
        """Test getting song rating"""
        # Get a song ID
        response = client.get("/songs?per_page=1")
        assert response.status_code == 200
        song_id = response.json()["songs"][0]["id"]
        
        # First rate the song
        client.post(f"/songs/{song_id}/rate", json={"rating": 4})
        client.post(f"/songs/{song_id}/rate", json={"rating": 5})
        
        # Then get the rating
        response = client.get(f"/songs/{song_id}/rating")
        assert response.status_code == 200
        data = response.json()
        
        assert data["song_id"] == song_id
        assert "average_rating" in data
        assert "total_ratings" in data
        assert data["total_ratings"] >= 2
    
    def test_get_song_rating_no_ratings(self):
        """Test getting rating for song with no ratings"""
        # Get a song ID from a later page to avoid conflicts
        response = client.get("/songs?per_page=10&page=5")
        assert response.status_code == 200
        songs = response.json()["songs"]
        if len(songs) > 0:
            song_id = songs[0]["id"]
            
            response = client.get(f"/songs/{song_id}/rating")
            assert response.status_code == 200
            data = response.json()
            
            assert data["song_id"] == song_id
            # Don't assert specific values since there might be existing ratings
            assert "average_rating" in data
            assert "total_ratings" in data
    
    def test_get_nonexistent_song_rating(self):
        """Test getting rating for nonexistent song"""
        response = client.get("/songs/nonexistent_song_id_12345/rating")
        assert response.status_code == 404

class TestDataProcessor:
    def test_data_processor_normalization(self):
        """Test data normalization functionality"""
        from data_processor import PlaylistDataProcessor
        
        # Create test data in columnar format
        test_data = {
            "id": {"0": "test1", "1": "test2"},
            "title": {"0": "Song 1", "1": "Song 2"},
            "danceability": {"0": 0.5, "1": 0.6}
        }
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            temp_file = f.name
        
        try:
            processor = PlaylistDataProcessor(temp_file, "test_processor.db")
            songs = processor.normalize_data(test_data)
            
            assert len(songs) == 2
            assert songs[0]["id"] == "test1"
            assert songs[0]["title"] == "Song 1"
            assert songs[0]["danceability"] == 0.5
            assert songs[1]["id"] == "test2"
            assert songs[1]["title"] == "Song 2"
            assert songs[1]["danceability"] == 0.6
            
        finally:
            os.unlink(temp_file)
            if os.path.exists("test_processor.db"):
                os.unlink("test_processor.db")

if __name__ == "__main__":
    pytest.main([__file__])
