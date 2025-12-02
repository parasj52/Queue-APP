# Data Access Object (DAO) for jobs and DLQ
from db import get_conn
import time


def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS jobs (
        id TEXT PRIMARY KEY,
        payload TEXT,
        status TEXT,
        retries INTEGER,
        user TEXT,
        idempotency_key TEXT,
        created_at REAL
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS dlq (
        id TEXT PRIMARY KEY,
        payload TEXT,
        user TEXT,
        reason TEXT,
        created_at REAL
    )''')
    conn.commit()
    conn.close()


def insert_job(job_id, payload, user, idempotency_key=None, status='pending'):
    conn = get_conn()
    c = conn.cursor()
    now = time.time()
    c.execute("INSERT INTO jobs (id, payload, status, retries, user, idempotency_key, created_at) VALUES (?, ?, ?, 0, ?, ?, ?)",
              (job_id, payload, status, user, idempotency_key, now))
    conn.commit()
    conn.close()


def get_job(job_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, payload, status, retries, user, idempotency_key, created_at FROM jobs WHERE id=?", (job_id,))
    row = c.fetchone()
    conn.close()
    return row


def find_job_by_idempotency(user, idempotency_key):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id FROM jobs WHERE user=? AND idempotency_key=?", (user, idempotency_key))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

# list all jobs for all users
def list_all_jobs(limit=100):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, status, retries, user FROM jobs ORDER BY created_at DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return rows

def list_jobs_for_user(user, limit=50):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, status, retries FROM jobs WHERE user=? ORDER BY created_at DESC LIMIT ?", (user, limit))
    rows = c.fetchall()
    conn.close()
    return rows


def count_jobs_in_window(user, window_start):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM jobs WHERE user=? AND created_at>?", (user, window_start))
    count = c.fetchone()[0]
    conn.close()
    return count


def count_running_jobs(user):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM jobs WHERE user=? AND status='running'", (user,))
    count = c.fetchone()[0]
    conn.close()
    return count


def update_job_status(job_id, new_status):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE jobs SET status=? WHERE id=?", (new_status, job_id))
    conn.commit()
    conn.close()


def increment_retries(job_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE jobs SET retries=retries+1, status='pending' WHERE id=?", (job_id,))
    conn.commit()
    conn.close()


def delete_job(job_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM jobs WHERE id=?", (job_id,))
    conn.commit()
    conn.close()


def insert_dlq(job_id, payload, user, reason):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO dlq (id, payload, user, reason, created_at) VALUES (?, ?, ?, ?, ?)",
              (job_id, payload, user, reason, time.time()))
    conn.commit()
    conn.close()


def list_dlq(limit=50):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, payload, user, reason FROM dlq ORDER BY created_at DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return rows


def metrics():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM jobs")
    total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM jobs WHERE status='failed'")
    failed = c.fetchone()[0]
    c.execute("SELECT SUM(retries) FROM jobs")
    retries = c.fetchone()[0] or 0
    conn.close()
    return {'total_jobs': total, 'failed_jobs': failed, 'total_retries': retries}

