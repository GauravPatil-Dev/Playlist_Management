#!/usr/bin/env python3
"""
FastAPI Backend for Playlist Management
Provides REST APIs for song data with pagination, search, and rating functionality
"""

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import sqlite3
import json
from pydantic import BaseModel, Field
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Playlist API",
    description="REST API for managing playlist data with song ratings",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class Song(BaseModel):
    id: str
    title: str
    danceability: Optional[float] = None
    energy: Optional[float] = None
    key: Optional[int] = None
    loudness: Optional[float] = None
    mode: Optional[int] = None
    acousticness: Optional[float] = None
    instrumentalness: Optional[float] = None
    liveness: Optional[float] = None
    valence: Optional[float] = None
    tempo: Optional[float] = None
    duration_ms: Optional[int] = None
    time_signature: Optional[int] = None
    num_bars: Optional[int] = None
    num_sections: Optional[int] = None
    num_segments: Optional[int] = None
    class_: Optional[int] = Field(None, alias="class")
    star_rating: Optional[float] = None

class SongResponse(BaseModel):
    songs: List[Song]
    total: int
    page: int
    per_page: int
    total_pages: int

class RatingRequest(BaseModel):
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5 stars")

class RatingResponse(BaseModel):
    song_id: str
    average_rating: float
    total_ratings: int

# Database connection
def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect("playlist.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row  # This enables column access by name
    return conn

# API Endpoints

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Playlist API",
        "version": "1.0.0",
        "endpoints": {
            "get_all_songs": "/songs",
            "get_song_by_title": "/songs/search",
            "rate_song": "/songs/{song_id}/rate",
            "get_song_rating": "/songs/{song_id}/rating"
        }
    }

@app.get("/songs", response_model=SongResponse, tags=["Songs"])
async def get_all_songs(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    db: sqlite3.Connection = Depends(get_db_connection)
):
    """
    Get all songs with pagination
    
    Returns:
        Paginated list of songs with metadata
    """
    try:
        cursor = db.cursor()
        
        # Get total count
        cursor.execute("SELECT COUNT(*) as total FROM songs")
        total = cursor.fetchone()["total"]
        
        # Calculate pagination
        offset = (page - 1) * per_page
        total_pages = (total + per_page - 1) // per_page
        
        # Get songs for current page
        cursor.execute("""
            SELECT * FROM songs 
            ORDER BY title 
            LIMIT ? OFFSET ?
        """, (per_page, offset))
        
        rows = cursor.fetchall()
        songs = []
        
        for row in rows:
            song_dict = dict(row)
            # Handle the 'class' field (reserved keyword in Python)
            if 'class' in song_dict:
                song_dict['class_'] = song_dict.pop('class')
            songs.append(Song(**song_dict))
        
        return SongResponse(
            songs=songs,
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(f"Error fetching songs: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/songs/search", response_model=List[Song], tags=["Songs"])
async def search_songs_by_title(
    title: str = Query(..., description="Song title to search for"),
    db: sqlite3.Connection = Depends(get_db_connection)
):
    """
    Search songs by title
    
    Args:
        title: Title to search for (case-insensitive partial match)
        
    Returns:
        List of songs matching the title with all attributes
    """
    try:
        cursor = db.cursor()
        
        cursor.execute("""
            SELECT * FROM songs 
            WHERE LOWER(title) LIKE LOWER(?) 
            ORDER BY title
        """, (f"%{title}%",))
        
        rows = cursor.fetchall()
        songs = []
        
        for row in rows:
            song_dict = dict(row)
            if 'class' in song_dict:
                song_dict['class_'] = song_dict.pop('class')
            songs.append(Song(**song_dict))
        
        return songs
        
    except Exception as e:
        logger.error(f"Error searching songs: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/songs/{song_id}/rate", response_model=RatingResponse, tags=["Ratings"])
async def rate_song(
    song_id: str,
    rating_request: RatingRequest,
    db: sqlite3.Connection = Depends(get_db_connection)
):
    """
    Rate a song with 1-5 stars
    
    Args:
        song_id: ID of the song to rate
        rating_request: Rating data (1-5 stars)
        
    Returns:
        Updated rating information for the song
    """
    try:
        cursor = db.cursor()
        
        # Check if song exists
        cursor.execute("SELECT id FROM songs WHERE id = ?", (song_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Song not found")
        
        # Insert rating
        cursor.execute("""
            INSERT INTO song_ratings (song_id, rating) 
            VALUES (?, ?)
        """, (song_id, rating_request.rating))
        
        # Calculate new average rating
        cursor.execute("""
            SELECT AVG(rating) as avg_rating, COUNT(*) as total_ratings 
            FROM song_ratings 
            WHERE song_id = ?
        """, (song_id,))
        
        result = cursor.fetchone()
        average_rating = result["avg_rating"] or 0.0
        total_ratings = result["total_ratings"]
        
        # Update song's star_rating
        cursor.execute("""
            UPDATE songs 
            SET star_rating = ? 
            WHERE id = ?
        """, (average_rating, song_id))
        
        db.commit()
        
        return RatingResponse(
            song_id=song_id,
            average_rating=round(average_rating, 2),
            total_ratings=total_ratings
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rating song: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/songs/{song_id}/rating", response_model=RatingResponse, tags=["Ratings"])
async def get_song_rating(
    song_id: str,
    db: sqlite3.Connection = Depends(get_db_connection)
):
    """
    Get rating information for a song
    
    Args:
        song_id: ID of the song
        
    Returns:
        Rating information for the song
    """
    try:
        cursor = db.cursor()
        
        # Check if song exists
        cursor.execute("SELECT id FROM songs WHERE id = ?", (song_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Song not found")
        
        # Get rating information
        cursor.execute("""
            SELECT AVG(rating) as avg_rating, COUNT(*) as total_ratings 
            FROM song_ratings 
            WHERE song_id = ?
        """, (song_id,))
        
        result = cursor.fetchone()
        average_rating = result["avg_rating"] or 0.0
        total_ratings = result["total_ratings"]
        
        return RatingResponse(
            song_id=song_id,
            average_rating=round(average_rating, 2),
            total_ratings=total_ratings
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting song rating: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
