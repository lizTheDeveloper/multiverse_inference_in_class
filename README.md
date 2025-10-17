# Multiverse Inference Gateway

A distributed AI inference gateway that enables students to share and access AI models hosted on their own servers through a unified OpenAI-compatible API. The system acts as a routing layer that manages model server registration, performs continuous health monitoring, and routes inference requests to healthy backend servers with automatic failover.

## Features

- **OpenAI-Compatible API**: Use familiar OpenAI Python library without modifications
- **Distributed Model Hosting**: Students can register their own model servers
- **Automatic Health Monitoring**: Continuous health checks with automatic failover
- **Load Balancing**: Round-robin distribution across healthy servers
- **Streaming Support**: Server-Sent Events (SSE) for real-time inference
- **Easy Registration**: Simple REST API for server management
- **Comprehensive Logging**: Structured logging with rotation and sensitive data redaction

## Prerequisites

- Python 3.11 or higher
- pip (Python package installer)
- Virtual environment tool (venv)

## Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd multiverse_inference_in_class
```

### 2. Create Virtual Environment

```bash
python3.11 -m venv env
source env/bin/activate  # On macOS/Linux
# env\Scripts\activate  # On Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

Copy the example configuration file and edit it:

```bash
cp .env.example .env
```

Edit `.env` and set at minimum:

```bash
ADMIN_API_KEY="your-secure-api-key-here-minimum-16-chars"
```

**Important**: The `ADMIN_API_KEY` must be at least 16 characters long. This key is required to access admin endpoints for server registration.

### 5. Start the Gateway

```bash
source .env && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Or use the Python script directly:

```bash
source .env && python app/main.py
```

The gateway will be available at:
- API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc

### 6. Verify Installation

Check the health endpoint:

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "Multiverse Inference Gateway",
  "version": "1.0.0",
  "database": "healthy"
}
```

## Project Structure

```
multiverse_inference_in_class/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── routers/             # API route handlers
│   │   ├── __init__.py
│   │   ├── admin.py         # Admin endpoints (Phase 2)
│   │   └── inference.py     # Inference endpoints (Phase 3)
│   ├── services/            # Business logic
│   │   ├── __init__.py
│   │   ├── registry.py      # Server registration (Phase 2)
│   │   ├── router.py        # Request routing (Phase 3)
│   │   └── health_checker.py # Health monitoring (Phase 4)
│   └── utils/               # Utility modules
│       ├── __init__.py
│       ├── config.py        # Configuration management
│       ├── database.py      # Database operations
│       └── logger.py        # Logging utilities
├── tests/                   # Test suite
├── plans/                   # Project planning documents
├── devlog/                  # Development log
├── logs/                    # Application logs (created at runtime)
├── requirements.txt         # Python dependencies
├── .env.example            # Example configuration
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

## Configuration

All configuration is managed through environment variables, which can be set in the `.env` file. See `.env.example` for a complete list of available options.

### Key Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `ADMIN_API_KEY` | (required) | API key for admin endpoints (min 16 chars) |
| `HOST` | `0.0.0.0` | Host to bind the server to |
| `PORT` | `8000` | Port to bind the server to |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `DATABASE_URL` | `sqlite+aiosqlite:///./gateway.db` | Database connection URL |
| `HEALTH_CHECK_INTERVAL_SECONDS` | `60` | Interval between health checks |
| `MAX_CONSECUTIVE_FAILURES` | `3` | Failures before marking unhealthy |
| `REQUEST_TIMEOUT_SECONDS` | `300` | Timeout for backend requests |

## API Documentation

Once the gateway is running, visit http://localhost:8000/docs for interactive API documentation.

### System Endpoints

- `GET /` - API root information
- `GET /health` - Gateway health check

### Admin API (`/admin/*`)

Admin endpoints require authentication via `X-API-Key` header.

- `POST /admin/register` - Register a new model server
- `DELETE /admin/register/{registration_id}` - Deregister a server
- `PUT /admin/register/{registration_id}` - Update server details
- `GET /admin/servers` - List all registered servers (with optional filters)
- `GET /admin/stats` - Get gateway statistics

### Inference API (`/v1/*`)

OpenAI-compatible endpoints for making model requests.

- `GET /v1/models` - List available models
- `POST /v1/chat/completions` - Create a chat completion
- `POST /v1/completions` - Create a text completion

## Usage Examples

### Registering a Model Server

```bash
curl -X POST "http://localhost:8000/admin/register" \
  -H "X-API-Key: your-admin-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "llama-2-7b",
    "endpoint_url": "https://your-server.ngrok.io",
    "owner_name": "Your Name",
    "owner_email": "your.email@example.com",
    "description": "My model server"
  }'
```

### Listing Available Models

```bash
curl http://localhost:8000/v1/models
```

### Making an Inference Request

Using the OpenAI Python library:

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="not-needed"  # Gateway doesn't require client API keys by default
)

response = client.chat.completions.create(
    model="llama-2-7b",
    messages=[
        {"role": "user", "content": "Hello! How are you?"}
    ]
)

print(response.choices[0].message.content)
```

Using curl:

```bash
curl -X POST "http://localhost:8000/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama-2-7b",
    "messages": [
      {"role": "user", "content": "Hello! How are you?"}
    ]
  }'
```

## Current Status

✅ **Phase 1**: Foundation & Infrastructure - Complete
✅ **Phase 2**: Admin API - Server Registration - Complete
✅ **Phase 3**: Inference API - Request Routing - Complete
✅ **Phase 4**: Background Health Checker - Complete
✅ **Phase 5**: Streaming Support - Complete
⏳ **Phase 6**: Web User Interface - Pending
✅ **Phase 7**: Polish & Documentation - Complete

## Development

### Running in Development Mode

Enable auto-reload for development:

```bash
source .env && python -m uvicorn app.main:app --reload
```

Or set `RELOAD=true` in your `.env` file.

### Running Tests

```bash
pytest tests/ -v --cov=app
```

### Checking Code Style

```bash
# Install development dependencies
pip install flake8 black mypy

# Check style
flake8 app/ tests/

# Format code
black app/ tests/

# Type checking
mypy app/
```

## Logging

Logs are written to both console and file by default. Log files are stored in the `logs/` directory with automatic rotation.

- **Log File**: `logs/gateway.log`
- **Max Size**: 10 MB (configurable)
- **Backups**: 5 files (configurable)
- **Format**: Structured with timestamps, log levels, component names, and context

Sensitive information (API keys, tokens) is automatically redacted from logs.

## Database

The gateway uses SQLite by default with Write-Ahead Logging (WAL) mode enabled for better concurrent access.

- **Location**: `gateway.db` (configurable)
- **Schema**: Automatically created on first run
- **Backups**: Recommended to backup regularly in production

## Troubleshooting

### Issue: `admin_api_key must be set`

**Solution**: Create a `.env` file and set `ADMIN_API_KEY` to a value at least 16 characters long.

### Issue: `Database health check failed`

**Solution**: Ensure the application has write permissions to the current directory and the database file.

### Issue: Port already in use

**Solution**: Change the `PORT` in your `.env` file or stop the process using port 8000:

```bash
# Find process using port 8000
lsof -ti:8000

# Kill the process (replace PID with actual process ID)
kill -9 <PID>
```

### Issue: Module not found errors

**Solution**: Ensure virtual environment is activated and dependencies are installed:

```bash
source env/bin/activate
pip install -r requirements.txt
```

## Contributing

This is a class project. Follow these guidelines:

1. Create feature branches for new work
2. Write tests for new features
3. Update documentation as needed
4. Follow PEP 8 style guidelines
5. Use type hints and docstrings
6. No single-letter variable names

## License

This project is for educational purposes.

## Support

For issues or questions, please contact the course instructor or teaching assistants.

## Acknowledgments

Built for the Multiverse School distributed AI inference project.

