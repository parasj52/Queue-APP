# Business logic layer (services) for job queue_app
import uuid
import time
import dao

MAX_RETRIES = 3
RATE_LIMIT = 10  # jobs per minute
CONCURRENT_LIMIT = 5


def initialize():
    dao.init_db()


def submit_job(payload, user, idempotency_key=None):
    # rate limiting check
    now = time.time()
    window_start = now - 60
    count = dao.count_jobs_in_window(user, window_start)
    if count >= RATE_LIMIT:
        return {'error': 'Rate limit exceeded'}, 429
    # idempotency
    if idempotency_key:
        existing = dao.find_job_by_idempotency(user, idempotency_key)
        if existing:
            return {'job_id': existing, 'status': 'duplicate'}, 200
    job_id = str(uuid.uuid4())
    dao.insert_job(job_id, str(payload), user, idempotency_key)
    return {'job_id': job_id, 'status': 'pending'}, 200


def get_job_status(job_id):
    row = dao.get_job(job_id)
    if not row:
        return None
    # id, payload, status, retries, user, idempotency_key, created_at
    return {'job_id': row[0], 'payload': row[1], 'status': row[2], 'retries': row[3]}

# list all jobs for all users
def list_all_jobs(limit=100):
    rows = dao.list_all_jobs(limit)
    jobs = [{'id': r[0], 'status': r[1], 'retries': r[2], 'user': r[3]} for r in rows]
    return jobs

def list_jobs(user, limit=50):
    rows = dao.list_jobs_for_user(user, limit)
    jobs = [{'id': r[0], 'status': r[1], 'retries': r[2]} for r in rows]
    return jobs


def list_dlq(limit=50):
    rows = dao.list_dlq(limit)
    return [{'id': r[0], 'payload': r[1], 'user': r[2], 'reason': r[3]} for r in rows]


def lease_job(job_id):
    # simple lease: set status running if pending
    row = dao.get_job(job_id)
    if not row:
        return None, 404
    if row[2] != 'pending':
        return None, 400
    dao.update_job_status(job_id, 'running')
    return {'job_id': job_id, 'status': 'running'}, 200


def ack_job(job_id):
    row = dao.get_job(job_id)
    if not row:
        return None, 404
    if row[2] != 'running':
        return None, 400
    dao.update_job_status(job_id, 'done')
    return {'job_id': job_id, 'status': 'done'}, 200


def retry_job(job_id):
    row = dao.get_job(job_id)
    if not row:
        return {'error': 'Job not found'}, 404
    retries = row[3]
    if retries + 1 >= MAX_RETRIES:
        return {'error': 'Max retries reached'}, 400
    dao.increment_retries(job_id)
    return {'job_id': job_id, 'status': 'pending', 'retries': retries+1}, 200


def move_to_dlq(job_id, reason='max retries'):
    row = dao.get_job(job_id)
    if not row:
        return {'error': 'Job not found'}, 404
    payload = row[1]
    user = row[4]
    dao.insert_dlq(job_id, payload, user, reason)
    dao.delete_job(job_id)
    return {'job_id': job_id, 'status': 'dlq', 'reason': reason}, 200


def metrics():
    return dao.metrics()

