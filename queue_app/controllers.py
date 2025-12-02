# Controller layer: Flask route handlers delegating to services
from flask import request, jsonify
import services


def register_routes(app):
    @app.route('/jobs', methods=['POST'])
    def submit_job():
        data = request.json or {}
        user = request.headers.get('X-User', 'anonymous')
        idempotency_key = data.get('idempotency_key')
        payload = data.get('payload')
        result, status = services.submit_job(payload, user, idempotency_key)
        return jsonify(result), status

    # list all jobs for all users (admin only)
    @app.route('/admin/jobs', methods=['GET'])
    def list_all_jobs():
        admin_key = request.headers.get('X-Admin-Key')
        if admin_key != 'secret-admin-key':
            return jsonify({'error': 'Unauthorized'}), 403
        jobs = services.list_all_jobs()
        return jsonify({'jobs': jobs})




    @app.route('/jobs/<job_id>', methods=['GET'])
    def job_status(job_id):
        row = services.get_job_status(job_id)
        if not row:
            return jsonify({'error': 'Job not found'}), 404
        return jsonify(row)

    @app.route('/jobs', methods=['GET'])
    def list_jobs():
        user = request.headers.get('X-User', 'anonymous')
        jobs = services.list_jobs(user)
        return jsonify({'jobs': jobs})

    @app.route('/dlq', methods=['GET'])
    def dlq():
        items = services.list_dlq()
        return jsonify({'dlq': items})

    @app.route('/metrics', methods=['GET'])
    def metrics():
        return jsonify(services.metrics())

    @app.route('/jobs/<job_id>/lease', methods=['POST'])
    def lease_job(job_id):
        result, status = services.lease_job(job_id)
        if status != 200:
            return jsonify(result), status
        return jsonify(result)

    @app.route('/jobs/<job_id>/ack', methods=['POST'])
    def ack_job(job_id):
        result, status = services.ack_job(job_id)
        if status != 200:
            return jsonify(result), status
        return jsonify(result)

    @app.route('/jobs/<job_id>/retry', methods=['POST'])
    def retry_job(job_id):
        result, status = services.retry_job(job_id)
        return jsonify(result), status

    @app.route('/jobs/<job_id>/dlq', methods=['POST'])
    def move_to_dlq(job_id):
        reason = request.json.get('reason', 'max retries')
        result, status = services.move_to_dlq(job_id, reason)
        return jsonify(result), status

