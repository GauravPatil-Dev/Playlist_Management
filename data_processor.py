#!/usr/bin/env python3
"""
Data Processing Script for Playlist Normalization
Converts columnar JSON format to normalized row-based format
"""

import json
import sqlite3
import pandas as pd
from typing import Dict, List, Any
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PlaylistDataProcessor:
    def __init__(self, json_file_path: str, db_path: str = "playlist.db"):
        """
        Initialize the data processor
        
        Args:
            json_file_path: Path to the JSON file containing playlist data
            db_path: Path to SQLite database file
        """
        self.json_file_path = json_file_path
        self.db_path = db_path
        self.conn = None
        
    def load_json_data(self) -> Dict[str, Any]:
        """Load JSON data from file"""
        try:
            with open(self.json_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            logger.info(f"Successfully loaded JSON data with {len(data)} attributes")
            return data
        except Exception as e:
            logger.error(f"Error loading JSON file: {e}")
            raise
    
    def normalize_data(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Normalize columnar data to row-based format
        
        Args:
            data: Columnar JSON data
            
        Returns:
            List of dictionaries representing normalized song records
        """
        # Get the number of records (assuming all attributes have same length)
        first_attribute = list(data.values())[0]
        num_records = len(first_attribute)
        
        normalized_records = []
        
        for i in range(num_records):
            record = {}
            for attribute_name, attribute_values in data.items():
                if str(i) in attribute_values:
                    record[attribute_name] = attribute_values[str(i)]
                else:
                    record[attribute_name] = None
            
            # Add star_rating column (initialized to None)
            record['star_rating'] = None
            
            normalized_records.append(record)
        
        logger.info(f"Normalized {len(normalized_records)} song records")
        return normalized_records
    
    def create_database(self):
        """Create SQLite database and tables"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            cursor = self.conn.cursor()
            
            # Create songs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS songs (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    danceability REAL,
                    energy REAL,
                    key INTEGER,
                    loudness REAL,
                    mode INTEGER,
                    acousticness REAL,
                    instrumentalness REAL,
                    liveness REAL,
                    valence REAL,
                    tempo REAL,
                    duration_ms INTEGER,
                    time_signature INTEGER,
                    num_bars INTEGER,
                    num_sections INTEGER,
                    num_segments INTEGER,
                    class INTEGER,
                    star_rating REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create ratings table for tracking individual ratings
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS song_ratings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    song_id TEXT,
                    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (song_id) REFERENCES songs (id)
                )
            ''')
            
            self.conn.commit()
            logger.info("Database and tables created successfully")
            
        except Exception as e:
            logger.error(f"Error creating database: {e}")
            raise
    
    def insert_songs(self, songs: List[Dict[str, Any]]):
        """Insert normalized songs into database"""
        try:
            cursor = self.conn.cursor()
            
            for song in songs:
                cursor.execute('''
                    INSERT OR REPLACE INTO songs (
                        id, title, danceability, energy, key, loudness, mode,
                        acousticness, instrumentalness, liveness, valence, tempo,
                        duration_ms, time_signature, num_bars, num_sections,
                        num_segments, class, star_rating
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    song.get('id'),
                    song.get('title'),
                    song.get('danceability'),
                    song.get('energy'),
                    song.get('key'),
                    song.get('loudness'),
                    song.get('mode'),
                    song.get('acousticness'),
                    song.get('instrumentalness'),
                    song.get('liveness'),
                    song.get('valence'),
                    song.get('tempo'),
                    song.get('duration_ms'),
                    song.get('time_signature'),
                    song.get('num_bars'),
                    song.get('num_sections'),
                    song.get('num_segments'),
                    song.get('class'),
                    song.get('star_rating')
                ))
            
            self.conn.commit()
            logger.info(f"Successfully inserted {len(songs)} songs into database")
            
        except Exception as e:
            logger.error(f"Error inserting songs: {e}")
            raise
    
    def export_to_json(self, songs: List[Dict[str, Any]], output_file: str = "normalized_songs.json"):
        """Export normalized data to JSON file"""
        try:
            with open(output_file, 'w', encoding='utf-8') as file:
                json.dump(songs, file, indent=2, ensure_ascii=False)
            logger.info(f"Normalized data exported to {output_file}")
        except Exception as e:
            logger.error(f"Error exporting to JSON: {e}")
            raise
    
    def process(self, export_json: bool = True):
        """Main processing method"""
        try:
            # Load data
            data = self.load_json_data()
            
            # Normalize data
            songs = self.normalize_data(data)
            
            # Create database
            self.create_database()
            
            # Insert into database
            self.insert_songs(songs)
            
            # Export to JSON if requested
            if export_json:
                self.export_to_json(songs)
            
            logger.info("Data processing completed successfully")
            return songs
            
        except Exception as e:
            logger.error(f"Error in data processing: {e}")
            raise
        finally:
            if self.conn:
                self.conn.close()

def main():
    """Main function to run the data processor"""
    # Process the playlist data
    processor = PlaylistDataProcessor("playlist.json")
    songs = processor.process()
    
    print(f"Successfully processed {len(songs)} songs")
    print("Sample song data:")
    if songs:
        print(json.dumps(songs[0], indent=2))

if __name__ == "__main__":
    main()
