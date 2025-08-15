# 🎵 Playlist Management System

A full-stack application for processing playlist data and providing REST APIs for song management with rating functionality.

## 📋 Features

### ✅ Data Processing (1.1)
- **JSON Normalization**: Converts columnar JSON format to normalized row-based format
- **Database Storage**: Stores normalized data in SQLite database
- **Data Export**: Exports normalized data to JSON file

### ✅ Backend API (1.2)
- **RESTful API**: Built with FastAPI for high performance
- **Pagination**: Get all songs with configurable pagination
- **Search**: Search songs by title (case-insensitive)
- **Star Rating**: Rate songs with 1-5 stars
- **Rating Statistics**: Get average ratings and total rating count
- **Auto-generated Documentation**: Interactive API docs with Swagger UI

### ✅ Frontend (Minimal Demo)
- **Simple Interface**: Basic HTML/CSS/JS demo
- **API Testing**: Interactive testing of all endpoints
- **Real-time Results**: Immediate feedback on API calls
- **Error Handling**: Clear error messages and validation

### ✅ Testing (1.2.4)
- **Unit Tests**: Comprehensive test coverage for all endpoints
- **Data Processing Tests**: Tests for normalization functionality
- **Error Handling**: Tests for edge cases and error scenarios

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd vivpro
   ```

2. **Create and activate virtual environment (recommended)**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Process the playlist data**
   ```bash
   python data_processor.py
   ```

4. **Start the API server**
   ```bash
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

5. **Test the API**
   - **Interactive API Docs**: Visit `http://localhost:8000/docs` for Swagger documentation
   - **Simple Frontend Demo**: Open `frontend/index.html` in your web browser
   - **Direct API Testing**: Use curl or any HTTP client to test endpoints

## 📊 API Documentation

### Base URL
```
http://localhost:8000
```

### Interactive API Docs
Visit `http://localhost:8000/docs` for interactive Swagger documentation.

### Endpoints

#### 1. Get All Songs (MUST HAVE - 1.2.1)
```http
GET /songs?page=1&per_page=10
```

**Parameters:**
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Items per page (default: 10, max: 100)

**Response:**
```json
{
  "songs": [
    {
      "id": "5vYA1mW9g2Coh1HUFUSmlb",
      "title": "3AM",
      "danceability": 0.521,
      "energy": 0.673,
      "star_rating": 4.2
    }
  ],
  "total": 100,
  "page": 1,
  "per_page": 10,
  "total_pages": 10
}
```

#### 2. Search Songs by Title (MUST HAVE - 1.2.2)
```http
GET /songs/search?title=love
```

**Parameters:**
- `title` (required): Search term (case-insensitive partial match)

**Response:**
```json
[
  {
    "id": "6LtPIXlIzPOTF8vTecYjRe",
    "title": "Bleeding Love",
    "danceability": 0.6,
    "energy": 0.7,
    "key": 5,
    "loudness": -5.2,
    "mode": 1,
    "acousticness": 0.3,
    "instrumentalness": 0.0,
    "liveness": 0.1,
    "valence": 0.4,
    "tempo": 120.5,
    "duration_ms": 240000,
    "time_signature": 4,
    "num_bars": 120,
    "num_sections": 8,
    "num_segments": 400,
    "class_": 1,
    "star_rating": 4.2
  }
]
```

#### 3. Rate a Song (NICE TO HAVE - 1.2.3)
```http
POST /songs/{song_id}/rate
Content-Type: application/json

{
  "rating": 5
}
```

**Parameters:**
- `song_id` (path): ID of the song to rate
- `rating` (body): Rating from 1 to 5 stars

**Response:**
```json
{
  "song_id": "5vYA1mW9g2Coh1HUFUSmlb",
  "average_rating": 4.5,
  "total_ratings": 3
}
```

#### 4. Get Song Rating
```http
GET /songs/{song_id}/rating
```

**Response:**
```json
{
  "song_id": "5vYA1mW9g2Coh1HUFUSmlb",
  "average_rating": 4.2,
  "total_ratings": 5
}
```

#### 5. Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "message": "API is running"
}
```

## 🧪 Running Tests

```bash
# Run all tests
pytest tests/

# Run with verbose output
pytest -v tests/

# Run specific test file
pytest tests/test_api.py

# Run with coverage
pytest --cov=app tests/
```

## 📁 Project Structure

```
vivpro/
├── app/
│   └── main.py              # FastAPI application
├── frontend/
│   └── index.html           # Web interface
├── tests/
│   └── test_api.py          # Unit tests
├── data_processor.py        # Data normalization script
├── requirements.txt         # Python dependencies
├── playlist.json           # Sample playlist data
├── playlist.db             # SQLite database (generated)
├── normalized_songs.json   # Normalized data (generated)
└── README.md              # This file
```

## 🔧 Configuration

### Database
- **Type**: SQLite (file-based, no setup required)
- **Location**: `playlist.db` (auto-created)
- **Tables**: 
  - `songs`: Main song data
  - `song_ratings`: Individual user ratings

### API Configuration
- **Host**: `0.0.0.0` (accessible from any IP)
- **Port**: `8000`
- **CORS**: Enabled for all origins (development)

## 📈 Data Processing Details

### Input Format
The system processes JSON data in columnar format:
```json
{
  "id": {"0": "song1", "1": "song2"},
  "title": {"0": "Song 1", "1": "Song 2"},
  "danceability": {"0": 0.5, "1": 0.6}
}
```

### Output Format
Converts to normalized row-based format:
```json
[
  {
    "id": "song1",
    "title": "Song 1",
    "danceability": 0.5
  },
  {
    "id": "song2",
    "title": "Song 2",
    "danceability": 0.6
  }
]
```

## 🎯 API Features

### Pagination
- **Default**: 10 items per page
- **Maximum**: 100 items per page
- **Metadata**: Total count, current page, total pages

### Search
- **Case-insensitive**: Matches regardless of case
- **Partial matching**: Finds songs containing search term
- **Real-time**: Fast search with database indexing

### Rating System
- **Range**: 1-5 stars
- **Validation**: Ensures ratings are within valid range
- **Statistics**: Tracks average rating and total ratings
- **Real-time updates**: Immediate UI feedback

## 🚀 Deployment

### Development
```bash
# Start with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```



## 🔍 Troubleshooting

### Common Issues

1. **Database not found**
   ```bash
   python data_processor.py
   ```

2. **Port already in use**
   ```bash
   # Use different port
   uvicorn app.main:app --port 8001
   ```

3. **CORS errors in frontend**
   - Ensure API is running on `http://localhost:8000`
   - Check browser console for errors

4. **Import errors**
   ```bash
   pip install -r requirements.txt
   ```

## 📝 API Response Codes

- `200`: Success
- `404`: Resource not found
- `422`: Validation error
- `500`: Internal server error



## 🎉 Features Summary

| Feature | Status | Description |
|---------|--------|-------------|
| Data Processing | ✅ Complete | Normalizes JSON data to database |
| Get All Songs | ✅ Complete | Paginated song listing |
| Search by Title | ✅ Complete | Case-insensitive search |
| Star Rating | ✅ Complete | 1-5 star rating system |
| Unit Tests | ✅ Complete | Comprehensive test coverage |
| Frontend Demo | ✅ Complete | Simple API testing interface |
| API Documentation | ✅ Complete | Auto-generated Swagger docs |
| Error Handling | ✅ Complete | Proper HTTP status codes |
| Pagination | ✅ Complete | Configurable page size |
| Database | ✅ Complete | SQLite with proper schema |
