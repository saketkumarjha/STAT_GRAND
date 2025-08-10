# NCO Semantic Search Backend

AI-enabled Semantic Search for National Classification of Occupation (NCO) - Backend API

## Overview

This backend provides RESTful APIs for semantic search functionality over NCO-2015 occupation data. It includes multilingual support, vector similarity search, and comprehensive analytics.

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── api/                 # API routes and endpoints
│   │   ├── __init__.py
│   │   ├── routes.py        # Main API router
│   │   └── endpoints/       # Individual endpoint modules
│   │       ├── search.py    # Search endpoints
│   │       ├── occupations.py # Occupation data endpoints
│   │       └── analytics.py # Analytics endpoints
│   ├── core/                # Core configuration and utilities
│   │   ├── __init__.py
│   │   ├── config.py        # Application configuration
│   │   └── dependencies.py  # FastAPI dependencies
│   ├── models/              # Data models
│   │   ├── __init__.py
│   │   ├── occupation.py    # Occupation data model
│   │   └── search.py        # Search result models
│   └── services/            # Business logic services
│       └── __init__.py
├── requirements.txt         # Python dependencies
├── .env.example            # Environment configuration template
├── run_server.py           # Server startup script
└── README.md               # This file
```

## Quick Start

1. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**

   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start the Server**

   ```bash
   python run_server.py
   ```

4. **Access API Documentation**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## API Endpoints

### Search Endpoints (`/api/v1/search`)

- `POST /` - Semantic search for occupation codes
- `GET /suggestions` - Get search suggestions
- `GET /similar/{occupation_code}` - Get similar occupations

### Occupation Endpoints (`/api/v1/occupations`)

- `GET /{occupation_code}` - Get occupation details
- `GET /` - List occupations with filtering
- `GET /hierarchy/{level}` - Get hierarchy information

### Analytics Endpoints (`/api/v1/analytics`)

- `GET /usage` - Usage metrics and statistics
- `GET /search-patterns` - Search pattern analysis
- `GET /performance` - Performance metrics
- `POST /feedback` - Submit user feedback

## Configuration

The application uses environment variables for configuration. See `.env.example` for available options:

- **Application Settings**: Name, version, debug mode
- **API Settings**: Host, port, prefix
- **Database Settings**: Connection URL, echo mode
- **ML Settings**: Model configuration, cache settings
- **Language Settings**: Supported languages, defaults
- **Search Settings**: Result limits, confidence thresholds

## Development

### Running in Development Mode

```bash
# Set DEBUG=true in .env
python run_server.py
```

### API Testing

The server includes automatic API documentation at `/docs` endpoint for interactive testing.

## Implementation Status

This is the initial project structure setup. Core functionality will be implemented in subsequent development phases:

- ✅ Project structure and configuration
- ✅ FastAPI application setup
- ✅ API endpoint scaffolding
- ✅ Data models definition
- ⏳ Database integration (next phase)
- ⏳ ML model integration (next phase)
- ⏳ Semantic search implementation (next phase)

## Requirements Addressed

This implementation addresses the following requirements:

- **4.1**: NCO-2015 data structure and models
- **4.2**: FastAPI project setup with routing structure
