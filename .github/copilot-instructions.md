# Copilot Instructions for Distributed Task Queue & Job Processor

## Project Overview
This project is a prototype distributed job queue and worker system. It supports authenticated job submission, worker-based processing, and real-time status tracking via a dashboard.

## Architecture Guidelines
- **API Layer**: Expose REST (or gRPC) endpoints for job submission and status checks. Each job should support an optional idempotency key.
- **Persistence**: Use a durable store (SQLite, Redis, or Postgres) for jobs. Jobs must survive process restarts.
- **Workers**: Implement polling for jobs, with lease/ack/retry logic. Failed jobs after max retries go to a Dead Letter Queue (DLQ).
- **Rate Limiting**: Enforce per-tenant limits (e.g., max 5 concurrent jobs, 10 new jobs/minute).
- **Dashboard**: Build a simple web UI (React or HTML+JS) showing job states and DLQ. Use WebSockets or polling for live updates.
- **Observability**: Log all major events (submit, start, finish, fail) with job/trace IDs. Expose metrics (total jobs, failed jobs, retries).

## Developer Workflow
- **Start API server**: `python api.py` or `node api.js` (adjust for your stack)
- **Start worker(s)**: `python worker.py` or `node worker.js`
- **Run dashboard**: `npm start` (if using React), or open `dashboard.html`
- **Database setup**: Use SQLite for simplicity (`sqlite3 jobs.db`), or configure Redis/Postgres as needed.
- **Testing**: Place tests in a `tests/` directory. Use `pytest` or `npm test` as appropriate.

## Project-Specific Patterns
- Jobs should have status: `pending`, `running`, `done`, `failed`.
- Use a DLQ table/collection for failed jobs.
- Each log entry should include a job ID or trace ID.
- Rate limits and quotas must be enforced per user/tenant.
- Retry logic: jobs re-queued up to N times, then sent to DLQ.

## Key Files & Directories (to create)
- `api.py` or `api.js` — API server
- `worker.py` or `worker.js` — Worker process
- `dashboard/` — Web UI
- `models.py` or `models.js` — Job and user models
- `db.py` or `db.js` — Persistence logic
- `tests/` — Unit and integration tests
- `README.md` — Design notes and trade-offs

## Integration Points
- Database connection string in config file (e.g., `config.json`)
- WebSocket endpoint for dashboard updates
- API authentication (token-based or basic auth)

## Example Patterns
- Job submission:
  ```python
  POST /jobs { "payload": {...}, "idempotency_key": "abc123" }
  ```
- Worker lease/ack:
  ```python
  # Lease
  UPDATE jobs SET status='running' WHERE id=?
  # Ack
  UPDATE jobs SET status='done' WHERE id=?
  # Retry
  UPDATE jobs SET status='pending', retries=retries+1 WHERE id=? AND retries < MAX
  ```

## Notes
- Keep code modular: separate API, worker, dashboard, and persistence logic.
- Document design trade-offs in `README.md`.
- Prototype-level reliability and observability are sufficient.
