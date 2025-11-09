# Engineering Implementation Plan - Multiverse Inference System

## 1. Feature Deconstruction

### Implementation Summary
Build a distributed AI inference gateway that enables students to share and access AI models hosted on their own servers through a unified OpenAI-compatible API. The system acts as a routing layer that manages model server registration, performs continuous health monitoring, and routes inference requests to healthy backend servers with automatic failover.

### User Stories & Acceptance Criteria

#### US-001: Register Model Server (FR-API-REG-001 through FR-API-REG-010)
**As a** student hosting a model  
**I want to** register my server with the gateway  
**So that** other students can use my model through the unified API

**Acceptance Criteria**:
- [ ] Can POST to `/admin/register` with model details
- [ ] Registration completes in under 5 minutes
- [ ] System validates the server URL before accepting registration
- [ ] Receive unique registration ID upon success
- [ ] System performs initial health check immediately after registration
- [ ] Can update registration with PUT endpoint
- [ ] Can deregister with DELETE endpoint
- [ ] API key authentication required for all admin endpoints

#### US-002: Request Inference (FR-API-INF-001 through FR-API-INF-008)
**As a** student using models  
**I want to** send inference requests using the OpenAI Python library  
**So that** I can use familiar tools without learning new APIs

**Acceptance Criteria**:
- [ ] Can use `openai.ChatCompletion.create()` without modifications
- [ ] Receive responses in standard OpenAI format
- [ ] Support for both streaming and non-streaming responses
- [ ] Get clear error message if requested model is unavailable
- [ ] Requests automatically route to healthy servers
- [ ] Automatic retry with failover if selected server fails

#### US-003: Monitor Server Health (FR-HEALTH-001 through FR-HEALTH-008)
**As a** student hosting a model  
**I want to** see when my server is marked as unhealthy  
**So that** I can fix issues and restore service

**Acceptance Criteria**:
- [ ] Can query `/admin/servers` to see my server's health status
- [ ] Health status updated within 60 seconds of failure
- [ ] Logs show specific reason for health check failure
- [ ] Background health checker runs independently
- [ ] Consecutive failures tracked appropriately
- [ ] Health metrics visible in server listing

#### US-004: Deregister Server (FR-API-REG-007)
**As a** student hosting a model  
**I want to** remove my server from the registry  
**So that** requests stop being routed to it when I shut down

**Acceptance Criteria**:
- [ ] Deregistration completes immediately
- [ ] No new requests routed after deregistration
- [ ] Can re-register same server later

#### US-005: List Available Models (FR-API-INF-005)
**As a** student using models  
**I want to** see which models are currently available  
**So that** I know which models I can request

**Acceptance Criteria**:
- [ ] Can call `/v1/models` endpoint
- [ ] Response shows model names and count of healthy servers
- [ ] Response format matches OpenAI API specification

#### US-006: View Server Dashboard (FR-UI-DASH-*)
**As a** student or instructor  
**I want to** see a visual dashboard of all registered servers  
**So that** I can quickly assess system health and server status

**Acceptance Criteria**:
- [ ] Can access web dashboard via browser
- [ ] Dashboard shows real-time health status of all servers
- [ ] Can filter and sort servers
- [ ] Dashboard auto-refreshes without page reload
- [ ] Mobile-responsive design works on phone/tablet

#### US-007: Register Server via Web Form (FR-UI-REG-*)
**As a** student hosting a model  
**I want to** register my server using a web form  
**So that** I don't need to write code or use curl commands

**Acceptance Criteria**:
- [ ] Can access registration form via web UI
- [ ] Form validates inputs in real-time
- [ ] Receive immediate feedback on registration success/failure
- [ ] Can copy registration ID easily
- [ ] Form is intuitive and completes in under 5 minutes

#### US-008: Test Inference via Web UI (FR-UI-INF-*)
**As a** student using models  
**I want to** test inference requests through the web interface  
**So that** I can verify models work before integrating into my code

**Acceptance Criteria**:
- [ ] Can select available models from dropdown
- [ ] Can enter prompts and see responses
- [ ] Can test streaming responses in real-time
- [ ] See which backend server handled the request
- [ ] View response time and token usage

### Overall Success Metrics
- **Registration Time**: Average time to register a new server < 5 minutes
- **Uptime**: Gateway availability > 99%
- **Request Success Rate**: > 95% of requests successfully routed to healthy servers
- **Detection Speed**: Server failures detected within 60 seconds
- **Concurrent Users**: Support at least 10 concurrent inference requests
- **Adoption**: At least 50% of students successfully host or use models

### Overall Definition of Done
- [ ] All functional requirements (FR-*) implemented including Web UI
- [ ] All test cases pass with ≥70% code coverage
- [ ] API documentation complete and accessible at `/docs`
- [ ] Web UI is functional, responsive, and user-friendly
- [ ] Web UI successfully tested on Chrome, Firefox, and Safari
- [ ] Setup documentation enables deployment in < 15 minutes
- [ ] 3+ students successfully register test servers (via API or Web UI)
- [ ] 3+ students successfully make inference requests (via API or Web UI)
- [ ] Students can complete registration via Web UI in < 5 minutes
- [ ] Gateway handles 10 concurrent requests without errors
- [ ] Health checker detects failures within 60 seconds
- [ ] Code follows PEP 8 with type hints and docstrings

---

## 2. Technical Scope

### Affected Systems/Components
**New Systems (To Be Created)**:
- FastAPI application server (gateway)
- SQLite database for model registry
- Background health checker service
- Admin API endpoints (`/admin/*`)
- Inference API endpoints (`/v1/*`)
- Web UI routes and pages (`/`, `/dashboard`, `/register`, etc.)
- Request routing service
- Centralized logging system
- Configuration management system
- Frontend static files (HTML, CSS, JavaScript)
- Jinja2 templates for server-side rendering

**External Systems (Dependencies)**:
- Student-hosted model servers (ngrok tunnels)
- OpenAI API specification (compatibility target)
- CDN-hosted frontend libraries (Tailwind CSS, Chart.js, etc.)

### Dependency Map

**Internal APIs**:
- Registry Service: CRUD operations on model_servers table
- Routing Service: Query healthy servers, select via round-robin
- Health Checker Service: Async background task updating server health status
- Validation Utils: URL validation, input sanitization

**External Services**:
- Student backend servers: OpenAI-compatible `/v1/models`, `/v1/chat/completions`, `/v1/completions` endpoints
- Ngrok or similar tunneling services (student-provided)

**Libraries/SDKs**:

Backend (Python):
- `fastapi` - Web framework (required)
- `uvicorn[standard]` - ASGI server (required)
- `httpx` - Async HTTP client (required)
- `pydantic` - Data validation (required, included with FastAPI)
- `pydantic-settings` - Configuration management (recommended)
- `python-dotenv` - Environment variable loading (recommended)
- `aiosqlite` - Async SQLite support (optional, or use raw sqlite3)
- `jinja2` - HTML templating (required for Web UI)

Frontend (JavaScript/CSS via CDN):
- Tailwind CSS - Responsive styling framework
- Alpine.js or vanilla JavaScript - Frontend interactivity
- Chart.js - Health history visualization (optional)
- Day.js - Date formatting (optional)

### Architectural Notes & Decisions

**Architecture Pattern**: Monolithic application with separation of concerns
- Single FastAPI application serving both API and Web UI
- Modular structure with routers, services, and utilities
- Background task for health checking (asyncio.create_task)
- Server-side rendering with Jinja2 templates
- Static file serving for CSS, JavaScript, and images

**Database Design**:
- SQLite with WAL mode for concurrent access
- Single `model_servers` table (primary)
- Optional `health_checks` table for historical tracking (Phase 6)
- Indexes on `model_name`, `health_status`, `is_active`

**Async Design**:
- FastAPI async endpoints for all request handlers
- `httpx.AsyncClient` for backend server communication
- `asyncio` background task for health checker
- No external task queue (Celery/RQ) - keep it simple

**API Compatibility**:
- Strict adherence to OpenAI API format for inference endpoints
- Custom admin endpoints for registration/management
- OpenAPI/Swagger docs auto-generated by FastAPI

**Load Balancing**:
- Phase 1-4: Simple round-robin (in-memory counter)
- Future: Could add latency-based or weighted algorithms

**Security Model**:
- API key authentication for admin endpoints (X-API-Key header)
- Optional API key for client inference endpoints
- URL validation to prevent SSRF attacks
- Input validation via Pydantic models

---

## 3. Risk & Requirements

### RAID Log

#### Risks
- **HIGH**: Ngrok tunnels change URLs on restart (80% probability)
  - *Mitigation*: Easy update endpoint, clear documentation, consider stable URLs
- **HIGH**: Health check false positives from transient network issues (60% probability)
  - *Mitigation*: Require 3 consecutive failures, longer timeouts, exponential backoff
- **MEDIUM**: Backend API incompatibility with OpenAI spec (50% probability)
  - *Mitigation*: Document requirements, provide test script, validate responses
- **MEDIUM**: Database corruption losing all registrations (10% probability, high impact)
  - *Mitigation*: SQLite WAL mode, automated backups, export/import capability
- **MEDIUM**: Gateway as single point of failure (30% probability)
  - *Mitigation*: Simple deployment for fast restart, process monitoring, documentation
- **LOW**: Malicious registrations (20% probability)
  - *Mitigation*: API key auth, URL validation, rate limiting

#### Assumptions
- Students can maintain ngrok tunnels or similar public endpoints
- Student servers will implement OpenAI-compatible API format
- Python 3.11+ available in deployment environment
- No Docker required (per requirements)
- SQLite sufficient for initial deployment (<50 servers)
- Students have basic knowledge of REST APIs and Python
- Instructor will provide shared API key for admin endpoints

#### Issues
- None identified at planning stage

#### Dependencies
- **Hard Dependencies**:
  - Python 3.11+ runtime environment
  - Virtual environment for dependency isolation
  - Network access to student servers
  - File system write access for SQLite database
- **Soft Dependencies**:
  - `.env` file for configuration (can use env vars directly)
  - Process supervisor for production (systemd, supervisor, or manual restart)

### Non-Functional Requirements (NFRs)

#### Performance (NFR-PERF-*)
- Gateway overhead < 100ms (P95 latency) - **NFR-PERF-001**
- Support ≥100 concurrent requests - **NFR-PERF-002**
- Health checker completes full cycle within 60s for ≤50 servers - **NFR-PERF-003**
- Database queries < 10ms - **NFR-PERF-004**
- Handle ≥1000 requests/day - **NFR-PERF-005**

#### Security (NFR-SEC-*)
- API key authentication for admin endpoints - **NFR-SEC-001**
- Input validation and sanitization - **NFR-SEC-002**
- URL validation to prevent SSRF - **NFR-SEC-003**
- Rate limiting (60 req/min per IP) - **NFR-SEC-004**
- HTTPS support for backend communication - **NFR-SEC-005**
- No logging of API keys - **NFR-SEC-007**

#### Scalability (NFR-SCALE-*)
- Support ≥50 registered servers - **NFR-SCALE-001**
- Multiple servers per model without degradation - **NFR-SCALE-002**
- Design for horizontal scaling (future) - **NFR-SCALE-003**

#### Observability
- Centralized logging with DEBUG/INFO/WARNING/ERROR/CRITICAL levels - **FR-LOG-001, FR-LOG-002**
- Log to file and console - **FR-LOG-003**
- Structured log entries with timestamp, level, component, message, request ID - **FR-LOG-004**
- Comprehensive event logging (registrations, health checks, requests, errors) - **FR-LOG-005**

---

## 4. Phased Execution Plan

### Phase 1: Foundation & Infrastructure

**Phase Goal**: Establish core infrastructure, database, logging, and configuration management to support all future features.

**Key Tasks**:
- [x] Set up project directory structure per **TECH-PROJ-001**
  - Create `app/`, `tests/`, `plans/`, `devlog/` directories
  - Set up module structure: `routers/`, `services/`, `utils/`
- [x] Create `requirements.txt` with minimal dependencies per **TECH-008**
- [x] Implement centralized logging module per **FR-LOG-001** through **FR-LOG-007**
  - Support DEBUG/INFO/WARNING/ERROR/CRITICAL levels
  - Log to file and console with rotation
  - Structured format with timestamps, component names, request IDs
- [x] Implement configuration management per **TECH-CFG-001** through **TECH-CFG-003**
  - Use `pydantic-settings` for settings model
  - Load from `.env` file with `python-dotenv`
  - Define all required config parameters
- [x] Create database schema per **TECH-DB-001**
  - Implement `model_servers` table with indexes
  - Set up SQLite connection with WAL mode per risk mitigation
  - Create database initialization function
- [x] Create basic FastAPI application in `app/main.py` per **TECH-DEPLOY-001**
  - Initialize FastAPI app with CORS middleware
  - Set up logging on startup
  - Initialize database on startup
  - Add `GET /health` endpoint for gateway health check
- [x] Write `.gitignore` to exclude `.env`, `*.db`, `__pycache__`, etc.
- [x] Create sample `.env.example` file with all config parameters documented

**Effort Estimate**: M (Medium complexity, foundational work)

**Definition of Done**:
- [x] Project structure matches **TECH-PROJ-001** specification
- [x] `uvicorn app.main:app` runs successfully
- [x] `GET /health` endpoint returns 200 OK
- [x] Logging outputs to both console and file
- [x] Configuration loads from `.env` file
- [x] Database file created with correct schema
- [x] All code has type hints and docstrings per **NFR-MAINT-002**, **NFR-MAINT-005**
- [x] Code follows PEP 8 per **NFR-MAINT-001**
- [x] No single-letter variable names per **NFR-MAINT-004**
- [x] README.md created with setup instructions

---

### Phase 2: Admin API - Server Registration

**Phase Goal**: Implement registration, deregistration, and management endpoints for student servers to join the gateway.

**Key Tasks**:
- [x] Create Pydantic models for registration API per **FR-API-REG-001**
  - `RegisterServerRequest` model
  - `RegisterServerResponse` model
  - `ServerListItem` model
- [x] Implement Registry Service in `app/services/registry.py`
  - `register_server()` - Insert new server record per **FR-REG-001**, **FR-REG-002**
  - `deregister_server()` - Soft delete or hard delete
  - `update_server()` - Update server details
  - `list_servers()` - Query all servers with filtering
  - `get_server_by_id()` - Fetch single server
  - `find_healthy_servers()` - Query by model name and health status
- [x] Implement URL validation utility per **NFR-SEC-003**, Appendix B
  - Validate HTTP/HTTPS scheme only
  - Reject private IP ranges (127.0.0.1, 10.x, 192.168.x, 172.16-31.x)
  - Reject localhost and internal hostnames
- [x] Implement initial health check function (simple)
  - Send GET to `{endpoint_url}/v1/models`
  - 10 second timeout
  - Return healthy/unhealthy status
- [x] Create admin router in `app/routers/admin.py`
  - `POST /admin/register` per **FR-API-REG-001** through **FR-API-REG-006**
  - `DELETE /admin/register/{registration_id}` per **FR-API-REG-007**
  - `PUT /admin/register/{registration_id}` per **FR-API-REG-008**
  - `GET /admin/servers` per **FR-API-REG-009**
- [x] Implement API key authentication dependency per **FR-API-REG-010**, **NFR-SEC-001**
  - Check `X-API-Key` header against configured `ADMIN_API_KEY`
  - Return 403 if invalid or missing
- [x] Add comprehensive error handling per **FR-ERROR-001** through **FR-ERROR-005**
  - 400 for invalid input
  - 403 for invalid API key
  - 404 for non-existent server
  - 503 if initial health check fails
  - OpenAI-compatible error format
- [x] Add logging for all registration events per **FR-LOG-005**
- [x] Write integration tests
  - Test successful registration
  - Test registration with invalid URL (TC-REG-002)
  - Test registration without API key (TC-REG-003)
  - Test deregistration (TC-REG-004)
  - Test update endpoint (TC-REG-006)

**Effort Estimate**: M (Medium complexity, CRUD operations with validation)

**Definition of Done**:
- [x] All admin endpoints functional and documented in `/docs`
- [x] API key authentication enforced on all admin endpoints
- [x] URL validation prevents SSRF attacks
- [x] Initial health check runs before accepting registration
- [x] Appropriate HTTP status codes returned per **FR-ERROR-001**
- [x] Errors in OpenAI-compatible format per **FR-ERROR-002**
- [x] All registration events logged
- [x] Integration tests pass with ≥70% coverage
- [x] Can successfully register a test server in < 5 minutes (manual test)
- [x] PR merged to main branch

---

### Phase 3: Inference API - Request Routing (Non-Streaming)

**Phase Goal**: Implement OpenAI-compatible inference endpoints with request routing, round-robin load balancing, and automatic failover.

**Key Tasks**:
- [x] Create Pydantic models for inference API per **FR-API-INF-002**, **FR-API-INF-003**
  - `ChatCompletionRequest` model
  - `ChatCompletionResponse` model
  - `CompletionRequest` model
  - `CompletionResponse` model
  - `ModelListResponse` model
  - Match OpenAI API specification exactly
- [x] Implement Router Service in `app/services/router.py`
  - `select_server()` - Round-robin load balancing per **FR-ROUTE-002**
  - `forward_request()` - Proxy request to backend server per **FR-ROUTE-005**
  - `handle_request()` - Main routing logic per **FR-ROUTE-001**
- [x] Implement round-robin load balancer
  - Track last-used index per model name (in-memory dict)
  - Cycle through healthy servers
  - Thread-safe counter increment
- [x] Implement request forwarding with `httpx.AsyncClient`
  - Forward all OpenAI-compatible parameters per **FR-API-INF-007**
  - Include backend server's API key if configured per **FR-ROUTE-006**
  - Set timeout per **FR-ROUTE-003** (default 300s)
  - Handle both success and error responses
- [x] Implement retry logic with failover per **FR-ROUTE-004**
  - If request fails, mark server as unhealthy
  - Retry with next available healthy server
  - Maximum 2 retry attempts
  - Return 504 if all attempts exhausted
- [x] Create inference router in `app/routers/inference.py`
  - `GET /v1/models` per **FR-API-INF-005**
  - `POST /v1/chat/completions` (non-streaming only) per **FR-API-INF-001**
  - `POST /v1/completions` (non-streaming only) per **FR-API-INF-004**
- [x] Implement `/v1/models` endpoint
  - Query registry for all active servers
  - Group by model name
  - Count healthy servers per model
  - Return OpenAI-compatible list format
- [x] Implement `/v1/chat/completions` endpoint (non-streaming)
  - Accept OpenAI-compatible request
  - Query healthy servers for requested model
  - Return 404 if no servers registered per **FR-ERROR-001**
  - Return 503 if all servers unhealthy per **FR-ERROR-001**
  - Route to selected server
  - Return OpenAI-compatible response
- [x] Implement `/v1/completions` endpoint (non-streaming)
  - Similar logic to chat completions
- [x] Add comprehensive logging per **FR-LOG-005**
  - Log routing decisions (which server selected)
  - Log request latency
  - Log retry attempts
  - Log failures
- [x] Add optional `X-Gateway-Server-ID` response header per **FR-API-INF-008**
- [x] Write integration tests
  - Test routing to healthy server (TC-INF-001)
  - Test 404 for non-existent model (TC-INF-002)
  - Test 503 when all servers unhealthy (TC-INF-003)
  - Test failover to second server (TC-INF-004)
  - Test round-robin distribution (TC-INF-007)
  - Test timeout behavior (TC-INF-006)

**Effort Estimate**: M (Medium-high complexity, core routing logic)

**Definition of Done**:
- [x] All inference endpoints functional and documented in `/docs`
- [x] OpenAI Python library can successfully make requests
- [x] Round-robin load balancing working correctly
- [x] Automatic failover on server failure
- [x] Appropriate error codes (404, 503, 504) returned
- [x] Request/response format matches OpenAI specification exactly
- [x] Routing decisions logged with latency metrics
- [x] Integration tests pass with ≥70% coverage
- [ ] Manual test: 3 students successfully make inference requests using OpenAI library
- [ ] Gateway overhead < 100ms measured with echo server
- [x] PR merged to main branch

---

### Phase 4: Background Health Checker

**Phase Goal**: Implement continuous background health monitoring with configurable check intervals and automatic status updates.

**Key Tasks**:
- [x] Implement Health Checker Service in `app/services/health_checker.py`
  - `check_server_health()` - Perform single health check per **FR-HEALTH-003**
  - `health_check_loop()` - Continuous async loop per **FR-HEALTH-001**
  - `update_health_status()` - Update database with results
- [x] Implement health check logic per **FR-HEALTH-003**
  - Send GET request to `{server_url}/v1/models`
  - 10 second timeout per **HEALTH_CHECK_TIMEOUT_SECONDS**
  - Expect HTTP 200 with valid JSON
  - Mark healthy on success, unhealthy on failure
- [x] Implement consecutive failure tracking per **FR-HEALTH-004**
  - Increment `consecutive_failures` on each failure
  - Reset to 0 on success
  - Track in `model_servers` table
- [x] Implement auto-deregistration logic per **FR-HEALTH-005**
  - Deregister (soft delete) after N consecutive failures
  - N configurable via `MAX_CONSECUTIVE_FAILURES` (default 3)
- [x] Implement health check scheduling per **FR-HEALTH-002**
  - Configurable interval via `HEALTH_CHECK_INTERVAL_SECONDS` (default 60)
  - Use `asyncio.sleep()` between cycles
  - Check all active servers each cycle
- [x] Update `last_checked_at` timestamp per **FR-HEALTH-006**
- [x] Add comprehensive health check logging per **FR-HEALTH-007**
  - Log each check result (server ID, URL, status, response time)
  - Log status transitions (healthy→unhealthy, unhealthy→healthy)
  - Log auto-deregistrations
  - Include error details on failures
- [x] Start health checker on application startup
  - Use `@app.on_event("startup")` in `main.py`
  - Launch as background task with `asyncio.create_task()`
- [x] Implement graceful shutdown on application exit
  - Use `@app.on_event("shutdown")`
  - Cancel health checker task
- [ ] Add health metrics calculation per **FR-HEALTH-008** (optional, nice-to-have)
  - Calculate success rate
  - Track average response time
  - Store in memory or separate table
- [x] Write integration tests
  - Test healthy server marked as healthy (TC-HEALTH-001)
  - Test unhealthy server marked as unhealthy (TC-HEALTH-002)
  - Test consecutive failure tracking (TC-HEALTH-003)
  - Test auto-deregistration after N failures (TC-HEALTH-004)
  - Test health checker resumes after gateway restart (TC-HEALTH-005)

**Effort Estimate**: M (Medium complexity, async background task)

**Definition of Done**:
- [x] Health checker runs continuously in background
- [x] All active servers checked at configured interval
- [x] Server health status updated in database
- [x] Consecutive failures tracked correctly
- [x] Auto-deregistration after N failures working
- [x] Status transitions logged with detailed information
- [x] Health checker starts on app startup per **NFR-REL-005**
- [x] Health checker shuts down gracefully
- [x] Integration tests pass with ≥70% coverage
- [x] Manual test: Simulate server failure, verify detection within 60 seconds
- [x] PR merged to main branch

---

### Phase 5: Streaming Support via SSE

**Phase Goal**: Add Server-Sent Events streaming support for real-time inference responses.

**Key Tasks**:
- [x] Update inference endpoints to handle `stream: true` parameter
  - Modify `POST /v1/chat/completions` per **FR-API-INF-006**
  - Modify `POST /v1/completions` per **FR-API-INF-006**
- [x] Implement streaming response proxy in Router Service
  - Detect `stream: true` in request
  - Forward request to backend with streaming enabled
  - Stream response chunks back to client
  - Use FastAPI `StreamingResponse` class
- [x] Implement SSE format per specification
  - Format: `data: {JSON}\n\n` per SSE spec (reference 1.4)
  - Each chunk is a complete SSE event
  - Send `data: [DONE]\n\n` at end of stream
- [x] Handle streaming errors gracefully
  - If backend connection drops mid-stream, log error
  - Close client connection cleanly
  - Mark server as unhealthy if streaming fails
- [x] Update request forwarding to use `httpx` streaming
  - Use `httpx.AsyncClient.stream()` method
  - Async iterate over response chunks
  - Forward each chunk to client immediately
- [x] Add streaming-specific logging
  - Log when streaming starts
  - Log chunk count and total bytes transferred
  - Log streaming completion or errors
- [x] Update Pydantic models for streaming responses
  - Add streaming response chunk models
  - Match OpenAI streaming format exactly
- [x] Write integration tests
  - Test streaming chat completions (TC-INF-005)
  - Test streaming completions
  - Test streaming with multiple chunks
  - Test streaming error handling (connection drop)
  - Test non-streaming requests still work

**Effort Estimate**: M (Medium complexity, streaming proxy logic)

**Definition of Done**:
- [x] Streaming responses work with OpenAI Python library
- [x] SSE format matches specification
- [x] Streaming errors handled gracefully
- [x] Both streaming and non-streaming modes work
- [x] Streaming-specific events logged
- [x] Integration tests pass with ≥70% coverage
- [ ] Manual test: Stream a long response and verify real-time display
- [ ] PR merged to main branch

---

### Phase 6: Web User Interface

**Phase Goal**: Implement browser-based interface for server management, monitoring, and testing with modern, responsive design.

**Key Tasks**:
- [ ] Set up static file serving and Jinja2 templates in FastAPI per **TECH-UI-003**
  - Configure `StaticFiles` mount for `/static` directory
  - Configure `Jinja2Templates` for HTML templates
  - Add `jinja2` to requirements.txt
- [ ] Create UI router in `app/routers/ui.py`
  - `GET /` - Redirect to dashboard or serve landing page
  - `GET /dashboard` - Serve dashboard page
  - `GET /register` - Serve registration form page
  - `GET /server/{id}` - Serve server detail page
  - `GET /server/{id}/edit` - Serve server edit page
  - `GET /models` - Serve models list page
  - `GET /test` - Serve inference test page
  - `GET /logs` - Serve logs viewer (optional)
  - `GET /settings` - Serve settings page (optional)
- [ ] Create base HTML template per **FR-UI-NAV-001** through **FR-UI-NAV-003**
  - Navigation menu with all sections
  - Header with app title and quick stats
  - Footer with version info
  - Include Tailwind CSS via CDN per **TECH-UI-004**
  - Include necessary JavaScript libraries via CDN
- [ ] Implement Dashboard view per **FR-UI-DASH-001** through **FR-UI-DASH-005**
  - Summary cards (total servers, healthy count, models available)
  - Server list table with health status color coding
  - Filtering by model name, health status, student ID
  - Sorting by date, name, status, last check
  - Auto-refresh every 30 seconds using JavaScript
  - Clickable rows to navigate to detail view
- [ ] Implement Registration Form per **FR-UI-REG-001** through **FR-UI-REG-007**
  - All required and optional fields
  - Client-side validation with real-time feedback
  - "Test Connection" button to verify endpoint before submission
  - Submit form via Fetch API to `/admin/register`
  - Display success message with copyable registration ID
  - Display error messages from API
  - Loading states during submission
- [ ] Implement Server Detail View per **FR-UI-DETAIL-001** through **FR-UI-DETAIL-003**
  - Display all server metadata
  - Health check history timeline/chart
  - Action buttons: Edit, Delete, Force Health Check, Copy URL
  - Fetch server data via `/admin/servers/{id}` endpoint (need to add)
- [ ] Implement Server Edit Form per **FR-UI-EDIT-001** through **FR-UI-EDIT-004**
  - Pre-populate form with current values
  - Highlight modified fields
  - Confirmation dialog before saving
  - Submit via PUT to `/admin/register/{id}`
- [ ] Implement Models View per **FR-UI-MODEL-001** through **FR-UI-MODEL-003**
  - List all unique model names
  - Show server count and health percentage per model
  - Expandable server list for each model
  - Search/filter functionality
- [ ] Implement Inference Test Interface per **FR-UI-INF-001** through **FR-UI-INF-004**
  - Model selector dropdown (populated from `/v1/models`)
  - Message input textarea
  - System prompt input (optional)
  - Advanced options (temperature, max_tokens, etc.)
  - Stream toggle
  - Submit to `/v1/chat/completions`
  - Display streaming responses in real-time using SSE
  - Show metadata (server used, response time, tokens)
- [ ] Create shared JavaScript utilities in `app/static/js/common.js`
  - API client wrapper with authentication
  - Toast notification system per **FR-UI-ERR-003**
  - Loading state helpers
  - Error handling utilities per **FR-UI-ERR-001**
  - Debounce function for search/filter per **FR-UI-API-004**
- [ ] Implement responsive CSS styling per **FR-UI-002**
  - Mobile-first design with Tailwind CSS
  - Test on desktop, tablet, and mobile viewports
  - Ensure all interactions work on touch devices
- [ ] Add additional API endpoints needed for Web UI
  - `GET /admin/servers/{id}` - Get single server details
  - `POST /admin/servers/{id}/health-check` - Force health check
  - `GET /admin/stats` - Get dashboard statistics (optional)
  - `GET /admin/logs` - Get recent logs (optional)
- [ ] Implement API key input/storage for Web UI per **FR-UI-API-002**
  - Modal or page to enter API key
  - Store in sessionStorage or localStorage
  - Include in all admin API requests
  - Show authentication status in header
- [ ] Write integration tests for UI routes
  - Test all pages render without errors
  - Test static file serving
  - Test template rendering with sample data
  - Test error pages (404, 500)

**Effort Estimate**: M (Medium-high complexity, multiple interactive views)

**Definition of Done**:
- [ ] All UI pages accessible and render correctly
- [ ] Dashboard displays real-time server status with auto-refresh
- [ ] Registration form validates input and submits successfully
- [ ] Server detail view shows all metadata and history
- [ ] Edit form updates servers correctly
- [ ] Models view groups servers by model name
- [ ] Inference test interface makes requests and displays responses
- [ ] Streaming responses display in real-time
- [ ] All views are responsive (desktop, tablet, mobile)
- [ ] Navigation works correctly across all pages
- [ ] Toast notifications display for all user actions
- [ ] Error handling works for all API failures
- [ ] No JavaScript console errors in browser
- [ ] UI tested on Chrome, Firefox, and Safari per **NFR-USE-008**
- [ ] Integration tests pass with ≥70% coverage
- [ ] Manual test: Student registers server via Web UI in < 5 minutes
- [ ] Manual test: Student tests inference via Web UI successfully
- [ ] PR merged to main branch

---

### Phase 7: Polish, Documentation & Production Readiness

**Phase Goal**: Enhance error handling, improve logging coverage, write comprehensive documentation, and prepare for classroom deployment.

**Key Tasks**:
- [ ] Enhance error handling across all endpoints
  - Add request validation edge cases
  - Improve error messages to be more actionable per **FR-ERROR-005**
  - Ensure all errors logged with full context per **FR-ERROR-003**
  - Add request body size limits per Appendix B
- [ ] Implement rate limiting per **NFR-SEC-004**
  - 60 requests/minute per IP (configurable)
  - Use middleware or decorator
  - Return 429 Too Many Requests when exceeded
- [ ] Add input sanitization per **NFR-SEC-002**
  - Validate numeric ranges
  - Sanitize string inputs
  - Enforce request body size limits (1MB max)
- [x] Improve logging coverage
  - Add request/response correlation IDs
  - Log system startup/shutdown per **FR-LOG-005**
  - Add configuration change logging
  - Implement log rotation per **FR-LOG-006**
  - Verify API key redaction per **FR-LOG-007**
- [ ] Optional: Create `health_checks` table for historical tracking per **FR-REG-004**
  - Store last 100 health check results per server
  - Query endpoint to retrieve health history
- [x] Write comprehensive README.md per **NFR-USE-004**
  - System overview
  - Prerequisites (Python 3.11+)
  - Installation steps
  - Configuration guide
  - Starting the gateway
  - Stopping the gateway
  - Troubleshooting section
- [ ] Write setup documentation
  - Virtual environment setup
  - Dependencies installation
  - Database initialization
  - `.env` configuration
  - First run walkthrough
  - Target: Complete setup in < 15 minutes
- [x] Create example scripts per **NFR-USE-005**
  - `examples/register_server.py` - Student hosting example
  - `examples/use_model.py` - Student using example
  - `examples/list_models.py` - List available models
  - `examples/check_health.py` - Admin health check example
- [ ] Write API usage documentation
  - Add descriptions to all endpoints in OpenAPI docs
  - Document request/response formats
  - Add example requests and responses
  - Document error codes and meanings
- [x] Create startup script per **TECH-DEPLOY-004**
  - `start.sh` - Activates venv, sources `.env`, starts uvicorn
  - `stop.sh` - Gracefully stops the gateway
- [ ] Performance testing per **PERF-TEST-001**, **PERF-TEST-002**
  - Load test with 100 concurrent requests
  - Measure gateway latency overhead
  - Verify < 100ms overhead requirement
  - Test with 50 registered servers
- [x] Create GCE deployment automation per **TECH-DEPLOY-PROD-006**
  - `deploy/gce-setup.sh` - GCE instance initialization script
  - `deploy/install.sh` - Install Python 3.11, dependencies, configure system
  - `deploy/update.sh` - Pull latest code, restart service
  - `deploy/backup.sh` - Backup database to GCS bucket
  - `deploy/multiverse-gateway.service` - systemd service file
  - `deploy/nginx.conf` or `deploy/Caddyfile` - Reverse proxy config
- [x] Write comprehensive deployment documentation per **TECH-DEPLOY-PROD-007**
  - GCE instance creation guide (console and gcloud CLI)
  - Instance specifications: e2-micro (1 GB RAM, 0.25-2 vCPU)
  - SSH setup and key configuration
  - System dependencies installation
  - Repository setup and configuration
  - Systemd service setup and management
  - Reverse proxy setup (nginx or Caddy)
  - SSL certificate setup with Let's Encrypt
  - Firewall configuration (ports 22, 80, 443)
  - Health monitoring and alerts
  - Backup and restore procedures
  - Update and rollback procedures
  - Troubleshooting common issues
- [ ] Create security hardening guide per **TECH-DEPLOY-PROD-009**
  - Non-root user setup for service
  - SSH key-only authentication
  - Firewall rules (ufw or GCP firewall)
  - Automatic security updates
  - API key rotation procedure
  - Rate limiting configuration
  - HTTPS enforcement
- [ ] Create monitoring and maintenance guide
  - Service status checking (systemctl, logs)
  - Database size monitoring
  - Disk space monitoring
  - Log rotation verification
  - Backup verification
  - Performance metrics collection
  - Common maintenance tasks
- [x] Write devlog entry summarizing implementation
  - Key decisions made
  - Challenges encountered
  - Lessons learned
  - Future improvements

**Effort Estimate**: M (Medium complexity, mostly documentation and polish)

**Definition of Done**:
- [ ] All error messages are clear and actionable
- [ ] Rate limiting implemented and tested
- [ ] Comprehensive logging covers all events
- [x] README enables setup in < 15 minutes (tested with naive user)
- [x] Example scripts work and are well-commented
- [ ] API documentation complete in `/docs`
- [x] Startup/stop scripts functional
- [ ] Performance tests pass (≥100 concurrent, <100ms overhead)
- [ ] Code coverage ≥ 70% per **NFR-MAINT-003**, **TEST-004**
- [ ] All code follows PEP 8, has type hints and docstrings
- [x] GCE deployment scripts complete and tested
- [x] Deployment documentation covers all steps from instance creation to SSL setup
- [ ] Security hardening guide complete
- [ ] Successfully deployed to test GCE e2-micro instance
- [ ] Monitoring and maintenance procedures documented
- [ ] Backup and restore procedures tested
- [ ] System meets all success criteria from Section 1
- [ ] PR merged to main branch
- [ ] System ready for classroom rollout on GCE

---

## 5. Resource & Timeline

### Roles Required
- **Backend Developer(s)**: Python/FastAPI expertise, async programming knowledge
- **Frontend Developer(s)**: HTML/CSS/JavaScript, responsive design, UI/UX principles
- **DevOps/Deployment**: Optional for production deployment assistance
- **QA/Testing**: Manual testing with actual student servers and UI testing
- **Technical Writer**: Optional for documentation polish

### Estimated Timeline
**Note**: Timing removed per user request. Agents will execute phases sequentially.

### Potential Bottlenecks
- **Phase 2**: Initial health check may be slow if student servers are unresponsive
- **Phase 3**: OpenAI API compatibility requires careful attention to response format details
- **Phase 4**: Async background task coordination with database updates needs careful design
- **Phase 5**: Streaming proxy may have edge cases with different backend implementations
- **Phase 6**: Web UI implementation with multiple views and real-time features may require iteration
- **Phase 7**: Documentation quality depends on thoroughness, can be time-intensive

---

## 6. Communication Plan

### Key Stakeholders
- **Instructor/Course Lead**: Final approval on deployment readiness
- **Students (Server Hosts)**: Need registration documentation and support
- **Students (Model Users)**: Need usage documentation and API examples
- **TAs/Support Staff**: Need troubleshooting guides

### Reporting Cadence & Method
- **Per Phase**: Create PR with implementation, link to requirements met
- **After Phase 2**: Demo registration API to instructor, recruit 3 test servers
- **After Phase 3**: Demo end-to-end inference to instructor and test users
- **After Phase 4**: Share health monitoring logs with instructor
- **After Phase 5**: Demo streaming to instructor
- **After Phase 6**: Demo Web UI to instructor and students, collect usability feedback
- **After Phase 7**: Final review and classroom rollout decision

### Status Updates
- Progress tracked via GitHub issues/PRs
- Devlog entries for significant decisions or blockers
- Demo videos or screenshots for each phase completion

---

## 7. Plan Summary

### Total Estimated Phases
**7 Phases**, each designed as a single pull request of medium complexity:
1. **Foundation**: Infrastructure, database, logging, config (M)
2. **Registration API**: Server registration and management (M)
3. **Inference Routing**: OpenAI-compatible endpoints with failover (M)
4. **Health Checker**: Background health monitoring (M)
5. **Streaming Support**: SSE streaming for real-time responses (M)
6. **Web User Interface**: Browser-based dashboard, forms, and testing interface (M)
7. **Polish & Docs**: Error handling, documentation, production readiness (M)

### Critical Path/Key Dependencies
- **Phase 1** → **Phase 2** → **Phase 3**: Foundation enables registration, which enables routing
- **Phase 2** + **Phase 3** → **Phase 4**: Health checker needs servers registered and routing implemented
- **Phase 3** → **Phase 5**: Streaming builds on non-streaming routing
- **Phase 2** + **Phase 3** + **Phase 4** → **Phase 6**: Web UI needs API endpoints functional
- **All Phases** → **Phase 7**: Polish phase depends on all features being implemented

**Alternative Sequencing** (Early UI Feedback):
If user feedback is critical, consider: Phase 1 → Phase 2 → Phase 3 → Phase 6 (basic UI) → Phase 4 → Phase 5 → Phase 6 (complete) → Phase 7. This delivers a working UI earlier for usability testing, though it may require rework.

**Alternative Sequencing** (Risk-First):
If student servers are known to be highly unstable, consider: Phase 1 → Phase 2 → Phase 4 → Phase 3 → Phase 5 → Phase 6 → Phase 7. This builds health checking before routing, improving reliability from day one.

### Suggested First Step
1. Create virtual environment: `python3.11 -m venv env`
2. Activate: `source env/bin/activate`
3. Create `plans/plan.md` (this document) ✅
4. Begin **Phase 1: Foundation** - Set up project structure and infrastructure
5. Create PR for Phase 1 when complete

---

## 8. Production Deployment

### Google Cloud Engine Deployment (Live)

**Deployment Date**: October 17, 2025
**Deployed By**: Automated via gcloud CLI
**Status**: ✅ Active and Healthy

#### Instance Configuration

- **Instance Name**: multiverse-gateway
- **Machine Type**: e2-small (2 vCPUs, 2GB RAM)
- **Zone**: us-west1-b
- **Region**: us-west1
- **Project**: multiverseschool
- **External IP**: 136.117.2.59
- **OS**: Ubuntu 22.04 LTS
- **Disk**: 20GB standard persistent disk

#### Access Points

**Web User Interface**:
- Dashboard: http://136.117.2.59/dashboard
- Server Registration: http://136.117.2.59/register
- Model Viewer: http://136.117.2.59/models
- Inference Testing: http://136.117.2.59/test
- Settings: http://136.117.2.59/settings

**API Endpoints**:
- Base URL: http://136.117.2.59
- API Documentation: http://136.117.2.59/docs
- Health Check: http://136.117.2.59/health
- Models List: http://136.117.2.59/v1/models

#### Credentials

**Admin API Key**: `6ix6iURn29_4MPybfbyXgbxoO8-dPeoKuRPRR9Sj58o`
(Required for server registration and admin operations)

#### Deployed Services

1. **FastAPI Application**
   - Running on port 8000 (internal)
   - Managed by systemd: `multiverse-gateway.service`
   - Auto-starts on boot
   - All phases (1-6) fully operational

2. **Nginx Reverse Proxy**
   - Listening on port 80 (HTTP)
   - Proxying to application
   - Streaming support enabled
   - Logs: `/var/log/nginx/multiverse-gateway-*.log`

3. **Features Live**
   - ✅ Server registration (API + Web UI)
   - ✅ Health monitoring (background service)
   - ✅ Request routing (round-robin load balancing)
   - ✅ Streaming support (SSE)
   - ✅ Web dashboard (real-time updates)
   - ✅ Inference testing UI

#### Service Management

```bash
# SSH into instance
gcloud compute ssh multiverse-gateway --project=multiverseschool --zone=us-west1-b

# Check service status
sudo systemctl status multiverse-gateway

# View logs
sudo journalctl -u multiverse-gateway -f

# Restart service
sudo systemctl restart multiverse-gateway
```

#### File Locations

- Application: `/opt/multiverse-gateway/`
- Virtual Environment: `/opt/multiverse-gateway/env/`
- Configuration: `/opt/multiverse-gateway/.env`
- Database: `/opt/multiverse-gateway/gateway.db`
- systemd Service: `/etc/systemd/system/multiverse-gateway.service`
- Nginx Config: `/etc/nginx/sites-available/multiverse-gateway`

#### Backup & Maintenance

```bash
# Create backup
sudo su - gateway -c 'cd /opt/multiverse-gateway && bash deploy/backup.sh'

# Update application
sudo su - gateway -c 'cd /opt/multiverse-gateway && bash deploy/update.sh'
```

#### Monitoring

- Gateway Health: http://136.117.2.59/health
- Application Logs: `sudo journalctl -u multiverse-gateway -f`
- Nginx Logs: `sudo tail -f /var/log/nginx/multiverse-gateway-*.log`

#### Security

- HTTP/HTTPS firewall rules configured
- Admin API key authentication required
- Non-root service execution (gateway user)
- Security hardening via systemd

**Full deployment documentation**: See `GCE_DEPLOYMENT.md`

---

**Document Version**: 2.1
**Last Updated**: 2025-10-17
**Next Review**: After student testing in classroom
**Changelog**:
- v2.1: Added production deployment information (GCE)
- v2.1: Marked Phase 3 as complete
- v2.0: Added Phase 6 (Web User Interface) with comprehensive UI specifications
- v1.0: Initial plan with 6 phases (API-only implementation)

