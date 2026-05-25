# backend/models.py
import sqlite3
import os
from datetime import datetime, timezone

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
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            question_no INTEGER NOT NULL CHECK(question_no BETWEEN 1 AND 8),
            answer TEXT NOT NULL,
            is_correct INTEGER NOT NULL DEFAULT 0,
            sub_no INTEGER NOT NULL DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(id),
            UNIQUE(student_id, question_no, sub_no)
        );

        CREATE TABLE IF NOT EXISTS drawings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL UNIQUE,
            points TEXT NOT NULL,
            auto_score TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(id)
        );

        CREATE TABLE IF NOT EXISTS self_check (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL UNIQUE,
            point_check TEXT NOT NULL DEFAULT '',
            line_check TEXT NOT NULL DEFAULT '',
            draw_check TEXT NOT NULL DEFAULT '',
            note TEXT NOT NULL DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(id)
        );
    """)
    conn.commit()

    # Migration: add sub_no column and widen CHECK for existing databases
    cols = [c[1] for c in conn.execute("PRAGMA table_info(answers)").fetchall()]
    if 'sub_no' not in cols:
        # Note: SQLite DDL auto-commits, so this migration is not fully atomic.
        # The risk is low: only the DROP/RENAME window could lose data on crash.
        conn.execute("ALTER TABLE answers ADD COLUMN sub_no INTEGER NOT NULL DEFAULT 0")
        # Recreate table to widen CHECK constraint (SQLite can't ALTER CHECK)
        conn.execute("""
            CREATE TABLE answers_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                question_no INTEGER NOT NULL CHECK(question_no BETWEEN 1 AND 8),
                answer TEXT NOT NULL,
                is_correct INTEGER NOT NULL DEFAULT 0,
                sub_no INTEGER NOT NULL DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students(id),
                UNIQUE(student_id, question_no, sub_no)
            )
        """)
        conn.execute("INSERT INTO answers_new SELECT id, student_id, question_no, answer, is_correct, 0, updated_at FROM answers")
        conn.execute("DROP TABLE answers")
        conn.execute("ALTER TABLE answers_new RENAME TO answers")
        conn.commit()

    conn.close()


# Reference answers for grading
REFERENCE_ANSWERS = {1: 'A', 2: 'B', 3: 'A', 4: 'B', 5: 'A', 6: 'A', 7: 'D'}

FILL_BLANK_ANSWERS = {8: {1: '25', 2: '4', 3: '11', 4: '100'}}

# Standard drawing coordinates: (day_index 0-5) -> expected data value
DRAWING_STANDARD = {0: 30, 1: 32, 2: 35, 3: 36, 4: 39, 5: 42}
DRAWING_TOLERANCE = 2

# X-axis labels for drawing
DAY_LABELS = ['周一', '周二', '周三', '周四', '周五', '周六']


def grade_drawing(points):
    """points: list of [day_index, value] — 6 points.
    Returns auto_score dict with points_correct, labels_complete, in_order, trend.
    """
    if len(points) != 6:
        return {'points_correct': False, 'labels_complete': False, 'in_order': False, 'trend': '无法判断'}

    # Check if points are in order by day_index (0,1,2,3,4,5)
    days = [p[0] for p in points]
    in_order = all(days[i] < days[i+1] for i in range(len(days)-1))

    # Check each point's value against standard (using day_index from pt[0])
    points_correct = True
    for pt in points:
        day_index = pt[0]
        expected = DRAWING_STANDARD.get(day_index)
        if expected is None:
            points_correct = False
            break
        value = pt[1] if isinstance(pt, (list, tuple)) and len(pt) >= 2 else pt
        if abs(value - expected) > DRAWING_TOLERANCE:
            points_correct = False
            break

    labels_complete = len(points) == 6
    trend = '上升' if in_order and points_correct else '无法判断'

    return {
        'points_correct': points_correct,
        'labels_complete': labels_complete,
        'in_order': in_order,
        'trend': trend,
    }
