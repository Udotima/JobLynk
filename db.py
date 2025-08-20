import os
from typing import Optional, List
from psycopg import connect, Connection
from psycopg.rows import dict_row
from psycopg.errors import UniqueViolation
from dotenv import load_dotenv

load_dotenv()

conn_str = os.getenv("POSTGRES_URL")

def get_db_connection() -> Connection:
    if not conn_str:
        raise ValueError("POSTGRES_URL environment variable is not set")
    return connect(conn_str, row_factory=dict_row)

def create_tables() -> None:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL CHECK (role IN ('freelancer', 'employer')),
            company_name TEXT
        );
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS jobs (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            salary DOUBLE PRECISION NOT NULL,
            job_type TEXT NOT NULL,
            employer_id INTEGER NOT NULL REFERENCES users(id)
        );
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS applications (
            id SERIAL PRIMARY KEY,
            job_id INTEGER NOT NULL REFERENCES jobs(id),
            freelancer_id INTEGER NOT NULL REFERENCES users(id),
            cover_letter TEXT,
            resume_path TEXT,
            UNIQUE(job_id, freelancer_id)
        );
        """
    )
    conn.commit()
    conn.close()

def insert_user(name: str, email: str, password: str, role: str, company_name: str = None) -> Optional[int]:
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO users (name, email, password, role, company_name)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
            """,
            (name, email, password, role, company_name),
        )
        user_id = cur.fetchone()["id"]
        conn.commit()
        return user_id
    except UniqueViolation:
        conn.rollback()
        return None
    finally:
        conn.close()

def get_user_by_email(email: str) -> Optional[dict]:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, email, password, role, company_name FROM users WHERE email = %s", (email,))
    user = cur.fetchone()
    conn.close()
    return user

def get_user_by_id(user_id: int) -> Optional[dict]:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, email, password, role, company_name FROM users WHERE id = %s", (user_id,))
    user = cur.fetchone()
    conn.close()
    return user

def insert_job(title: str, description: str, salary: float, job_type: str, employer_id: int) -> Optional[int]:
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO jobs (title, description, salary, job_type, employer_id)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
            """,
            (title, description, salary, job_type, employer_id),
        )
        job_id = cur.fetchone()["id"]
        conn.commit()
        return job_id
    except Exception:
        conn.rollback()
        return None
    finally:
        conn.close()

def get_jobs_by_employer(employer_id: int) -> List[dict]:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, title, description, salary, job_type FROM jobs WHERE employer_id = %s", (employer_id,))
    jobs = cur.fetchall()
    conn.close()
    return jobs

def get_all_jobs() -> List[dict]:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, title, description, salary, job_type, employer_id FROM jobs")
    jobs = cur.fetchall()
    conn.close()
    return jobs

def insert_application(job_id: int, freelancer_id: int, cover_letter: str, resume_path: str) -> bool:
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO applications (job_id, freelancer_id, cover_letter, resume_path)
            VALUES (%s, %s, %s, %s)
            """,
            (job_id, freelancer_id, cover_letter, resume_path),
        )
        conn.commit()
        return True
    except UniqueViolation:
        conn.rollback()
        return False
    finally:
        conn.close()