# backend/models.py
import sqlite3
import os

DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
DB_PATH = os.path.join(DB_DIR, 'learning.db')


def get_db():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                question_no INTEGER NOT NULL CHECK(question_no BETWEEN 1 AND 5),
                answer TEXT NOT NULL,
                is_correct INTEGER NOT NULL DEFAULT 0,
                sub_no INTEGER NOT NULL DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students(id),
                UNIQUE(student_id, question_no, sub_no)
            );

            CREATE TABLE IF NOT EXISTS level_stars (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                level_no INTEGER NOT NULL CHECK(level_no BETWEEN 1 AND 5),
                stars INTEGER NOT NULL DEFAULT 0 CHECK(stars BETWEEN 0 AND 3),
                attempts INTEGER NOT NULL DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students(id),
                UNIQUE(student_id, level_no)
            );
        """)
        conn.commit()

        # Migration: widen CHECK constraint from 1-8 to 1-5 and clean old data
        _migrate_answers(conn)
        # Migration: drop legacy tables if they exist
        _drop_legacy(conn)

    finally:
        conn.close()


def _migrate_answers(conn):
    """Recreate answers table with CHECK(1-5) and wipe old data."""
    create_sql = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='answers'"
    ).fetchone()
    if create_sql and 'BETWEEN 1 AND 8' in create_sql['sql']:
        conn.execute("BEGIN")
        try:
            conn.execute("DELETE FROM answers")
            conn.execute("""
                CREATE TABLE answers_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    question_no INTEGER NOT NULL CHECK(question_no BETWEEN 1 AND 5),
                    answer TEXT NOT NULL,
                    is_correct INTEGER NOT NULL DEFAULT 0,
                    sub_no INTEGER NOT NULL DEFAULT 0,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (student_id) REFERENCES students(id),
                    UNIQUE(student_id, question_no, sub_no)
                )
            """)
            conn.execute("DROP TABLE answers")
            conn.execute("ALTER TABLE answers_new RENAME TO answers")
            conn.commit()
        except:
            conn.rollback()
            raise


def _drop_legacy(conn):
    """Drop drawings and self_check tables from old schema."""
    conn.execute("DROP TABLE IF EXISTS drawings")
    conn.execute("DROP TABLE IF EXISTS self_check")
    conn.commit()


# Reference answers for grading (question_no -> {sub_no: answer})
REFERENCE_ANSWERS = {
    1: {0: 'A'},
    2: {1: 'A', 2: 'B'},
    3: {0: 'D'},
    4: {0: 'A'},
    5: {1: '25', 2: '4', 3: '11', 4: '100'},
}

QUESTION_LABELS = {
    1: 'Q1 点与线的含义',
    2: 'Q2 条形图 vs 折线图',
    3: 'Q3 汽车行程图像',
    4: 'Q4 铁棒入水实验',
    5: 'Q5 水温加热实验',
}
