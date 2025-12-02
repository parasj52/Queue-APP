# DB connection helper for job queue_app
import sqlite3
DB_PATH = 'jobs.db'

def get_conn():
    return sqlite3.connect(DB_PATH)
