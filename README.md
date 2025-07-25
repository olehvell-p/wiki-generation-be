# FastAPI URL Analyzer Template

A FastAPI application template with a single `/analyze` endpoint that accepts URLs for analysis.

## Features

- **POST /analyze** - Analyzes a given URL and returns basic information
- **GET /** - Root endpoint with API information
- **GET /health** - Health check endpoint
- Auto-generated OpenAPI documentation
- Request/response validation with Pydantic
- Type hints throughout

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

Start the development server:
```bash
python main.py
```

Or using uvicorn directly:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: http://localhost:8000

## API Documentation

Once running, you can view the interactive API documentation at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Usage

### Analyze URL

**Endpoint**: `POST /analyze`

**Request Body**:
```json
{
  "url": "https://example.com/path?query=value"
}
```

**Response**:
```json
{
  "url": "https://example.com/path?query=value",
  "status": "success",
  "message": "URL analyzed successfully",
  "data": {
    "domain": "example.com",
    "scheme": "https",
    "path": "/path",
    "query": "query=value"
  }
}
```

### Example with curl

```bash
curl -X POST "http://localhost:8000/analyze" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://example.com"}'
```

## Development

The template includes:
- Input validation (URL format checking)
- Proper error handling
- Type hints and response models
- Structured logging ready
- Health check endpoint

You can extend the `/analyze` endpoint with your own URL analysis logic by modifying the `analyze_url` function in `main.py`. 