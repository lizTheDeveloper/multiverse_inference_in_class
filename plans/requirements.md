# Multiverse Inference System - Requirements Specification

## 1. Introduction

### 1.1 Purpose

This document specifies the requirements for the Multiverse Inference System, a distributed AI inference gateway designed for educational environments. The system enables students to share and access AI models hosted on their own servers through a unified API endpoint.

**Target Audience**: This document is intended for:
- Developers implementing the system
- Students hosting and using models
- System administrators deploying the gateway
- Instructors overseeing the infrastructure

### 1.2 Scope

**In Scope**:
- Model server registration and deregistration API
- Unified inference gateway with OpenAI-compatible endpoints
- Continuous health monitoring of registered servers
- Request routing with automatic failover
- Admin interface for server management
- Comprehensive logging and error handling

**Out of Scope**:
- Model training or fine-tuning
- User authentication and authorization (beyond simple API keys)
- Billing or cost management
- Model hosting infrastructure (students provide their own)
- Advanced load balancing algorithms (Phase 1)

### 1.3 Definitions and Acronyms

- **API**: Application Programming Interface
- **FastAPI**: Modern Python web framework for building APIs
- **Gateway**: The central server that routes inference requests
- **Health Check**: Automated test to verify server availability
- **LLM**: Large Language Model
- **Ngrok**: Tunneling service that exposes local servers to the internet
- **OpenAI API**: Standard API format used by OpenAI for model inference
- **SSE**: Server-Sent Events, protocol for server-to-client streaming
- **Student Server**: A server hosted by a student that runs an AI model
- **Registration**: Process of adding a model server to the gateway registry

### 1.4 References

- OpenAI API Specification: https://platform.openai.com/docs/api-reference
- FastAPI Documentation: https://fastapi.tiangolo.com/
- RFC 2119 (Requirement Keywords): https://www.ietf.org/rfc/rfc2119.txt
- Server-Sent Events Specification: https://html.spec.whatwg.org/multipage/server-sent-events.html

## 2. Goals and Objectives

### 2.1 Business Goals

1. **Resource Sharing**: Enable efficient sharing of computational resources among students without centralized infrastructure costs
2. **Learning Platform**: Provide hands-on experience with distributed systems, API design, and model hosting
3. **Accessibility**: Lower barriers to AI model experimentation by pooling available resources

### 2.2 User Goals

**For Students Hosting Models**:
- Register their model servers in less than 5 minutes
- Receive notifications when their server becomes unhealthy
- View usage statistics for their hosted models

**For Students Using Models**:
- Access multiple models through a single, familiar API
- Use standard OpenAI client libraries without modification
- Receive clear error messages when models are unavailable

### 2.3 Success Metrics

- **Registration Time**: Average time to register a new server < 5 minutes
- **Uptime**: Gateway availability > 99%
- **Request Success Rate**: > 95% of requests successfully routed to healthy servers
- **Detection Speed**: Server failures detected within 60 seconds
- **Concurrent Users**: Support at least 10 concurrent inference requests
- **Adoption**: At least 50% of students successfully host or use models

## 3. User Stories

### US-001: Register Model Server
**As a** student hosting a model  
**I want to** register my server with the gateway  
**So that** other students can use my model through the unified API

**Acceptance Criteria**:
- Registration completes in under 5 minutes
- System validates the server URL before accepting registration
- I receive a unique registration ID upon success
- System performs initial health check immediately after registration

### US-002: Request Inference
**As a** student using models  
**I want to** send inference requests using the OpenAI Python library  
**So that** I can use familiar tools without learning new APIs

**Acceptance Criteria**:
- Can use `openai.ChatCompletion.create()` without modifications
- Receive responses in standard OpenAI format
- Get clear error message if requested model is unavailable

### US-003: Monitor Server Health
**As a** student hosting a model  
**I want to** see when my server is marked as unhealthy  
**So that** I can fix issues and restore service

**Acceptance Criteria**:
- Can query `/admin/servers` to see my server's health status
- Health status updated within 60 seconds of failure
- Logs show specific reason for health check failure

### US-004: Deregister Server
**As a** student hosting a model  
**I want to** remove my server from the registry  
**So that** requests stop being routed to it when I shut down

**Acceptance Criteria**:
- Deregistration completes immediately
- No new requests routed after deregistration
- Can re-register same server later

### US-005: List Available Models
**As a** student using models  
**I want to** see which models are currently available  
**So that** I know which models I can request

**Acceptance Criteria**:
- Can call `/v1/models` endpoint
- Response shows model names and count of healthy servers
- Response format matches OpenAI API specification

### US-006: View Server Dashboard
**As a** student or instructor  
**I want to** see a visual dashboard of all registered servers  
**So that** I can quickly assess system health and server status

**Acceptance Criteria**:
- Can access web dashboard via browser
- Dashboard shows real-time health status of all servers
- Can filter and sort servers
- Dashboard auto-refreshes without page reload
- Mobile-responsive design works on phone/tablet

### US-007: Register Server via Web Form
**As a** student hosting a model  
**I want to** register my server using a web form  
**So that** I don't need to write code or use curl commands

**Acceptance Criteria**:
- Can access registration form via web UI
- Form validates inputs in real-time
- Receive immediate feedback on registration success/failure
- Can copy registration ID easily
- Form is intuitive and completes in under 5 minutes

### US-008: Test Inference via Web UI
**As a** student using models  
**I want to** test inference requests through the web interface  
**So that** I can verify models work before integrating into my code

**Acceptance Criteria**:
- Can select available models from dropdown
- Can enter prompts and see responses
- Can test streaming responses in real-time
- See which backend server handled the request
- View response time and token usage

## 4. Functional Requirements

### 4.1 Model Registry (FR-REG)

**FR-REG-001**: The system MUST maintain a persistent database of registered model servers.

**FR-REG-002**: The system MUST store the following metadata for each registration:
- Unique registration ID (UUID)
- Model name/identifier
- Server endpoint URL
- Optional API key for backend authentication
- Model capabilities (max_tokens, context_length, streaming support)
- Registration timestamp
- Last health check timestamp
- Current health status (healthy/unhealthy/unknown)
- Optional metadata (student_id, description)

**FR-REG-003**: The system MUST support multiple servers hosting the same model name.

**FR-REG-004**: The system SHOULD track historical health check data for each server (last 100 checks).

**FR-REG-005**: The system MAY support soft deletion (marking as deleted rather than removing records).

### 4.2 Server Registration API (FR-API-REG)

**FR-API-REG-001**: The system MUST provide `POST /admin/register` endpoint accepting:
```json
{
  "model_name": "string (required)",
  "endpoint_url": "string (required, valid URL)",
  "api_key": "string (optional)",
  "capabilities": {
    "max_tokens": "integer (optional)",
    "context_length": "integer (optional)",
    "streaming": "boolean (optional, default: true)"
  },
  "metadata": {
    "student_id": "string (optional)",
    "description": "string (optional)"
  }
}
```

**FR-API-REG-002**: The system MUST validate that `endpoint_url` is a valid HTTP/HTTPS URL.

**FR-API-REG-003**: The system MUST perform an immediate health check before accepting registration.

**FR-API-REG-004**: The system MUST return HTTP 201 with registration ID on success:
```json
{
  "registration_id": "uuid",
  "status": "registered",
  "health_status": "healthy"
}
```

**FR-API-REG-005**: The system MUST return HTTP 400 for invalid requests with detailed error message.

**FR-API-REG-006**: The system MUST return HTTP 503 if initial health check fails with error details.

**FR-API-REG-007**: The system MUST provide `DELETE /admin/register/{registration_id}` endpoint for deregistration.

**FR-API-REG-008**: The system MUST provide `PUT /admin/register/{registration_id}` endpoint to update server details.

**FR-API-REG-009**: The system MUST provide `GET /admin/servers` endpoint listing all registered servers with health status.

**FR-API-REG-010**: All admin endpoints MUST require API key authentication via `X-API-Key` header.

### 4.3 Inference API (FR-API-INF)

**FR-API-INF-001**: The system MUST provide `POST /v1/chat/completions` endpoint compatible with OpenAI API specification.

**FR-API-INF-002**: The system MUST accept the following request parameters:
- `model` (string, required): Model name
- `messages` (array, required): Chat messages
- `temperature` (float, optional): Sampling temperature
- `max_tokens` (integer, optional): Maximum tokens to generate
- `stream` (boolean, optional): Enable streaming responses
- `top_p` (float, optional): Nucleus sampling parameter
- Additional OpenAI-compatible parameters

**FR-API-INF-003**: The system MUST return responses in OpenAI chat completion format:
```json
{
  "id": "chatcmpl-{uuid}",
  "object": "chat.completion",
  "created": {unix_timestamp},
  "model": "{model_name}",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "{response_text}"
    },
    "finish_reason": "stop|length|content_filter|null"
  }],
  "usage": {
    "prompt_tokens": {integer},
    "completion_tokens": {integer},
    "total_tokens": {integer}
  }
}
```

**FR-API-INF-004**: The system MUST provide `POST /v1/completions` endpoint for non-chat completions.

**FR-API-INF-005**: The system MUST provide `GET /v1/models` endpoint returning list of available models.

**FR-API-INF-006**: The system MUST support streaming responses via Server-Sent Events when `stream: true`.

**FR-API-INF-007**: The system MUST forward all OpenAI-compatible parameters to the backend server.

**FR-API-INF-008**: The system MAY add custom headers to track request routing (e.g., `X-Gateway-Server-ID`).

### 4.4 Request Routing (FR-ROUTE)

**FR-ROUTE-001**: When receiving an inference request, the system MUST:
1. Query registry for healthy servers hosting the requested model
2. If no healthy servers exist, return HTTP 503 with error message
3. If multiple healthy servers exist, select one using the configured load balancing strategy
4. Forward the request to the selected server
5. Return the server's response to the client

**FR-ROUTE-002**: The system MUST implement round-robin load balancing as the default strategy.

**FR-ROUTE-003**: The system MUST timeout requests after the configured timeout period (default: 300 seconds).

**FR-ROUTE-004**: If a forwarded request fails, the system MUST:
1. Mark the server as unhealthy
2. Retry with another healthy server (if available)
3. Maximum 2 retry attempts
4. Return HTTP 504 if all attempts fail

**FR-ROUTE-005**: The system MUST preserve the original request body when forwarding to backend servers.

**FR-ROUTE-006**: The system MUST include backend server's API key (if configured) when forwarding requests.

**FR-ROUTE-007**: The system SHOULD log routing decisions including selected server and latency.

### 4.5 Health Checking (FR-HEALTH)

**FR-HEALTH-001**: The system MUST run a background health checker service that operates independently of the API server.

**FR-HEALTH-002**: The health checker MUST check all registered servers at the configured interval:
- Default: Every 60 seconds
- Configurable range: 1-300 seconds

**FR-HEALTH-003**: For each health check, the system MUST:
1. Send GET request to `{server_url}/v1/models`
2. Wait up to 10 seconds for response
3. Verify response is HTTP 200 with valid JSON
4. Mark as healthy if check succeeds
5. Mark as unhealthy if check fails

**FR-HEALTH-004**: The system MUST track consecutive health check failures.

**FR-HEALTH-005**: The system MAY automatically deregister servers after 3 consecutive health check failures.

**FR-HEALTH-006**: The system MUST update `last_checked` timestamp after each health check.

**FR-HEALTH-007**: The system MUST log all health check results including:
- Server ID and URL
- Check timestamp
- Success/failure status
- Response time (if successful)
- Error details (if failed)

**FR-HEALTH-008**: The system SHOULD calculate and store health metrics:
- Success rate (last 100 checks)
- Average response time
- Uptime percentage
- Last transition timestamp (healthy ↔ unhealthy)

### 4.6 Error Handling (FR-ERROR)

**FR-ERROR-001**: The system MUST return appropriate HTTP status codes:
- 200: Success
- 400: Invalid request format
- 401: Authentication required
- 403: Forbidden (invalid API key)
- 404: Model not found (no servers registered)
- 500: Internal server error
- 503: Service unavailable (all servers unhealthy)
- 504: Gateway timeout

**FR-ERROR-002**: The system MUST return errors in OpenAI-compatible format:
```json
{
  "error": {
    "message": "Human-readable error message",
    "type": "error_type",
    "code": http_status_code
  }
}
```

**FR-ERROR-003**: The system MUST log all errors with:
- Timestamp
- Request ID
- Error type and message
- Full stack trace
- Request details (endpoint, parameters)

**FR-ERROR-004**: The system MUST NOT expose internal server details in error messages.

**FR-ERROR-005**: The system SHOULD provide actionable error messages (e.g., "Model 'llama-2' not found. Available models: [...]").

### 4.7 Logging (FR-LOG)

**FR-LOG-001**: The system MUST implement centralized logging for all components.

**FR-LOG-002**: The system MUST support the following log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL.

**FR-LOG-003**: The system MUST log to both file and console (configurable).

**FR-LOG-004**: Each log entry MUST include:
- Timestamp (ISO 8601 format)
- Log level
- Component name (api/health_checker/registry)
- Message
- Request ID (if applicable)

**FR-LOG-005**: The system MUST log the following events:
- Server registrations and deregistrations
- Health check results and status transitions
- Inference requests (model, latency, success/failure)
- Routing decisions (selected server)
- All errors and exceptions with stack traces
- Configuration changes
- System startup and shutdown

**FR-LOG-006**: The system MAY implement log rotation to prevent disk space issues.

**FR-LOG-007**: The system SHOULD redact sensitive information (API keys) in logs.

### 4.8 Web User Interface (FR-UI)

**FR-UI-001**: The system MUST provide a web-based user interface accessible via browser.

**FR-UI-002**: The web UI MUST be responsive and work on desktop, tablet, and mobile devices.

**FR-UI-003**: The web UI MUST follow modern design principles with intuitive navigation and clear visual hierarchy.

#### 4.8.1 Dashboard (Main View)

**FR-UI-DASH-001**: The system MUST provide a dashboard showing:
- Total number of registered servers
- Number of healthy vs unhealthy servers
- Number of unique models available
- Total inference requests handled (if tracked)
- Real-time system health status

**FR-UI-DASH-002**: The dashboard MUST display a list of all registered servers with:
- Model name
- Health status (with color coding: green=healthy, red=unhealthy, yellow=unknown)
- Endpoint URL (truncated with expand option)
- Last health check timestamp
- Response time (if available)
- Student ID / Owner

**FR-UI-DASH-003**: The dashboard MUST allow filtering servers by:
- Model name
- Health status
- Student ID

**FR-UI-DASH-004**: The dashboard MUST allow sorting servers by:
- Registration date
- Model name
- Health status
- Last check time

**FR-UI-DASH-005**: The dashboard MUST auto-refresh server status every 30 seconds without page reload.

#### 4.8.2 Server Registration Form

**FR-UI-REG-001**: The system MUST provide a registration form with fields for:
- Model name (required, text input)
- Endpoint URL (required, URL input with validation)
- API key (optional, password input)
- Max tokens (optional, number input)
- Context length (optional, number input)
- Streaming support (optional, checkbox, default: true)
- Student ID (optional, text input)
- Description (optional, textarea)

**FR-UI-REG-002**: The form MUST validate inputs client-side before submission:
- Model name: non-empty, alphanumeric with hyphens/underscores
- Endpoint URL: valid HTTP/HTTPS URL format
- Numeric fields: positive integers only

**FR-UI-REG-003**: The form MUST display real-time validation feedback with clear error messages.

**FR-UI-REG-004**: The form MUST show a loading indicator during submission.

**FR-UI-REG-005**: On successful registration, the form MUST:
- Display success message with registration ID
- Show a "Copy Registration ID" button
- Provide option to register another server
- Clear the form

**FR-UI-REG-006**: On registration failure, the form MUST display the specific error message returned by the API.

**FR-UI-REG-007**: The form MUST perform a test health check before submission with visual feedback.

#### 4.8.3 Server Details View

**FR-UI-DETAIL-001**: Clicking a server in the dashboard MUST open a detailed view showing:
- All server metadata
- Full endpoint URL (not truncated)
- Registration timestamp
- Last health check timestamp and result
- Health check history (last 20 checks) with timestamps and status
- Consecutive failure count
- Uptime percentage (if tracked)

**FR-UI-DETAIL-002**: The detail view MUST provide action buttons:
- "Edit Server" - opens edit form
- "Delete Server" - with confirmation dialog
- "Force Health Check" - manually triggers health check
- "Copy Endpoint URL" - copies URL to clipboard

**FR-UI-DETAIL-003**: The detail view MUST display health check history as a timeline or chart showing status changes over time.

#### 4.8.4 Server Edit Form

**FR-UI-EDIT-001**: The edit form MUST pre-populate all fields with current server values.

**FR-UI-EDIT-002**: The edit form MUST allow updating all mutable fields (everything except registration ID).

**FR-UI-EDIT-003**: The edit form MUST show which fields have been modified.

**FR-UI-EDIT-004**: The edit form MUST require confirmation before saving changes.

#### 4.8.5 Models View

**FR-UI-MODEL-001**: The system MUST provide a "Models" view listing all unique model names.

**FR-UI-MODEL-002**: For each model, the view MUST show:
- Model name
- Number of servers hosting this model
- Number of healthy servers
- Health percentage (healthy/total)
- List of servers (expandable)

**FR-UI-MODEL-003**: The models view MUST allow filtering and searching by model name.

#### 4.8.6 Inference Test Interface

**FR-UI-INF-001**: The system SHOULD provide a test interface for making inference requests.

**FR-UI-INF-002**: The test interface MUST include:
- Model selector (dropdown of available models)
- Message input (textarea for user message)
- System prompt input (optional textarea)
- Advanced options (temperature, max_tokens, etc.)
- "Send Request" button
- "Stream Response" toggle

**FR-UI-INF-003**: The test interface MUST display responses in real-time for streaming requests.

**FR-UI-INF-004**: The test interface MUST show request/response metadata:
- Selected server (which backend was used)
- Response time
- Token usage
- Any errors

#### 4.8.7 Logs View

**FR-UI-LOG-001**: The system SHOULD provide a logs viewer showing recent gateway activity.

**FR-UI-LOG-002**: The logs view MUST support filtering by:
- Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Component (api, health_checker, registry)
- Time range
- Search term

**FR-UI-LOG-003**: The logs view MUST display for each entry:
- Timestamp
- Log level (color-coded)
- Component
- Message
- Request ID (if applicable)

**FR-UI-LOG-004**: The logs view MUST support auto-refresh and "tail" mode for real-time monitoring.

#### 4.8.8 Settings/Configuration View

**FR-UI-CFG-001**: The system SHOULD provide a settings view displaying:
- Current configuration values (read-only)
- System information (Python version, FastAPI version, database path)
- Gateway uptime
- Database statistics (number of servers, health checks performed)

**FR-UI-CFG-002**: The settings view MAY allow modifying certain runtime configurations (health check interval, auto-deregister threshold).

#### 4.8.9 Navigation and Layout

**FR-UI-NAV-001**: The web UI MUST include a persistent navigation menu with links to:
- Dashboard (home)
- Register Server
- Models
- Test Inference (optional)
- Logs (optional)
- Settings

**FR-UI-NAV-002**: The navigation MUST indicate the current active page.

**FR-UI-NAV-003**: The UI MUST include a header showing:
- Application title "Multiverse Inference Gateway"
- Current API key status (authenticated/not authenticated)
- Quick stats (total servers, healthy count)

#### 4.8.10 Error Handling and User Feedback

**FR-UI-ERR-001**: The UI MUST display clear error messages for all API failures.

**FR-UI-ERR-002**: The UI MUST show loading states for all async operations.

**FR-UI-ERR-003**: The UI MUST use toast/notification system for:
- Success messages (green)
- Error messages (red)
- Warning messages (yellow)
- Info messages (blue)

**FR-UI-ERR-004**: The UI MUST handle network errors gracefully with retry options.

#### 4.8.11 API Integration

**FR-UI-API-001**: The web UI MUST communicate with the backend via the existing REST API endpoints.

**FR-UI-API-002**: The UI MUST include API key in request headers for admin endpoints.

**FR-UI-API-003**: The UI MUST handle API rate limiting (429 responses) gracefully.

**FR-UI-API-004**: The UI SHOULD implement request debouncing for search and filter operations.

## 5. Non-Functional Requirements

### 5.1 Performance

**NFR-PERF-001**: The gateway MUST add less than 100ms overhead to inference requests (P95 latency).

**NFR-PERF-002**: The system MUST support at least 100 concurrent inference requests without degradation.

**NFR-PERF-003**: The health checker MUST complete a full check cycle of all servers within 60 seconds (for ≤50 servers).

**NFR-PERF-004**: Database queries for finding healthy servers MUST complete within 10ms.

**NFR-PERF-005**: The system SHOULD handle at least 1000 inference requests per day.

**NFR-PERF-006**: The web UI MUST load initial page in less than 2 seconds on standard broadband connection.

**NFR-PERF-007**: The web UI MUST respond to user interactions within 100ms (excluding network requests).

**NFR-PERF-008**: The web UI MUST handle dashboard auto-refresh without blocking user interaction.

### 5.2 Reliability

**NFR-REL-001**: The gateway MUST achieve 99% uptime during operational hours.

**NFR-REL-002**: The system MUST handle backend server failures gracefully without crashing.

**NFR-REL-003**: The system MUST persist all registrations durably (zero data loss on restart).

**NFR-REL-004**: The system MUST automatically recover from transient failures (network timeouts, temporary database locks).

**NFR-REL-005**: The system SHOULD resume health checking automatically after restart.

### 5.3 Security

**NFR-SEC-001**: Admin endpoints MUST require API key authentication.

**NFR-SEC-002**: The system MUST validate and sanitize all input to prevent injection attacks.

**NFR-SEC-003**: The system MUST validate URLs to prevent SSRF (Server-Side Request Forgery) attacks.

**NFR-SEC-004**: The system SHOULD rate limit requests to prevent abuse (configurable, default: 60 requests/minute per IP).

**NFR-SEC-005**: The system MUST support HTTPS for backend server communication.

**NFR-SEC-006**: The system MAY allow disabling SSL certificate verification for development environments.

**NFR-SEC-007**: The system MUST NOT log API keys or sensitive authentication data.

### 5.4 Usability

**NFR-USE-001**: The system MUST provide OpenAPI/Swagger documentation at `/docs`.

**NFR-USE-002**: Error messages MUST be clear and actionable for students.

**NFR-USE-003**: The system MUST be installable with a single `pip install -r requirements.txt` command.

**NFR-USE-004**: Setup documentation MUST enable a new user to deploy the gateway in under 15 minutes.

**NFR-USE-005**: The system SHOULD provide example scripts for both hosting and using models.

**NFR-USE-006**: The web UI MUST be accessible and usable without training (intuitive design).

**NFR-USE-007**: The web UI MUST provide helpful tooltips and inline help text where needed.

**NFR-USE-008**: The web UI MUST work in modern browsers (Chrome, Firefox, Safari, Edge - latest 2 versions).

**NFR-USE-009**: The web UI MUST be fully functional without JavaScript errors in browser console.

**NFR-USE-010**: The web UI MUST achieve WCAG 2.1 Level AA accessibility compliance where feasible.

### 5.5 Maintainability

**NFR-MAINT-001**: The codebase MUST follow PEP 8 Python style guidelines.

**NFR-MAINT-002**: All functions and classes MUST include docstrings.

**NFR-MAINT-003**: The system MUST achieve at least 70% test coverage.

**NFR-MAINT-004**: The system MUST NOT use single-letter variable names.

**NFR-MAINT-005**: The system MUST use type hints throughout the codebase.

**NFR-MAINT-006**: Configuration MUST be externalized (environment variables, not hardcoded).

### 5.6 Scalability

**NFR-SCALE-001**: The system MUST support at least 50 registered model servers.

**NFR-SCALE-002**: The database schema MUST support multiple servers per model without performance degradation.

**NFR-SCALE-003**: The system SHOULD be designed to allow horizontal scaling (multiple gateway instances) in future phases.

### 5.7 Portability

**NFR-PORT-001**: The system MUST run on macOS, Linux, and Windows.

**NFR-PORT-002**: The system MUST work with Python 3.11+.

**NFR-PORT-003**: The system MUST NOT require Docker or containerization.

**NFR-PORT-004**: The system SHOULD minimize external dependencies.

## 6. Technical Requirements

### 6.1 Technology Stack

**TECH-001**: The system MUST use Python 3.11 as the programming language.

**TECH-002**: The system MUST use FastAPI as the web framework.

**TECH-003**: The system MUST use SQLite as the database (file-based, no separate server required).

**TECH-004**: The system MUST use `httpx` for async HTTP client requests.

**TECH-005**: The system MUST use Python's built-in `asyncio` for the health checker (no external task queue).

**TECH-006**: The system MUST use `uvicorn` as the ASGI server.

**TECH-007**: The system MAY use `pydantic` for data validation and settings management.

**TECH-008**: The system SHOULD minimize dependencies to essential packages only:
- `fastapi` - Web framework
- `uvicorn[standard]` - ASGI server
- `httpx` - Async HTTP client
- `pydantic` - Data validation
- `pydantic-settings` - Configuration management
- `python-dotenv` - Environment variable loading
- `aiosqlite` - Async SQLite support (or use SQLAlchemy with sqlite)

**TECH-009**: The system MUST NOT require:
- Docker or containerization
- PostgreSQL or external databases
- Redis or external caching
- Celery, RQ, or external task queues
- Message brokers (RabbitMQ, Kafka)

### 6.1.1 Frontend Stack

**TECH-UI-001**: The web UI SHOULD use modern, lightweight frontend technologies.

**TECH-UI-002**: Recommended frontend approach (in order of preference):
1. **Vanilla JavaScript with minimal dependencies** - For simplicity and no build step
2. **Alpine.js + Tailwind CSS** - For reactivity with minimal footprint
3. **Vue.js 3 + Tailwind CSS** - If more complex interactivity needed

**TECH-UI-003**: The web UI MUST be served as static files from FastAPI using `StaticFiles` and `Jinja2Templates` or similar.

**TECH-UI-004**: The web UI MUST use a CSS framework for consistent, responsive design:
- Recommended: Tailwind CSS (via CDN for simplicity)
- Alternative: Bootstrap 5, or custom CSS

**TECH-UI-005**: The web UI MAY use these additional libraries:
- Chart.js or similar for visualizations
- Axios or Fetch API for HTTP requests
- Day.js or similar for date formatting
- Clipboard.js for copy-to-clipboard functionality

**TECH-UI-006**: The web UI SHOULD minimize build tooling:
- Prefer CDN-served libraries over npm/webpack
- Use ES6 modules directly in browser where possible
- Avoid complex build pipelines unless necessary

**TECH-UI-007**: The frontend code MUST follow JavaScript best practices:
- Use `const` and `let` (no `var`)
- Use arrow functions and modern syntax
- Implement proper error handling
- Use async/await for asynchronous operations

### 6.2 Database Schema

**TECH-DB-001**: The system MUST implement the following database tables:

**Table: `model_servers`**
```sql
CREATE TABLE model_servers (
    id TEXT PRIMARY KEY,  -- UUID
    model_name TEXT NOT NULL,
    endpoint_url TEXT NOT NULL,
    api_key TEXT,
    max_tokens INTEGER,
    context_length INTEGER,
    streaming_supported BOOLEAN DEFAULT TRUE,
    student_id TEXT,
    description TEXT,
    registered_at TIMESTAMP NOT NULL,
    last_checked_at TIMESTAMP,
    health_status TEXT NOT NULL,  -- healthy/unhealthy/unknown
    consecutive_failures INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

CREATE INDEX idx_model_name ON model_servers(model_name);
CREATE INDEX idx_health_status ON model_servers(health_status);
CREATE INDEX idx_active ON model_servers(is_active);
```

**Table: `health_checks`** (optional, for historical tracking)
```sql
CREATE TABLE health_checks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    server_id TEXT NOT NULL,
    checked_at TIMESTAMP NOT NULL,
    status TEXT NOT NULL,  -- success/failure
    response_time_ms INTEGER,
    error_message TEXT,
    FOREIGN KEY (server_id) REFERENCES model_servers(id)
);

CREATE INDEX idx_server_id ON health_checks(server_id);
CREATE INDEX idx_checked_at ON health_checks(checked_at);
```

### 6.3 Configuration

**TECH-CFG-001**: The system MUST load configuration from environment variables.

**TECH-CFG-002**: The system MUST support `.env` file for local configuration.

**TECH-CFG-003**: Required configuration parameters:
```bash
# Server
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO  # DEBUG/INFO/WARNING/ERROR

# Database
DATABASE_URL=sqlite:///./multiverse.db

# Security
ADMIN_API_KEY=change-me-in-production

# Health Checker
HEALTH_CHECK_INTERVAL_SECONDS=60
HEALTH_CHECK_TIMEOUT_SECONDS=10
MAX_CONSECUTIVE_FAILURES=3

# Request Routing
REQUEST_TIMEOUT_SECONDS=300
MAX_RETRY_ATTEMPTS=2

# Optional Features
REQUIRE_CLIENT_AUTH=false
CLIENT_API_KEYS=  # Comma-separated if REQUIRE_CLIENT_AUTH=true
ENABLE_CORS=true
CORS_ORIGINS=*
```

### 6.4 Project Structure

**TECH-PROJ-001**: The system MUST follow this directory structure:
```
multiverse_inference_in_class/
├── .env                        # Configuration (not in git)
├── .gitignore
├── requirements.txt
├── README.md
├── plans/
│   ├── requirements.md         # This document
│   └── plan.md                # Implementation plan
├── devlog/                     # Development diary entries
├── app/
│   ├── __init__.py
│   ├── main.py                # FastAPI application entry point
│   ├── config.py              # Configuration management
│   ├── database.py            # Database connection and models
│   ├── models.py              # Pydantic models for API
│   ├── logging_config.py      # Centralized logging
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── inference.py       # /v1/* endpoints
│   │   ├── admin.py           # /admin/* endpoints
│   │   └── ui.py              # Web UI routes (serve HTML pages)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── registry.py        # Model registry operations
│   │   ├── router.py          # Request routing logic
│   │   └── health_checker.py # Background health checking
│   ├── utils/
│   │   ├── __init__.py
│   │   └── validation.py      # Input validation helpers
│   └── static/                # Frontend static files
│       ├── css/
│       │   └── styles.css     # Custom styles (if not using CDN only)
│       ├── js/
│       │   ├── api.js         # API client wrapper
│       │   ├── dashboard.js   # Dashboard page logic
│       │   ├── register.js    # Registration form logic
│       │   ├── models.js      # Models view logic
│       │   ├── test.js        # Inference test interface logic
│       │   └── common.js      # Shared utilities, notifications
│       └── img/               # Images, icons, logos
├── templates/                  # Jinja2 HTML templates
│   ├── base.html              # Base template with nav/header
│   ├── dashboard.html         # Main dashboard page
│   ├── register.html          # Server registration form
│   ├── detail.html            # Server detail view
│   ├── edit.html              # Server edit form
│   ├── models.html            # Models list view
│   ├── test.html              # Inference test interface
│   ├── logs.html              # Logs viewer (optional)
│   └── settings.html          # Settings view (optional)
├── deploy/                     # Deployment automation
│   ├── gce-setup.sh           # GCE instance initialization
│   ├── install.sh             # Install and configure
│   ├── update.sh              # Update deployment
│   ├── backup.sh              # Database backup script
│   ├── multiverse-gateway.service  # systemd service file
│   ├── nginx.conf             # nginx reverse proxy config
│   ├── Caddyfile              # Alternative: Caddy config
│   └── README.md              # Deployment guide
└── tests/
    ├── __init__.py
    ├── test_registry.py
    ├── test_routing.py
    ├── test_health_checker.py
    ├── test_api.py
    └── test_ui.py             # UI endpoint tests
```

### 6.5 Deployment

#### 6.5.1 Local Development Deployment

**TECH-DEPLOY-001**: The system MUST be runnable with a single command: `uvicorn app.main:app`

**TECH-DEPLOY-002**: The system MAY support running as a background process using: `nohup uvicorn app.main:app &`

**TECH-DEPLOY-003**: The system MUST initialize the database automatically on first startup.

**TECH-DEPLOY-004**: The system SHOULD provide a startup script that:
1. Activates virtual environment (if present)
2. Sources `.env` file
3. Starts uvicorn server

#### 6.5.2 Production Deployment (Google Compute Engine)

**TECH-DEPLOY-PROD-001**: The system MUST be deployable on Google Compute Engine (GCE).

**TECH-DEPLOY-PROD-002**: Recommended GCE instance specifications:
- **Machine type**: e2-micro (0.25-2 vCPU, 1 GB memory) for testing/small classes
- **Alternative**: e2-small (0.5-2 vCPU, 2 GB memory) for larger classes (30+ students)
- **Operating System**: Ubuntu 22.04 LTS or Ubuntu 24.04 LTS
- **Boot disk**: 10 GB standard persistent disk
- **Region**: us-central1 or closest to students
- **Network**: Allow HTTP (port 80) and HTTPS (port 443) traffic
- **Estimated cost**: ~$6-12/month for e2-micro, ~$15-25/month for e2-small

**TECH-DEPLOY-PROD-003**: The system MUST run as a systemd service for automatic startup and restart.

**TECH-DEPLOY-PROD-004**: The system MUST use a reverse proxy (nginx or Caddy) for:
- Serving on standard HTTP/HTTPS ports
- SSL/TLS certificate management (Let's Encrypt)
- Static file serving optimization
- Request logging

**TECH-DEPLOY-PROD-005**: The deployment SHOULD include:
- Automatic database backups (daily snapshot to GCS bucket)
- Log rotation configured
- Firewall rules limiting access to necessary ports
- Monitoring script checking service health

**TECH-DEPLOY-PROD-006**: The system MUST provide deployment automation scripts:
- `deploy/gce-setup.sh` - Initial GCE instance setup
- `deploy/install.sh` - Install dependencies and configure system
- `deploy/update.sh` - Update to new version without downtime
- `deploy/backup.sh` - Manual backup trigger

**TECH-DEPLOY-PROD-007**: Deployment steps MUST be documented for:
1. Creating GCE instance via console or gcloud CLI
2. SSH access configuration
3. Installing system dependencies (Python 3.11, nginx/Caddy, git)
4. Cloning repository
5. Configuring environment variables
6. Setting up systemd service
7. Configuring reverse proxy with SSL
8. Testing deployment
9. Monitoring and maintenance

**TECH-DEPLOY-PROD-008**: The system SHOULD support zero-downtime updates using:
- Graceful shutdown (existing requests complete)
- Health check endpoint for load balancer readiness
- Quick rollback capability (git checkout + service restart)

**TECH-DEPLOY-PROD-009**: Security hardening requirements:
- Non-root user for running the service
- Firewall configured (ufw or GCP firewall rules)
- SSH key-only authentication
- Automatic security updates enabled
- Rate limiting at reverse proxy level
- API key rotation documented

#### 6.5.3 Deployment Costs Estimation (GCE)

**e2-micro instance** (Recommended for small classes <20 students):
- Machine type: 0.25-2 vCPU (shared), 1 GB memory
- Cost: ~$6-8/month with sustained use discount
- Boot disk (10 GB): ~$2/month
- Egress (typical): ~$1-2/month
- **Total: ~$9-12/month**

**e2-small instance** (For larger classes 20-50 students):
- Machine type: 0.5-2 vCPU (shared), 2 GB memory
- Cost: ~$15-18/month with sustained use discount
- Boot disk (10 GB): ~$2/month
- Egress (typical): ~$2-5/month
- **Total: ~$19-25/month**

**Additional optional costs**:
- Domain name: ~$12/year (~$1/month)
- Cloud Storage for backups: ~$0.50-2/month
- Static IP address: ~$7/month (optional, use ephemeral IP to save cost)

**Cost optimization tips**:
- Use ephemeral external IP (free) instead of static IP
- Use Cloud Storage Standard for backups (cheapest tier)
- Enable preemptible instances for dev/test (not recommended for production)
- Use sustained use discounts (automatic with GCE)
- Monitor usage and right-size instance if needed

**Estimated total monthly cost: $10-27** depending on instance size and class usage.

## 7. Testing and Quality Assurance

### 7.1 Testing Strategy

**TEST-001**: The system MUST include integration tests rather than heavily mocked unit tests.

**TEST-002**: Tests MUST exercise real interactions between components.

**TEST-003**: External dependencies (actual student servers) MAY be mocked.

**TEST-004**: The system MUST achieve at least 70% code coverage.

### 7.2 Test Cases

**Test Category: Registration**
- **TC-REG-001**: Successfully register a new server with valid data
- **TC-REG-002**: Reject registration with invalid URL
- **TC-REG-003**: Reject registration without API key authentication
- **TC-REG-004**: Successfully deregister an existing server
- **TC-REG-005**: Return 404 when deregistering non-existent server
- **TC-REG-006**: Successfully update existing server details

**Test Category: Inference Routing**
- **TC-INF-001**: Successfully route request to healthy server
- **TC-INF-002**: Return 404 when requesting non-existent model
- **TC-INF-003**: Return 503 when all servers for model are unhealthy
- **TC-INF-004**: Failover to second server when first server fails
- **TC-INF-005**: Handle streaming responses correctly
- **TC-INF-006**: Timeout requests after configured duration
- **TC-INF-007**: Round-robin across multiple healthy servers

**Test Category: Health Checking**
- **TC-HEALTH-001**: Mark server as healthy when check succeeds
- **TC-HEALTH-002**: Mark server as unhealthy when check fails
- **TC-HEALTH-003**: Track consecutive failures correctly
- **TC-HEALTH-004**: Auto-deregister after N consecutive failures
- **TC-HEALTH-005**: Resume health checking after gateway restart

**Test Category: Error Handling**
- **TC-ERR-001**: Return proper error format for all error types
- **TC-ERR-002**: Handle malformed JSON in requests
- **TC-ERR-003**: Handle network errors from backend servers
- **TC-ERR-004**: Handle database connection failures

### 7.3 Performance Testing

**PERF-TEST-001**: Load test with 100 concurrent requests to verify throughput requirement.

**PERF-TEST-002**: Measure gateway latency overhead with simple echo server.

**PERF-TEST-003**: Test health checker performance with 50 registered servers.

### 7.4 Acceptance Criteria

The system is ready for release when:
- [ ] All functional requirements (FR-*) are implemented
- [ ] All test cases pass
- [ ] Code coverage ≥ 70%
- [ ] API documentation is complete and accurate
- [ ] Setup can be completed in < 15 minutes
- [ ] All success metrics from Section 2.3 are achievable

## 8. Implementation Phases

Each phase should be implementable in a single pull request and fit within one conversation context.

### Phase 1: Foundation
**Goal**: Basic infrastructure and database setup

**Tasks**:
- [ ] Set up project structure
- [ ] Configure logging module
- [ ] Create database models and connection
- [ ] Implement configuration management
- [ ] Create basic FastAPI app with health endpoint (`GET /health`)

**Deliverables**: Runnable FastAPI app with database

### Phase 2: Registration API
**Goal**: Allow servers to register

**Tasks**:
- [ ] Implement registration endpoint (`POST /admin/register`)
- [ ] Implement deregistration endpoint (`DELETE /admin/register/{id}`)
- [ ] Implement update endpoint (`PUT /admin/register/{id}`)
- [ ] Implement list endpoint (`GET /admin/servers`)
- [ ] Add API key authentication
- [ ] Add input validation

**Deliverables**: Functional admin API with tests

### Phase 3: Health Checker
**Goal**: Monitor registered servers

**Tasks**:
- [ ] Implement async health checker service
- [ ] Integrate with database to update health status
- [ ] Add configuration for check interval
- [ ] Implement consecutive failure tracking
- [ ] Add comprehensive logging

**Deliverables**: Background health checker with tests

### Phase 4: Inference Routing (Non-Streaming)
**Goal**: Route basic inference requests

**Tasks**:
- [ ] Implement `/v1/models` endpoint
- [ ] Implement `/v1/chat/completions` (non-streaming)
- [ ] Implement `/v1/completions` (non-streaming)
- [ ] Implement routing logic with round-robin
- [ ] Add retry logic with failover
- [ ] Implement OpenAI-compatible response formatting

**Deliverables**: Functional inference API with tests

### Phase 5: Streaming Support
**Goal**: Support streaming responses

**Tasks**:
- [ ] Implement SSE streaming for `/v1/chat/completions`
- [ ] Implement SSE streaming for `/v1/completions`
- [ ] Test with streaming backend servers
- [ ] Handle streaming errors gracefully

**Deliverables**: Streaming support with tests

### Phase 6: Web User Interface
**Goal**: Browser-based interface for server management and monitoring

**Tasks**:
- [ ] Set up FastAPI static file serving and Jinja2 templates
- [ ] Create base HTML template with navigation
- [ ] Implement dashboard view with server list
- [ ] Implement registration form with client-side validation
- [ ] Implement server detail and edit views
- [ ] Implement models list view
- [ ] Add auto-refresh functionality for real-time updates
- [ ] Implement inference test interface
- [ ] Add responsive CSS styling (mobile-friendly)
- [ ] Implement notification/toast system for user feedback

**Deliverables**: Fully functional web UI with all views

### Phase 7: Polish and Documentation
**Goal**: Production-ready system

**Tasks**:
- [ ] Add comprehensive error handling
- [ ] Improve logging coverage
- [ ] Write setup documentation
- [ ] Create example scripts for students
- [ ] Add API usage examples
- [ ] Performance testing and optimization
- [ ] UI/UX testing and refinement
- [ ] Accessibility compliance check

**Deliverables**: Production-ready system with documentation

## 9. Example Usage

### 9.1 Student Hosting a Model

**Step 1: Start your local model server**
```bash
# Example using vLLM or text-generation-webui
# Server running on http://localhost:8080
```

**Step 2: Expose via ngrok**
```bash
ngrok http 8080
# Public URL: https://abc123.ngrok.io
```

**Step 3: Register with gateway**
```python
import requests

response = requests.post(
    "http://gateway.example.com/admin/register",
    json={
        "model_name": "llama-2-7b",
        "endpoint_url": "https://abc123.ngrok.io",
        "capabilities": {
            "max_tokens": 4096,
            "context_length": 4096,
            "streaming": True
        },
        "metadata": {
            "student_id": "alice",
            "description": "Personal Llama 2 7B instance"
        }
    },
    headers={"X-API-Key": "shared-class-key"}
)

print(response.json())
# Output: {"registration_id": "550e8400-e29b-41d4-a716-446655440000", "status": "registered", "health_status": "healthy"}
```

### 9.2 Student Using a Model

**Using OpenAI Python Library**:
```python
from openai import OpenAI

# Point client to gateway
client = OpenAI(
    base_url="http://gateway.example.com/v1",
    api_key="not-needed"
)

# Use exactly like OpenAI API
response = client.chat.completions.create(
    model="llama-2-7b",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Explain quantum computing in simple terms."}
    ],
    temperature=0.7,
    max_tokens=200
)

print(response.choices[0].message.content)
```

**Streaming Example**:
```python
stream = client.chat.completions.create(
    model="llama-2-7b",
    messages=[{"role": "user", "content": "Tell me a story"}],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

**Using Raw HTTP**:
```python
import requests

response = requests.post(
    "http://gateway.example.com/v1/chat/completions",
    json={
        "model": "llama-2-7b",
        "messages": [{"role": "user", "content": "Hello!"}]
    }
)

print(response.json())
```

### 9.3 Checking Available Models

```python
import requests

response = requests.get("http://gateway.example.com/v1/models")
models = response.json()

for model in models["data"]:
    print(f"Model: {model['id']}, Servers: {model['available_servers']}")
```

### 9.4 Monitoring Server Status (Admin)

**Via API**:
```python
import requests

response = requests.get(
    "http://gateway.example.com/admin/servers",
    headers={"X-API-Key": "shared-class-key"}
)

for server in response.json():
    print(f"Model: {server['model_name']}")
    print(f"  Status: {server['health_status']}")
    print(f"  URL: {server['endpoint_url']}")
    print(f"  Last Check: {server['last_checked_at']}")
    print(f"  Student: {server['metadata']['student_id']}")
    print()
```

### 9.5 Using the Web Interface

**Accessing the Dashboard**:
1. Open browser and navigate to `http://gateway.example.com/`
2. View all registered servers with real-time health status
3. Use filters to find specific models or students
4. Click on any server to see detailed information

**Registering a Server via Web UI**:
1. Click "Register Server" in the navigation menu
2. Fill in the form:
   - Model name: `llama-2-7b`
   - Endpoint URL: `https://abc123.ngrok.io`
   - Student ID: `alice`
   - Description: `Personal Llama 2 7B instance`
3. Click "Test Connection" to verify server is reachable
4. Click "Register Server"
5. Copy the registration ID displayed on success

**Testing Inference via Web UI**:
1. Click "Test Inference" in the navigation menu
2. Select model from dropdown: `llama-2-7b`
3. Enter your prompt in the message box
4. Toggle "Stream Response" if desired
5. Click "Send Request"
6. View response in real-time
7. See metadata: which server handled request, response time, tokens used

**Monitoring Server Health**:
1. From dashboard, click on any server row
2. View detailed health history and statistics
3. Use "Force Health Check" button to manually trigger check
4. Use "Edit" button to update server configuration
5. Use "Delete" button to deregister server

### 9.6 Production Deployment on Google Compute Engine

**Step 1: Create GCE Instance**

Using gcloud CLI:
```bash
# Create e2-micro instance
gcloud compute instances create multiverse-gateway \
  --machine-type=e2-micro \
  --zone=us-central1-a \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=10GB \
  --boot-disk-type=pd-standard \
  --tags=http-server,https-server

# Configure firewall rules (if not already set)
gcloud compute firewall-rules create allow-http \
  --allow=tcp:80 \
  --target-tags=http-server

gcloud compute firewall-rules create allow-https \
  --allow=tcp:443 \
  --target-tags=https-server
```

**Step 2: SSH into Instance and Run Setup Script**
```bash
# SSH into instance
gcloud compute ssh multiverse-gateway --zone=us-central1-a

# On the instance, clone repository
git clone https://github.com/yourusername/multiverse_inference_in_class.git
cd multiverse_inference_in_class

# Run automated setup
sudo bash deploy/gce-setup.sh
bash deploy/install.sh

# Configure environment
cp .env.example .env
nano .env  # Edit configuration values

# Start service
sudo systemctl start multiverse-gateway
sudo systemctl enable multiverse-gateway

# Check status
sudo systemctl status multiverse-gateway
```

**Step 3: Configure Domain and SSL (Optional but Recommended)**
```bash
# Point your domain to the instance's external IP
# Then run Caddy for automatic HTTPS
sudo systemctl start caddy
sudo systemctl enable caddy

# Or configure nginx with certbot
sudo certbot --nginx -d gateway.yourdomain.com
```

**Step 4: Verify Deployment**
```bash
# Check service is running
curl http://localhost:8000/health

# Check through reverse proxy
curl http://your-instance-ip/health
# Or
curl https://gateway.yourdomain.com/health
```

**Step 5: Setup Monitoring and Backups**
```bash
# Enable daily backups (edit crontab)
crontab -e
# Add: 0 2 * * * /home/username/multiverse_inference_in_class/deploy/backup.sh

# Monitor logs
sudo journalctl -u multiverse-gateway -f

# View application logs
tail -f logs/gateway.log
```

**Common Management Tasks**:
```bash
# Restart service
sudo systemctl restart multiverse-gateway

# Update to latest version
bash deploy/update.sh

# View logs
sudo journalctl -u multiverse-gateway --since "1 hour ago"

# Backup database manually
bash deploy/backup.sh

# Check service status
sudo systemctl status multiverse-gateway
```

## 10. Future Enhancements (Out of Scope for Initial Release)

The following features are explicitly out of scope for the initial implementation but may be added in future versions:

- **Advanced Load Balancing**: Latency-based or load-based routing
- **Request Queuing**: Queue requests when servers are at capacity
- **Multi-tenancy**: Separate model namespaces per class
- **Cost Tracking**: Track token usage per student
- **Model Versioning**: Support multiple versions of same model
- **Webhooks**: Notify on server status changes
- **Analytics**: Usage statistics and popular models dashboard
- **Rate Limiting Per Student**: Individual quotas
- **A/B Testing**: Route percentage of requests to specific servers
- **PostgreSQL Support**: For larger deployments
- **Metrics Export**: Prometheus/Grafana integration

## 11. Success Criteria and Launch Readiness

The system is considered ready for classroom use when:

- [ ] All Phase 1-7 requirements implemented and tested
- [ ] At least 3 students successfully register test servers (via API or Web UI)
- [ ] At least 3 students successfully make inference requests (via API or Web UI)
- [ ] Health checker detects and marks server failures within 60 seconds
- [ ] Gateway handles 10 concurrent requests without errors
- [ ] API documentation is complete and accessible at `/docs`
- [ ] Web UI is functional, responsive, and user-friendly
- [ ] Web UI successfully tested on Chrome, Firefox, and Safari
- [ ] Students can complete registration via Web UI in < 5 minutes
- [ ] Setup documentation enables new user deployment in < 15 minutes
- [ ] All P0 bugs resolved
- [ ] Code review completed by instructor/TA

## 12. Risks and Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Student servers frequently go offline | High | High | Implement robust health checking and failover |
| Ngrok tunnels change URLs on restart | Medium | High | Provide easy update endpoint; document re-registration process |
| Gateway becomes single point of failure | High | Medium | Design for easy restart; use simple deployment |
| Malicious requests to backend servers | Medium | Medium | Implement rate limiting and input validation |
| Database corruption | High | Low | Use SQLite with WAL mode; implement backups |
| Students share API keys publicly | Low | Medium | Document security best practices; rotate keys |

## 13. Glossary

- **Backend Server**: A student-hosted server running an AI model
- **Failover**: Automatic switching to alternative server when primary fails
- **Gateway**: This system - the central routing service
- **Health Check**: Automated test to verify a server is responding
- **Load Balancing**: Distributing requests across multiple servers
- **Model Registry**: Database of available models and their servers
- **Round-Robin**: Load balancing strategy that cycles through servers in order
- **SSE (Server-Sent Events)**: Protocol for server-to-client streaming over HTTP
- **SSRF (Server-Side Request Forgery)**: Attack where attacker tricks server into making requests to unintended destinations

## Appendix A: Minimal Dependencies Justification

To align with the requirement for minimal dependencies, the following packages are essential and justified:

1. **fastapi** (Required) - Core web framework
2. **uvicorn[standard]** (Required) - ASGI server to run FastAPI
3. **httpx** (Required) - Async HTTP client for forwarding requests
4. **pydantic** (Required) - Data validation, included with FastAPI
5. **pydantic-settings** (Optional but recommended) - Configuration management
6. **python-dotenv** (Optional but recommended) - Load `.env` files
7. **aiosqlite** (Optional) - Async SQLite support if using raw SQL

**Explicitly NOT using**:
- sqlalchemy - Unless needed for complex queries; raw SQL is sufficient
- celery/rq - Using built-in asyncio instead
- redis - No caching needed initially
- docker - Per requirements
- pytest - Use built-in unittest if desired
- requests - Using httpx for consistency (async)

Total essential dependencies: **3-4 packages**

## Appendix B: Security Considerations

### URL Validation
To prevent SSRF attacks, the system MUST validate registered URLs:
- Reject private IP ranges (127.0.0.1, 10.x.x.x, 192.168.x.x, 172.16-31.x.x)
- Reject localhost and internal hostnames
- Only allow http:// and https:// schemes
- Validate URL format before making requests

### API Key Management
- Store API keys as environment variables
- Never log API keys
- Use secure random generation for keys
- Document key rotation process

### Input Validation
- Validate all JSON inputs against Pydantic models
- Limit request body size (e.g., 1MB max)
- Sanitize string inputs
- Validate numeric ranges
