
# Worker process for job queue_app (API-based)
import time
import random
import requests

API_BASE = 'http://localhost:5000'

def lease_job():
    # Get pending jobs
    res = requests.get(f'{API_BASE}/admin/jobs', headers={'X-Admin-Key': 'secret-admin-key'})
    jobs = res.json().get('jobs', [])
    pending = [j for j in jobs if j['status'] == 'pending']
    if not pending:
        return None
    job = pending[-1]  # Pick oldest
    job_id = job['id']
    # Lease: mark as running
    requests.post(f'{API_BASE}/jobs/{job_id}/lease')
    return job_id

def ack_job(job_id):
    requests.post(f'{API_BASE}/jobs/{job_id}/ack')

def retry_job(job_id):
    requests.post(f'{API_BASE}/jobs/{job_id}/retry')

def send_to_dlq(job_id, reason):
    requests.post(f'{API_BASE}/jobs/{job_id}/dlq', json={'reason': reason})

while True:
    job_id = lease_job()
    if job_id:
        print(f"[LOG] Start job {job_id}")
        # Simulate job processing
        time.sleep(random.randint(1, 3))
        # Randomly succeed or fail
        success = random.choice([True, False, True])
        if success:
            ack_job(job_id)
            print(f"[LOG] Finish job {job_id}")
        else:
            # Get job status and retries
            res = requests.get(f'{API_BASE}/jobs/{job_id}')
            job = res.json()
            retries = job.get('retries', 0)
            if retries + 1 >= 3:
                send_to_dlq(job_id, 'max retries')
                print(f"[LOG] Job {job_id} sent to DLQ")
            else:
                retry_job(job_id)
                print(f"[LOG] Retry job {job_id}")
    else:
        time.sleep(2)
