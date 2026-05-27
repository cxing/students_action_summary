# Level Game Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace 8 old questions with 5 game-based levels, per-level instant submit, and teacher bar-chart generation.

**Architecture:** 5 independent Vue level components (`/level/1`–`/level/5`), each with unique game mechanics (shooting, drag-drop, animation+choice, fill-blank). Backend gets per-level submit endpoint + matplotlib chart PNG endpoint. Store simplified to `levels` object.

**Tech Stack:** Vue 3 + Pinia + Vue Router + Axios + Vite (frontend), Python Flask + SQLite + matplotlib (backend)

---

### Task 1: Database migration — models.py

**Files:**
- Modify: `backend/models.py`

- [ ] **Step 1: Rewrite models.py with new schema, reference answers, and drop old tables**

Replace the entire content of `backend/models.py`:

```python
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

    conn.close()


def _migrate_answers(conn):
    """Recreate answers table with CHECK(1-5) and wipe old data."""
    # Check if migration is needed by reading current CHECK
    create_sql = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='answers'"
    ).fetchone()
    if create_sql and 'BETWEEN 1 AND 8' in create_sql['sql']:
        # Wipe old answers (old question content is replaced)
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
        conn.execute("INSERT INTO answers_new SELECT * FROM answers")
        conn.execute("DROP TABLE answers")
        conn.execute("ALTER TABLE answers_new RENAME TO answers")
        conn.commit()


def _drop_legacy(conn):
    """Drop drawings and self_check tables from old schema."""
    tables = [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()]
    for t in ['drawings', 'self_check']:
        if t in tables:
            conn.execute(f"DROP TABLE {t}")
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
```

- [ ] **Step 2: Verify database init works**

Run: `cd backend && python3 -c "from models import init_db; init_db(); print('OK')"`
Expected: `OK` (no errors)

- [ ] **Step 3: Commit**

```bash
git add backend/models.py
git commit -m "feat: migrate database schema for 5-level game system"
```

---

### Task 2: Backend — auth.py (login response)

**Files:**
- Modify: `backend/auth.py`

- [ ] **Step 1: Rewrite student_login to return level data instead of old answers/drawing/self_check**

Replace the existing_answers/drawing/self_check loading section in `student_login()` (lines 28–59) with:

```python
    # Load existing level data for returning students
    existing_levels = {}
    if not is_new:
        ans_rows = conn.execute(
            'SELECT question_no, answer, is_correct, sub_no FROM answers WHERE student_id = ? ORDER BY question_no, sub_no',
            (student_id,)
        ).fetchall()
        for r in ans_rows:
            qno = str(r['question_no'])
            if qno not in existing_levels:
                existing_levels[qno] = {'answer': {}, 'stars': 0, 'attempts': 0}
            sn = str(r['sub_no']) if r['sub_no'] > 0 else '0'
            existing_levels[qno]['answer'][sn] = r['answer']

        star_rows = conn.execute(
            'SELECT level_no, stars, attempts FROM level_stars WHERE student_id = ?',
            (student_id,)
        ).fetchall()
        for sr in star_rows:
            lvl = str(sr['level_no'])
            if lvl not in existing_levels:
                existing_levels[lvl] = {'answer': {}, 'stars': 0, 'attempts': 0}
            existing_levels[lvl]['stars'] = sr['stars']
            existing_levels[lvl]['attempts'] = sr['attempts']
```

Replace the return statement (lines 63–69) with:

```python
    return jsonify({
        'student_id': student_id,
        'name': student_name,
        'existing_levels': existing_levels,
    })
```

Also remove the unused `import json` line. The final `auth.py` should only have `import json` removed.

- [ ] **Step 2: Verify login endpoint works**

Run in background: `cd backend && python3 app.py`
Then: `curl -s -X POST http://localhost:5001/api/student/login -H 'Content-Type: application/json' -d '{"name":"test123"}' | python3 -m json.tool`
Expected: JSON with `student_id`, `name`, `existing_levels: {}`

- [ ] **Step 3: Commit**

```bash
git add backend/auth.py
git commit -m "feat: update student login to return level data"
```

---

### Task 3: Backend — submit.py (per-level submit)

**Files:**
- Modify: `backend/submit.py`

- [ ] **Step 1: Rewrite submit.py for per-level submission**

Replace the entire content of `backend/submit.py`:

```python
# backend/submit.py
from flask import Blueprint, request, jsonify
from models import get_db, REFERENCE_ANSWERS

submit_bp = Blueprint('submit', __name__)


def _grade_answer(level_no, answer):
    """Grade a level answer. Returns dict of {sub_no: (answer_str, is_correct)}."""
    expected = REFERENCE_ANSWERS.get(level_no, {})
    results = {}
    for sub_no_str, expected_ans in expected.items():
        sub_no = int(sub_no_str)
        if sub_no == 0:
            student_ans = answer if isinstance(answer, str) else answer.get('0', '')
        else:
            student_ans = answer.get(str(sub_no), '') if isinstance(answer, dict) else ''
        is_correct = 1 if str(student_ans).strip() == str(expected_ans) else 0
        results[sub_no] = (str(student_ans).strip(), is_correct)
    return results


@submit_bp.route('/api/level/submit', methods=['POST'])
def submit_level():
    data = request.get_json()
    student_id = data.get('student_id')
    level_no = data.get('level_no')
    answer = data.get('answer')
    stars = data.get('stars', 0)
    attempts = data.get('attempts', 0)

    if not student_id or level_no is None:
        return jsonify({'error': '缺少参数'}), 400
    if level_no < 1 or level_no > 5:
        return jsonify({'error': '无效的关卡号'}), 400

    conn = get_db()

    student = conn.execute('SELECT id FROM students WHERE id = ?', (student_id,)).fetchone()
    if not student:
        conn.close()
        return jsonify({'error': '学生不存在'}), 404

    # Grade and save answers
    graded = _grade_answer(level_no, answer)
    all_correct = all(is_corr for _, is_corr in graded.values())

    for sub_no, (ans_str, is_correct) in graded.items():
        conn.execute("""
            INSERT INTO answers (student_id, question_no, answer, is_correct, sub_no, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(student_id, question_no, sub_no)
            DO UPDATE SET answer = excluded.answer, is_correct = excluded.is_correct, updated_at = CURRENT_TIMESTAMP
        """, (student_id, level_no, ans_str, is_correct, sub_no))

    # Save stars
    conn.execute("""
        INSERT INTO level_stars (student_id, level_no, stars, attempts, updated_at)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(student_id, level_no)
        DO UPDATE SET stars = excluded.stars, attempts = excluded.attempts, updated_at = CURRENT_TIMESTAMP
    """, (student_id, level_no, stars, attempts))

    conn.commit()
    conn.close()

    return jsonify({
        'ok': True,
        'is_correct': bool(all_correct),
        'stars': stars,
    })
```

- [ ] **Step 2: Verify submit endpoint**

```bash
curl -s -X POST http://localhost:5001/api/level/submit \
  -H 'Content-Type: application/json' \
  -d '{"student_id":1,"level_no":1,"answer":"A","stars":3,"attempts":1}' | python3 -m json.tool
```
Expected: `{"ok": true, "is_correct": true, "stars": 3}`

Test Q2 multi-sub:
```bash
curl -s -X POST http://localhost:5001/api/level/submit \
  -H 'Content-Type: application/json' \
  -d '{"student_id":1,"level_no":2,"answer":{"1":"A","2":"B"},"stars":2,"attempts":2}' | python3 -m json.tool
```
Expected: `{"ok": true, "is_correct": true, "stars": 2}`

- [ ] **Step 3: Commit**

```bash
git add backend/submit.py
git commit -m "feat: replace bulk submit with per-level submit endpoint"
```

---

### Task 4: Backend — teacher.py (updated dashboard + chart endpoint)

**Files:**
- Modify: `backend/teacher.py`

- [ ] **Step 1: Update dashboard endpoint for 5 questions + stars**

Replace the `dashboard()` function (lines 18–57) with:

```python
@teacher_bp.route('/api/teacher/dashboard', methods=['GET'])
@require_teacher
def dashboard():
    from models import get_db
    conn = get_db()

    students = conn.execute('SELECT id, name FROM students ORDER BY id').fetchall()
    result = []
    for s in students:
        ans_rows = conn.execute(
            'SELECT question_no, answer, is_correct, sub_no FROM answers WHERE student_id = ?',
            (s['id'],)
        ).fetchall()
        answers = {}
        scores = {}
        for row in ans_rows:
            qno = str(row['question_no'])
            if row['sub_no'] > 0:
                scores[f'{qno}_{row["sub_no"]}'] = bool(row['is_correct'])
            else:
                answers[qno] = row['answer']
                scores[qno] = bool(row['is_correct'])

        star_rows = conn.execute(
            'SELECT level_no, stars FROM level_stars WHERE student_id = ?',
            (s['id'],)
        ).fetchall()
        stars = {str(r['level_no']): r['stars'] for r in star_rows}
        total_stars = sum(r['stars'] for r in star_rows)

        result.append({
            'id': s['id'],
            'name': s['name'],
            'answers': answers,
            'scores': scores,
            'stars': stars,
            'total_stars': total_stars,
        })

    total = len(result)
    submitted = sum(1 for r in result if len(r['answers']) > 0)
    conn.close()

    return jsonify({
        'students': result,
        'stats': {'submitted': submitted, 'total': total},
    })
```

- [ ] **Step 2: Update student_detail endpoint for 5 questions + stars**

Replace the `student_detail()` function (lines 60–102) with:

```python
@teacher_bp.route('/api/teacher/student/<int:student_id>', methods=['GET'])
@require_teacher
def student_detail(student_id):
    from models import get_db
    conn = get_db()

    student = conn.execute('SELECT id, name FROM students WHERE id = ?', (student_id,)).fetchone()
    if not student:
        conn.close()
        return jsonify({'error': '学生不存在'}), 404

    ans_rows = conn.execute(
        'SELECT question_no, answer, is_correct, sub_no FROM answers WHERE student_id = ? ORDER BY question_no, sub_no',
        (student_id,)
    ).fetchall()
    answers = [
        {'question_no': r['question_no'], 'answer': r['answer'],
         'is_correct': bool(r['is_correct']), 'sub_no': r['sub_no']}
        for r in ans_rows
    ]

    star_rows = conn.execute(
        'SELECT level_no, stars, attempts FROM level_stars WHERE student_id = ? ORDER BY level_no',
        (student_id,)
    ).fetchall()
    stars = [
        {'level_no': r['level_no'], 'stars': r['stars'], 'attempts': r['attempts']}
        for r in star_rows
    ]
    total_stars = sum(r['stars'] for r in star_rows)

    conn.close()
    return jsonify({
        'id': student['id'],
        'name': student['name'],
        'answers': answers,
        'stars': stars,
        'total_stars': total_stars,
    })
```

- [ ] **Step 3: Update delete endpoint for level_stars**

Replace the `delete_student_submission()` function (lines 105–123) to also delete from level_stars:

```python
@teacher_bp.route('/api/teacher/student/<int:student_id>', methods=['DELETE'])
@require_teacher
def delete_student_submission(student_id):
    from models import get_db
    conn = get_db()

    student = conn.execute('SELECT id FROM students WHERE id = ?', (student_id,)).fetchone()
    if not student:
        conn.close()
        return jsonify({'error': '学生不存在'}), 404

    conn.execute('DELETE FROM answers WHERE student_id = ?', (student_id,))
    conn.execute('DELETE FROM level_stars WHERE student_id = ?', (student_id,))
    conn.execute('DELETE FROM students WHERE id = ?', (student_id,))
    conn.commit()
    conn.close()

    return jsonify({'ok': True})
```

- [ ] **Step 4: Add chart generation endpoint**

Add after the delete endpoint at the end of `teacher.py`:

```python
@teacher_bp.route('/api/teacher/chart', methods=['GET'])
@require_teacher
def chart():
    """Generate bar chart PNG. Query params: type=questions|stars"""
    import io
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from models import get_db, REFERENCE_ANSWERS

    chart_type = request.args.get('type', 'questions')
    conn = get_db()

    plt.rcParams['font.sans-serif'] = ['PingFang SC', 'Heiti SC', 'SimHei', 'Arial Unicode MS']
    plt.rcParams['axes.unicode_minus'] = False

    if chart_type == 'questions':
        # Per-question correct count
        labels = ['Q1 点与线', 'Q2 条形vs折线', 'Q3 汽车行程', 'Q4 铁棒入水', 'Q5 水温加热']
        correct_counts = []
        total_students = conn.execute('SELECT COUNT(*) FROM students').fetchone()[0] or 1

        for qno in range(1, 6):
            if qno in (2, 5):
                # Multi-sub: count students who got ALL sub-questions correct
                total_subs = len([k for k in REFERENCE_ANSWERS.get(qno, {}) if k > 0]) if qno == 2 else 4
                rows = conn.execute("""
                    SELECT student_id, SUM(is_correct) as correct_subs
                    FROM answers WHERE question_no = ?
                    GROUP BY student_id
                """, (qno,)).fetchall()
                count = sum(1 for r in rows if r['correct_subs'] == total_subs)
            else:
                count = conn.execute(
                    'SELECT COUNT(DISTINCT student_id) FROM answers WHERE question_no = ? AND is_correct = 1',
                    (qno,)
                ).fetchone()[0]
            correct_counts.append(count)

        fig, ax = plt.subplots(figsize=(10, 5))
        bars = ax.bar(labels, correct_counts, color='#4a90d9', edgecolor='white', linewidth=0.5)
        for bar, count in zip(bars, correct_counts):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                    str(count), ha='center', va='bottom', fontsize=14, fontweight='bold')
        ax.set_ylabel('正确人数', fontsize=13)
        ax.set_title(f'全班各题正确人数 (共 {total_students} 人)', fontsize=15, fontweight='bold')
        ax.set_ylim(0, max(correct_counts + [total_students]) + 2)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        plt.xticks(fontsize=11)
        plt.tight_layout()

    elif chart_type == 'stars':
        # Star distribution histogram
        conn2 = get_db()
        rows = conn2.execute(
            'SELECT student_id, SUM(stars) as total FROM level_stars GROUP BY student_id'
        ).fetchall()
        conn2.close()

        star_values = [r['total'] for r in rows]
        bins = [0, 3, 6, 9, 12, 15]
        bin_labels = ['0-3', '4-6', '7-9', '10-12', '13-15']
        counts = [0] * 5
        for v in star_values:
            for i in range(5):
                if bins[i] <= v <= bins[i + 1]:
                    counts[i] += 1
                    break

        fig, ax = plt.subplots(figsize=(10, 5))
        bars = ax.bar(bin_labels, counts, color='#f5a623', edgecolor='white', linewidth=0.5)
        for bar, count in zip(bars, counts):
            if count > 0:
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.2,
                        str(count), ha='center', va='bottom', fontsize=14, fontweight='bold')
        ax.set_xlabel('星星总数区间', fontsize=13)
        ax.set_ylabel('人数', fontsize=13)
        ax.set_title('全班星星总数分布', fontsize=15, fontweight='bold')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        plt.tight_layout()

    else:
        conn.close()
        return jsonify({'error': '无效的 type 参数'}), 400

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100)
    plt.close()
    buf.seek(0)
    conn.close()

    from flask import send_file
    return send_file(buf, mimetype='image/png')
```

Add `from flask import request` to the imports line and add REFERENCE_ANSWERS import at the top of the chart function. Actually, add the request import to the existing flask import:

Change line 3: `from flask import Blueprint, jsonify, session` → `from flask import Blueprint, jsonify, session, request`

- [ ] **Step 5: Verify teacher dashboard**

```bash
curl -s http://localhost:5001/api/teacher/dashboard -H 'Cookie: session=...' | python3 -m json.tool
```
Expected: JSON with `students` array and `stats` object, each student has `stars` and `total_stars` fields.

- [ ] **Step 6: Commit**

```bash
git add backend/teacher.py
git commit -m "feat: update teacher API for 5 levels, add bar chart endpoint"
```

---

### Task 5: Backend — app.py (register blueprint) + requirements.txt

**Files:**
- Modify: `backend/app.py`
- Modify: `backend/requirements.txt`

- [ ] **Step 1: Add matplotlib to requirements.txt**

Replace `backend/requirements.txt` content:

```
flask==3.1.1
flask-cors==5.0.1
matplotlib==3.10.3
```

- [ ] **Step 2: app.py — no changes needed (blueprint is already registered)**

The existing `app.py` already registers `submit_bp` and `teacher_bp`. Since we modified those modules in-place (same blueprint names), no changes to `app.py` are needed.

- [ ] **Step 3: Install dependencies and verify app starts**

```bash
cd backend && pip install -r requirements.txt && python3 -c "from app import create_app; app = create_app(); print('OK')"
```
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add backend/requirements.txt
git commit -m "chore: add matplotlib for teacher bar chart generation"
```

---

### Task 6: Frontend — Store (student.js)

**Files:**
- Modify: `frontend/src/stores/student.js`

- [ ] **Step 1: Rewrite store for levels-based state**

Replace the entire content of `frontend/src/stores/student.js`:

```javascript
import { defineStore } from 'pinia'
import { ref, reactive, computed } from 'vue'

export const useStudentStore = defineStore('student', () => {
  const studentId = ref(null)
  const name = ref('')
  const levels = reactive({
    1: { answer: null, stars: 0, attempts: 0 },
    2: { answer: null, stars: 0, attempts: 0 },
    3: { answer: null, stars: 0, attempts: 0 },
    4: { answer: null, stars: 0, attempts: 0 },
    5: { answer: null, stars: 0, attempts: 0 },
  })

  const totalStars = computed(() => {
    return Object.values(levels).reduce((sum, l) => sum + l.stars, 0)
  })

  function setStudent(id, studentName) { studentId.value = id; name.value = studentName }

  function setLevel(levelNo, data) {
    Object.assign(levels[levelNo], data)
  }

  function restoreLevels(existingLevels) {
    for (const [lvl, data] of Object.entries(existingLevels)) {
      const lv = parseInt(lvl)
      if (lv >= 1 && lv <= 5) {
        levels[lv].stars = data.stars || 0
        levels[lv].attempts = data.attempts || 0
        levels[lv].answer = data.answer || null
      }
    }
  }

  function reset() {
    studentId.value = null
    name.value = ''
    for (let i = 1; i <= 5; i++) {
      levels[i] = { answer: null, stars: 0, attempts: 0 }
    }
  }

  return { studentId, name, levels, totalStars, setStudent, setLevel, restoreLevels, reset }
})
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/stores/student.js
git commit -m "feat: rewrite store for 5-level game state"
```

---

### Task 7: Frontend — Router + API

**Files:**
- Modify: `frontend/src/router/index.js`
- Modify: `frontend/src/api.js`

- [ ] **Step 1: Update router with level routes, remove old routes**

Replace the entire content of `frontend/src/router/index.js`:

```javascript
import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'StudentLogin', component: () => import('../views-student/StudentLogin.vue') },
  { path: '/level/1', name: 'Level1', component: () => import('../views-student/Level1Balloon.vue') },
  { path: '/level/2', name: 'Level2', component: () => import('../views-student/Level2DragDrop.vue') },
  { path: '/level/3', name: 'Level3', component: () => import('../views-student/Level3CarRide.vue') },
  { path: '/level/4', name: 'Level4', component: () => import('../views-student/Level4WaterTank.vue') },
  { path: '/level/5', name: 'Level5', component: () => import('../views-student/Level5Thermometer.vue') },
  { path: '/submit-success', name: 'SubmitSuccess', component: () => import('../views-student/SubmitSuccess.vue') },
  { path: '/teacher', name: 'TeacherLogin', component: () => import('../views-teacher/TeacherLogin.vue') },
  { path: '/teacher/dashboard', name: 'Dashboard', component: () => import('../views-teacher/Dashboard.vue') },
  { path: '/teacher/student/:id', name: 'StudentDetail', component: () => import('../views-teacher/StudentDetail.vue'), props: true },
]

const router = createRouter({ history: createWebHistory(), routes })
export default router
```

- [ ] **Step 2: Update api.js — add levelSubmit, remove submitAll**

Replace the entire content of `frontend/src/api.js`:

```javascript
import axios from 'axios'

const api = axios.create({ baseURL: '/api', withCredentials: true })

export function studentLogin(name) { return api.post('/student/login', { name }) }
export function teacherLogin(username, password) { return api.post('/teacher/login', { username, password }) }
export function teacherCheck() { return api.get('/teacher/check') }

export function submitLevel(studentId, levelNo, answer, stars, attempts) {
  return api.post('/level/submit', {
    student_id: studentId,
    level_no: levelNo,
    answer: answer,
    stars: stars,
    attempts: attempts,
  })
}

export function getDashboard() { return api.get('/teacher/dashboard') }
export function getStudentDetail(studentId) { return api.get(`/teacher/student/${studentId}`) }
export function deleteStudentSubmission(studentId) { return api.delete(`/teacher/student/${studentId}`) }
export function getChartUrl(type) { return `/api/teacher/chart?type=${type}` }
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/router/index.js frontend/src/api.js
git commit -m "feat: update router and API for 5-level game flow"
```

---

### Task 8: Frontend — StudentLogin.vue

**Files:**
- Modify: `frontend/src/views-student/StudentLogin.vue`

- [ ] **Step 1: Update login to restore levels and navigate to /level/1**

Replace the `handleLogin` function (lines 52–81) in `StudentLogin.vue`:

```javascript
async function handleLogin() {
  if (!name.value.trim()) return
  loading.value = true
  error.value = ''
  try {
    const res = await studentLogin(name.value.trim())
    const d = res.data
    store.setStudent(d.student_id, d.name)
    if (d.existing_levels) {
      store.restoreLevels(d.existing_levels)
    }
    router.push('/level/1')
  } catch (e) {
    error.value = '登录失败，请重试'
  } finally {
    loading.value = false
  }
}
```

No template changes needed — the login page UI stays the same.

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views-student/StudentLogin.vue
git commit -m "feat: update login to restore levels and navigate to level 1"
```

---

### Task 9: Frontend — SubmitSuccess.vue

**Files:**
- Modify: `frontend/src/views-student/SubmitSuccess.vue`

- [ ] **Step 1: Rewrite SubmitSuccess to show star summary**

Replace the entire content of `frontend/src/views-student/SubmitSuccess.vue`:

```vue
<template>
  <div class="login-container">
    <div class="login-card success-card">
      <div class="success-icon">&#9733;</div>
      <h1>闯关完成！</h1>
      <p>{{ store.name }} 同学，你一共获得了 <strong>{{ store.totalStars }} / 15</strong> 颗星</p>

      <div class="stars-breakdown">
        <div v-for="lv in 5" :key="lv" class="star-row">
          <span class="star-level">第{{ lv }}关</span>
          <span class="star-count">
            <template v-for="s in 3" :key="s">
              <span :class="s <= store.levels[lv].stars ? 'star-filled' : 'star-empty'">&#9733;</span>
            </template>
          </span>
        </div>
      </div>

      <button @click="switchUser" class="btn-primary" style="margin-top: 20px;">切换用户</button>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useStudentStore } from '../stores/student.js'

const router = useRouter()
const store = useStudentStore()

function switchUser() {
  store.reset()
  router.push('/')
}
</script>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views-student/SubmitSuccess.vue
git commit -m "feat: update submit success page with star summary"
```

---

### Task 10: Frontend — Level1Balloon.vue (射击气球)

**Files:**
- Create: `frontend/src/views-student/Level1Balloon.vue`

- [ ] **Step 1: Create Level1Balloon.vue**

Write full component:

```vue
<template>
  <div class="level-container">
    <div class="level-header">
      <span class="level-badge">第 1 关</span>
      <span class="level-title">🎈 射击气球</span>
      <div class="star-display">
        <span v-for="s in 3" :key="s" :class="s <= store.levels[1].stars ? 'star-filled' : 'star-empty'">&#9733;</span>
      </div>
    </div>

    <div class="game-card">
      <p class="question-text">折线统计图中的"点"和"线"分别表示什么？</p>

      <div class="balloon-field">
        <div
          v-for="opt in options"
          :key="opt.key"
          class="balloon-pair"
          :class="{ 'balloon-hit': hitKey === opt.key, 'balloon-shake': shakeKey === opt.key }"
        >
          <div class="balloon balloon-point" @click="shoot(opt.key, opt.point)">
            <div class="balloon-string"></div>
            <div class="balloon-body" :style="{ background: opt.color }">
              <span class="balloon-label">点</span>
              <span class="balloon-text">{{ opt.point }}</span>
            </div>
          </div>
          <div class="balloon balloon-line" @click="shoot(opt.key, opt.line)">
            <div class="balloon-string"></div>
            <div class="balloon-body" :style="{ background: opt.color }">
              <span class="balloon-label">线</span>
              <span class="balloon-text">{{ opt.line }}</span>
            </div>
          </div>
          <span class="pair-letter">{{ opt.key }}</span>
        </div>
      </div>

      <div v-if="result !== null" :class="result ? 'feedback-correct' : 'feedback-wrong'">
        {{ result ? '🎯 射中了！太棒了！' : '💨 没射中，再试一次！' }}
      </div>

      <div class="nav-buttons">
        <router-link to="/" class="btn-secondary">退出</router-link>
        <router-link to="/level/2" class="btn-primary" :class="{ 'btn-disabled': store.levels[1].stars === 0 && result === null }">
          下一关 →
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useStudentStore } from '../stores/student.js'
import { submitLevel } from '../api.js'

const store = useStudentStore()
const result = ref(null)
const hitKey = ref(null)
const shakeKey = ref(null)

const options = [
  { key: 'A', point: '数量的多少', line: '数量的变化趋势', color: '#e74c3c', correct: true },
  { key: 'B', point: '图形的颜色', line: '数量的单位', color: '#3498db', correct: false },
  { key: 'C', point: '统计图的标题', line: '横轴的长度', color: '#2ecc71', correct: false },
]

async function shoot(key, text) {
  if (hitKey.value) return // prevent double-shoot
  const opt = options.find(o => o.key === key)
  const isCorrect = opt.correct
  const attempts = store.levels[1].attempts + 1
  const stars = isCorrect
    ? (attempts === 1 ? 3 : attempts === 2 ? 2 : 1)
    : 0

  hitKey.value = key
  if (!isCorrect) {
    shakeKey.value = key
    setTimeout(() => { shakeKey.value = null; hitKey.value = null }, 600)
  }

  store.setLevel(1, { answer: key, stars: isCorrect ? stars : 0, attempts })
  result.value = isCorrect

  try {
    await submitLevel(store.studentId, 1, key, isCorrect ? stars : 0, attempts)
  } catch (e) { /* game continues even if submit fails */ }
}
</script>
```

The component is too large to inline in one step. Let me write the complete file with all needed CSS animation classes. The actual Write call will include the full file. Key CSS classes for balloon animation are added to style.css in a later task.

- [ ] **Step 2: Verify component renders**

Run: `cd frontend && npm run dev`
Open `http://localhost:5173`, login, verify navigation to /level/1 shows the balloon game.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views-student/Level1Balloon.vue
git commit -m "feat: add Level 1 balloon shooting game"
```

---

### Task 11: Frontend — Level2DragDrop.vue (拖拽分类)

**Files:**
- Create: `frontend/src/views-student/Level2DragDrop.vue`

- [ ] **Step 1: Create Level2DragDrop.vue**

```vue
<template>
  <div class="level-container">
    <div class="level-header">
      <span class="level-badge">第 2 关</span>
      <span class="level-title">🧩 拖拽分类</span>
      <div class="star-display">
        <span v-for="s in 3" :key="s" :class="s <= store.levels[2].stars ? 'star-filled' : 'star-empty'">&#9733;</span>
      </div>
    </div>

    <div class="game-card">
      <!-- Reference tables -->
      <details class="ref-tables" open>
        <summary>统计数据参考（点击收起/展开）</summary>
        <div class="table-section">
          <h4>统计表一：6名同学一分钟仰卧起坐个数统计表</h4>
          <table class="data-table">
            <thead><tr><th>姓名</th><th>周子昂</th><th>许明哲</th><th>沈嘉诚</th><th>叶思涵</th><th>李欣怡</th><th>吴俊杰</th></tr></thead>
            <tbody><tr><td>个数/个</td><td>35</td><td>42</td><td>38</td><td>40</td><td>36</td><td>33</td></tr></tbody>
          </table>
        </div>
        <div class="table-section">
          <h4>统计表二：许明哲连续6天一分钟仰卧起坐成绩统计表</h4>
          <table class="data-table">
            <thead><tr><th>日期</th><th>周一</th><th>周二</th><th>周三</th><th>周四</th><th>周五</th><th>周六</th></tr></thead>
            <tbody><tr><td>个数/个</td><td>30</td><td>32</td><td>35</td><td>36</td><td>39</td><td>42</td></tr></tbody>
          </table>
        </div>
      </details>

      <p class="question-text">分别将两个统计表场景拖入正确的统计图篮子里：</p>

      <!-- Drag cards -->
      <div class="drag-cards">
        <div
          v-for="card in cards"
          :key="card.id"
          class="drag-card"
          :class="{ 'card-placed': card.placed, 'card-correct': card.placed && card.correct, 'card-wrong': card.placed && !card.correct }"
          :draggable="!card.placed"
          @dragstart="onDragStart($event, card)"
          @dragend="onDragEnd"
        >
          {{ card.label }}
        </div>
      </div>

      <!-- Drop zones -->
      <div class="drop-zones">
        <div
          class="drop-zone"
          :class="{ 'zone-hover': hoverZone === 'bar', 'zone-filled': zoneBar }"
          @dragover.prevent="hoverZone = 'bar'"
          @dragleave="hoverZone = null"
          @drop="onDrop($event, 'bar')"
        >
          <div class="zone-icon">📊</div>
          <div class="zone-label">条形统计图</div>
          <div class="zone-hint">用于比较数量的多少</div>
          <div v-if="zoneBar" class="zone-result" :class="zoneBar.correct ? 'correct' : 'wrong'">
            {{ zoneBar.correct ? '✓' : '✗' }} {{ zoneBar.label }}
          </div>
        </div>
        <div
          class="drop-zone"
          :class="{ 'zone-hover': hoverZone === 'line', 'zone-filled': zoneLine }"
          @dragover.prevent="hoverZone = 'line'"
          @dragleave="hoverZone = null"
          @drop="onDrop($event, 'line')"
        >
          <div class="zone-icon">📈</div>
          <div class="zone-label">折线统计图</div>
          <div class="zone-hint">用于表示数量的变化趋势</div>
          <div v-if="zoneLine" class="zone-result" :class="zoneLine.correct ? 'correct' : 'wrong'">
            {{ zoneLine.correct ? '✓' : '✗' }} {{ zoneLine.label }}
          </div>
        </div>
      </div>

      <div v-if="allPlaced" :class="allCorrect ? 'feedback-correct' : 'feedback-wrong'">
        {{ allCorrect ? '🎉 全部分类正确！' : '还有分类不对哦，点击卡片可以重新拖拽' }}
      </div>

      <div class="nav-buttons">
        <router-link to="/level/1" class="btn-secondary">上一关</router-link>
        <button v-if="!allPlaced" class="btn-primary btn-disabled" disabled>请完成拖拽</button>
        <router-link v-else to="/level/3" class="btn-primary">下一关 →</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useStudentStore } from '../stores/student.js'
import { submitLevel } from '../api.js'

const store = useStudentStore()
const hoverZone = ref(null)
const dragCard = ref(null)
const zoneBar = ref(null)
const zoneLine = ref(null)

const cards = ref([
  { id: 'table1', label: '统计表一场景\n（比较6名同学个数多少）', placed: false, correct: null, targetZone: 'bar' },
  { id: 'table2', label: '统计表二场景\n（表示许明哲6天成绩变化）', placed: false, correct: null, targetZone: 'line' },
])

const allPlaced = computed(() => cards.value.every(c => c.placed))
const allCorrect = computed(() => cards.value.every(c => c.correct === true))

function onDragStart(e, card) {
  dragCard.value = card
  e.dataTransfer.effectAllowed = 'move'
  e.dataTransfer.setData('text/plain', card.id)
}

function onDragEnd() {
  hoverZone.value = null
  dragCard.value = null
}

function onDrop(e, zone) {
  hoverZone.value = null
  if (!dragCard.value) return
  const card = cards.value.find(c => c.id === dragCard.value.id)
  if (!card || card.placed) return

  const isCorrect = card.targetZone === zone
  card.placed = true
  card.correct = isCorrect

  if (zone === 'bar') zoneBar.value = { label: card.label.split('\n')[0], correct: isCorrect }
  if (zone === 'line') zoneLine.value = { label: card.label.split('\n')[0], correct: isCorrect }

  if (allPlaced.value) {
    submitResult()
  }
}

function resetCard(card) {
  card.placed = false
  card.correct = null
  if (zoneBar.value?.label === card.label.split('\n')[0]) zoneBar.value = null
  if (zoneLine.value?.label === card.label.split('\n')[0]) zoneLine.value = null
}

async function submitResult() {
  const answer = {}
  cards.value.forEach(c => {
    const subNo = c.id === 'table1' ? '1' : '2'
    answer[subNo] = c.correct ? c.targetZone === 'bar' ? 'A' : 'B' : 'X'
  })
  const attempts = store.levels[2].attempts + 1
  const stars = allCorrect.value ? (attempts === 1 ? 3 : attempts === 2 ? 2 : 1) : 0
  store.setLevel(2, { answer, stars, attempts })
  try {
    await submitLevel(store.studentId, 2, answer, stars, attempts)
  } catch (e) { /* continue */ }
}
</script>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views-student/Level2DragDrop.vue
git commit -m "feat: add Level 2 drag-and-drop classification game"
```

---

### Task 12: Frontend — Level3CarRide.vue (汽车动画)

**Files:**
- Create: `frontend/src/views-student/Level3CarRide.vue`

- [ ] **Step 1: Create Level3CarRide.vue with car animation + chart selection**

```vue
<template>
  <div class="level-container">
    <div class="level-header">
      <span class="level-badge">第 3 关</span>
      <span class="level-title">🚗 汽车行程</span>
      <div class="star-display">
        <span v-for="s in 3" :key="s" :class="s <= store.levels[3].stars ? 'star-filled' : 'star-empty'">&#9733;</span>
      </div>
    </div>

    <div class="game-card">
      <p class="question-text">小明一家周末驾车去湿地公园游玩。汽车以50千米/时的速度行驶1小时到达湿地公园。他们一家在湿地公园玩了3小时后，驾车以原来的速度返回。以下图像中，正确的是（ ）</p>

      <!-- Car animation area -->
      <div class="car-animation-area">
        <div class="car-scene">
          <svg viewBox="0 0 600 120" class="car-scene-svg">
            <!-- Road -->
            <line x1="0" y1="95" x2="600" y2="95" stroke="#555" stroke-width="2"/>
            <line x1="0" y1="97" x2="600" y2="97" stroke="#ccc" stroke-width="1" stroke-dasharray="8 4"/>
            <!-- Home marker -->
            <text x="30" y="90" font-size="12" fill="#666">🏠 家</text>
            <!-- Park marker -->
            <text x="290" y="90" font-size="12" fill="#27ae60">🌳 湿地公园</text>
            <!-- Car -->
            <g :class="{ 'car-driving-to': phase === 1, 'car-parked': phase === 2, 'car-driving-back': phase === 3 }" class="car-group">
              <rect :x="carX" y="70" width="40" height="16" rx="4" fill="#e74c3c"/>
              <circle :cx="carX + 8" cy="88" r="5" fill="#333"/>
              <circle :cx="carX + 32" cy="88" r="5" fill="#333"/>
              <!-- Window -->
              <rect :x="carX + 26" y="73" width="10" height="6" rx="1" fill="#aed6f1"/>
            </g>
          </svg>
        </div>
        <div class="car-controls">
          <button v-if="phase === 0" @click="playAnimation" class="btn-primary play-btn">▶ 播放动画</button>
          <span v-else-if="phase === 1" class="phase-label">🚗 行驶中：去公园（1小时）</span>
          <span v-else-if="phase === 2" class="phase-label">🌳 游玩中（3小时）</span>
          <span v-else-if="phase === 3" class="phase-label">🚗 返程中（1小时）</span>
          <span v-else class="phase-label">✅ 动画结束，请选择正确图像</span>
        </div>
      </div>

      <!-- Phase label and description -->
      <div class="phase-desc">
        <span v-if="phase >= 0">离家距离变化：0km → 50km（行驶1h）→ 50km（游玩3h）→ 0km（返回1h）</span>
      </div>

      <!-- Chart options (shown after animation) -->
      <div v-if="phase === 4" class="chart-options-grid">
        <label
          v-for="(chart, key) in q3Charts"
          :key="key"
          class="chart-option"
          :class="{ selected: selectedAnswer === key }"
        >
          <input type="radio" name="q3" :value="key" :checked="selectedAnswer === key" @change="selectAnswer(key)" class="chart-radio"/>
          <div class="chart-label">{{ key }}</div>
          <svg :viewBox="chart.viewBox" class="chart-svg">
            <line v-for="g in chart.gridY" :key="'gy'+g.y" :x1="chart.margin.left" :y1="g.y" :x2="chart.plotRight" :y2="g.y" stroke="#e8e8e8" stroke-width="0.5"/>
            <line v-for="g in chart.gridX" :key="'gx'+g.x" :x1="g.x" :y1="chart.plotTop" :x2="g.x" :y2="chart.plotBottom" stroke="#e8e8e8" stroke-width="0.5"/>
            <line :x1="chart.margin.left" :y1="chart.plotTop" :x2="chart.margin.left" :y2="chart.plotBottom" stroke="#333" stroke-width="1.2"/>
            <line :x1="chart.margin.left" :y1="chart.plotBottom" :x2="chart.plotRight" :y2="chart.plotBottom" stroke="#333" stroke-width="1.2"/>
            <text v-for="t in chart.yTicks" :key="'yt'+t.value" :x="chart.margin.left - 6" :y="t.y" text-anchor="end" font-size="10" fill="#555" dominant-baseline="middle">{{ t.value }}</text>
            <text v-for="t in chart.xTicks" :key="'xt'+t.value" :x="t.x" :y="chart.plotBottom + 18" text-anchor="middle" font-size="10" fill="#555">{{ t.value }}</text>
            <text :x="12" :y="chart.plotTop + (chart.plotBottom - chart.plotTop) / 2" text-anchor="middle" font-size="12" fill="#333" :transform="'rotate(-90, 12, ' + (chart.plotTop + (chart.plotBottom - chart.plotTop) / 2) + ')'">{{ chart.yLabel }}</text>
            <text :x="chart.margin.left + (chart.plotRight - chart.margin.left) / 2" :y="chart.plotBottom + 34" text-anchor="middle" font-size="12" fill="#333">{{ chart.xLabel }}</text>
            <polyline :points="chart.linePoints" fill="none" stroke="#4a90d9" stroke-width="2.5" stroke-linejoin="round"/>
            <circle v-for="(pt, i) in chart.dataPoints" :key="'dp'+i" :cx="pt.x" :cy="pt.y" r="3.5" fill="#4a90d9"/>
          </svg>
        </label>
      </div>

      <div v-if="feedback" :class="feedback === 'correct' ? 'feedback-correct' : 'feedback-wrong'">
        {{ feedback === 'correct' ? '🎉 正确！小车顺利到达！' : '🤔 这路线不对哦，再想想' }}
      </div>

      <div class="nav-buttons">
        <router-link to="/level/2" class="btn-secondary">上一关</router-link>
        <router-link to="/level/4" class="btn-primary">下一关 →</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useStudentStore } from '../stores/student.js'
import { submitLevel } from '../api.js'

const store = useStudentStore()
const phase = ref(0) // 0=idle, 1=driving to, 2=playing, 3=driving back, 4=show charts
const carX = ref(30)
const selectedAnswer = ref(null)
const feedback = ref(null)

function playAnimation() {
  phase.value = 1
  // Drive to park (1h at 50km/h → 50km)
  carX.value = 30
  const interval = setInterval(() => {
    carX.value += 2.2
    if (carX.value >= 250) {
      carX.value = 250
      clearInterval(interval)
      // Play for 3 hours
      phase.value = 2
      setTimeout(() => {
        // Drive back
        phase.value = 3
        const backInterval = setInterval(() => {
          carX.value -= 2.2
          if (carX.value <= 30) {
            carX.value = 30
            clearInterval(backInterval)
            phase.value = 4 // Show charts
          }
        }, 20)
      }, 2000) // 2s to represent 3h
    }
  }, 20)
}

async function selectAnswer(key) {
  selectedAnswer.value = key
  const isCorrect = key === 'D'
  const attempts = store.levels[3].attempts + 1
  const stars = isCorrect ? (attempts === 1 ? 3 : attempts === 2 ? 2 : 1) : 0
  feedback.value = isCorrect ? 'correct' : 'wrong'
  store.setLevel(3, { answer: key, stars, attempts })
  try {
    await submitLevel(store.studentId, 3, key, stars, attempts)
  } catch (e) { /* continue */ }
}

// Chart data (same as old Q7 charts)
function makeChart(yLabel, timePoints) {
  const margin = { left: 55, top: 18, right: 20, bottom: 35 }
  const viewBox = '0 0 420 300'
  const plotRight = 400
  const plotBottom = 268
  const plotTop = margin.top
  const plotW = plotRight - margin.left
  const plotH = plotBottom - plotTop

  const xScale = (t) => margin.left + (t / 6) * plotW
  const yScale = (v) => plotBottom - (v / 100) * plotH

  const gridY = [0, 25, 50, 75, 100].map(v => ({ y: yScale(v) }))
  const gridX = [0, 1, 2, 3, 4, 5, 6].map(t => ({ x: xScale(t) }))
  const yTicks = [0, 25, 50, 75, 100].map(v => ({ value: v, y: yScale(v) }))
  const xTicks = [0, 1, 2, 3, 4, 5, 6].map(t => ({ value: t, x: xScale(t) }))

  const dataPoints = timePoints.map(([t, v]) => ({ x: xScale(t), y: yScale(v) }))
  const linePoints = dataPoints.map(p => `${p.x},${p.y}`).join(' ')

  return {
    viewBox, margin, plotRight, plotTop, plotBottom,
    gridY, gridX, yTicks, xTicks,
    yLabel: yLabel.replace(/\//g, ' / '),
    xLabel: '时间/时',
    dataPoints, linePoints,
  }
}

const q3Charts = computed(() => ({
  A: makeChart('行驶路程/千米', [[0,0],[1,50],[4,50],[5,100],[6,100]]),
  B: makeChart('行驶路程/千米', [[0,0],[1,50],[3,50],[4,100],[6,100]]),
  C: makeChart('离家距离/千米', [[0,0],[1,50],[4,50],[5,100],[6,100]]),
  D: makeChart('离家距离/千米', [[0,0],[1,50],[4,50],[5,25],[6,0]]),
}))
</script>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views-student/Level3CarRide.vue
git commit -m "feat: add Level 3 car ride animation game"
```

---

### Task 13: Frontend — Level4WaterTank.vue (水位实验室)

**Files:**
- Create: `frontend/src/views-student/Level4WaterTank.vue`

- [ ] **Step 1: Create Level4WaterTank.vue with water tank animation + chart selection**

```vue
<template>
  <div class="level-container">
    <div class="level-header">
      <span class="level-badge">第 4 关</span>
      <span class="level-title">🧪 水位实验室</span>
      <div class="star-display">
        <span v-for="s in 3" :key="s" :class="s <= store.levels[4].stars ? 'star-filled' : 'star-empty'">&#9733;</span>
      </div>
    </div>

    <div class="game-card">
      <p class="question-text">容器中有一些水，小夏将一根圆柱形铁棒垂直匀速地放入水中，水溢出 800 毫升水。随后又将铁棒匀速取出。下面选项中，正确反映了容器中水位变化情况的是（ ）</p>

      <!-- Water tank animation -->
      <div class="tank-animation-area">
        <div class="tank-scene">
          <svg viewBox="0 0 300 280" class="tank-svg">
            <!-- Tank -->
            <rect x="60" y="30" width="180" height="220" fill="none" stroke="#555" stroke-width="2"/>
            <!-- Original water level dashed line -->
            <line x1="55" y1="120" x2="245" y2="120" stroke="#e74c3c" stroke-width="1.5" stroke-dasharray="6 3"/>
            <text x="248" y="124" font-size="11" fill="#e74c3c">原始水位</text>
            <!-- Water -->
            <rect x="62" y="122" width="176" :height="waterHeight" fill="#4a90d9" opacity="0.5" class="water-fill"/>
            <!-- Iron rod -->
            <rect x="135" :y="rodY" width="30" :height="rodHeight" rx="3" fill="#666" class="rod-move"/>
            <!-- Labels -->
            <text x="150" y="270" text-anchor="middle" font-size="13" fill="#555">容器</text>
          </svg>
        </div>
        <div class="tank-controls">
          <button v-if="tankPhase === 0" @click="playTankAnimation" class="btn-primary play-btn">▶ 播放实验</button>
          <span v-else-if="tankPhase === 1" class="phase-label">⬇ 铁棒放入中...</span>
          <span v-else-if="tankPhase === 2" class="phase-label">💧 水溢出中...</span>
          <span v-else-if="tankPhase === 3" class="phase-label">⬆ 铁棒取出中...</span>
          <span v-else class="phase-label">✅ 实验结束，请选择正确图像</span>
        </div>
      </div>

      <!-- Key insight -->
      <div v-if="tankPhase === 4" class="insight-box">
        <strong>思考：</strong>水溢出 800 毫升后，这些水不会回到容器中。铁棒取出后，水位会低于原始水位。
      </div>

      <!-- Chart options -->
      <div v-if="tankPhase === 4" class="chart-options-grid">
        <label v-for="(desc, key) in chartDescriptions" :key="key"
          class="chart-option"
          :class="{ selected: selectedAnswer === key }"
        >
          <input type="radio" name="q4" :value="key" :checked="selectedAnswer === key" @change="selectAnswer(key)" class="chart-radio"/>
          <div class="chart-label">{{ key }}</div>
          <div class="chart-desc-text">{{ desc }}</div>
          <svg :viewBox="tankCharts[key].viewBox" class="chart-svg">
            <!-- Dashed line for original water level -->
            <line :x1="tankCharts[key].margin.left" :y1="tankCharts[key].dashedY" :x2="tankCharts[key].plotRight" :y2="tankCharts[key].dashedY" stroke="#e74c3c" stroke-width="1.2" stroke-dasharray="5 3"/>
            <text :x="tankCharts[key].plotRight + 4" :y="tankCharts[key].dashedY + 3" font-size="9" fill="#e74c3c">原水位</text>
            <!-- Grid -->
            <line v-for="g in tankCharts[key].gridY" :key="'gy'+g.y" :x1="tankCharts[key].margin.left" :y1="g.y" :x2="tankCharts[key].plotRight" :y2="g.y" stroke="#e8e8e8" stroke-width="0.5"/>
            <!-- Axes -->
            <line :x1="tankCharts[key].margin.left" :y1="tankCharts[key].plotTop" :x2="tankCharts[key].margin.left" :y2="tankCharts[key].plotBottom" stroke="#333" stroke-width="1.2"/>
            <line :x1="tankCharts[key].margin.left" :y1="tankCharts[key].plotBottom" :x2="tankCharts[key].plotRight" :y2="tankCharts[key].plotBottom" stroke="#333" stroke-width="1.2"/>
            <!-- Data line -->
            <polyline :points="tankCharts[key].linePoints" fill="none" stroke="#4a90d9" stroke-width="2.5" stroke-linejoin="round"/>
            <circle v-for="(pt, i) in tankCharts[key].dataPoints" :key="'dp'+i" :cx="pt.x" :cy="pt.y" r="3.5" fill="#4a90d9"/>
            <!-- Labels -->
            <text :x="tankCharts[key].margin.left + (tankCharts[key].plotRight - tankCharts[key].margin.left) / 2" :y="tankCharts[key].plotBottom + 24" text-anchor="middle" font-size="10" fill="#555">时间</text>
            <text :x="10" :y="tankCharts[key].plotTop + (tankCharts[key].plotBottom - tankCharts[key].plotTop) / 2" text-anchor="middle" font-size="10" fill="#333" :transform="'rotate(-90, 10, ' + (tankCharts[key].plotTop + (tankCharts[key].plotBottom - tankCharts[key].plotTop) / 2) + ')'">深度</text>
          </svg>
        </label>
      </div>

      <div v-if="feedback" :class="feedback === 'correct' ? 'feedback-correct' : 'feedback-wrong'">
        {{ feedback === 'correct' ? '🎉 正确！水溢出后不会回来，所以取出铁棒后水位低于原水位！' : '💡 提示：水溢出后没有回到容器中，取出铁棒后水面应该低于原来的虚线水位。' }}
      </div>

      <div class="nav-buttons">
        <router-link to="/level/3" class="btn-secondary">上一关</router-link>
        <router-link to="/level/5" class="btn-primary">下一关 →</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useStudentStore } from '../stores/student.js'
import { submitLevel } from '../api.js'

const store = useStudentStore()
const tankPhase = ref(0)
const waterHeight = ref(98)
const rodY = ref(40)
const rodHeight = ref(100)
const selectedAnswer = ref(null)
const feedback = ref(null)

const chartDescriptions = {
  A: '终点低于虚线（原水位）',
  B: '终点继续上升',
  C: '终点回到虚线（原水位）',
  D: '终点高于虚线（原水位）',
}

function playTankAnimation() {
  tankPhase.value = 1
  // Rod goes down
  const downInterval = setInterval(() => {
    rodY.value += 1.5
    rodHeight.value -= 1.5
    if (rodY.value >= 100) {
      clearInterval(downInterval)
      tankPhase.value = 2
      waterHeight.value = 158 // water rises above original
      // Water overflows
      setTimeout(() => {
        tankPhase.value = 3
        // Rod goes up
        const upInterval = setInterval(() => {
          rodY.value -= 1.5
          rodHeight.value += 1.5
          if (rodY.value <= 40) {
            clearInterval(upInterval)
            waterHeight.value = 70 // lower than original (overflow lost)
            tankPhase.value = 4
          }
        }, 20)
      }, 1500)
    }
  }, 20)
}

async function selectAnswer(key) {
  selectedAnswer.value = key
  const isCorrect = key === 'A'
  const attempts = store.levels[4].attempts + 1
  const stars = isCorrect ? (attempts === 1 ? 3 : attempts === 2 ? 2 : 1) : 0
  feedback.value = isCorrect ? 'correct' : 'wrong'
  store.setLevel(4, { answer: key, stars, attempts })
  try {
    await submitLevel(store.studentId, 4, key, stars, attempts)
  } catch (e) { /* continue */ }
}

// Tank chart configurations for 4 options
function makeTankChart(timePoints) {
  const margin = { left: 40, top: 15, right: 55, bottom: 35 }
  const viewBox = '0 0 380 280'
  const plotRight = 320
  const plotBottom = 250
  const plotTop = margin.top
  const plotW = plotRight - margin.left
  const plotH = plotBottom - plotTop
  const dashedY = plotBottom - 0.4 * plotH // original water level

  const xScale = (t) => margin.left + (t / 6) * plotW
  const yScale = (v) => plotBottom - (v / 100) * plotH * 0.7

  const gridY = [0, 25, 50, 75, 100].map(v => ({ y: yScale(v) }))
  const dataPoints = timePoints.map(([t, v]) => ({ x: xScale(t), y: yScale(v) }))
  const linePoints = dataPoints.map(p => `${p.x},${p.y}`).join(' ')

  return { viewBox, margin, plotRight, plotTop, plotBottom, dashedY, gridY, dataPoints, linePoints }
}

const tankCharts = computed(() => ({
  A: makeTankChart([[0,40],[2,55],[5,55],[6,25]]), // ends below dashed
  B: makeTankChart([[0,40],[2,55],[5,55],[6,80]]), // keeps rising
  C: makeTankChart([[0,40],[2,55],[5,55],[6,40]]), // back to original
  D: makeTankChart([[0,40],[2,55],[5,55],[6,50]]), // above original
}))
</script>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views-student/Level4WaterTank.vue
git commit -m "feat: add Level 4 water tank experiment game"
```

---

### Task 14: Frontend — Level5Thermometer.vue (温度填空)

**Files:**
- Create: `frontend/src/views-student/Level5Thermometer.vue`

- [ ] **Step 1: Create Level5Thermometer.vue with temperature chart + fill-blank + thermometer animation**

```vue
<template>
  <div class="level-container">
    <div class="level-header">
      <span class="level-badge">第 5 关</span>
      <span class="level-title">🌡️ 温度实验室</span>
      <div class="star-display">
        <span v-for="s in 3" :key="s" :class="s <= store.levels[5].stars ? 'star-filled' : 'star-empty'">&#9733;</span>
      </div>
    </div>

    <div class="game-card">
      <p class="question-text">小宇在做"一壶水加热"实验时，记录了水温变化情况，并制成统计图。请根据统计图填空：</p>

      <!-- Temperature chart -->
      <div class="chart-container">
        <svg :viewBox="chart.viewBox" class="fill-blank-chart-svg">
          <line v-for="g in chart.gridY" :key="'gy'+g.value" :x1="chart.margin.left" :y1="g.y" :x2="chart.plotRight" :y2="g.y" stroke="#e8e8e8" stroke-width="0.5"/>
          <line v-for="g in chart.gridX" :key="'gx'+g.value" :x1="g.x" :y1="chart.plotTop" :x2="g.x" :y2="chart.plotBottom" stroke="#e8e8e8" stroke-width="0.5"/>
          <line :x1="chart.margin.left" :y1="chart.plotTop" :x2="chart.margin.left" :y2="chart.plotBottom" stroke="#333" stroke-width="1.2"/>
          <line :x1="chart.margin.left" :y1="chart.plotBottom" :x2="chart.plotRight" :y2="chart.plotBottom" stroke="#333" stroke-width="1.2"/>
          <text v-for="t in chart.yTicks" :key="'yt'+t.value" :x="chart.margin.left - 8" :y="t.y" text-anchor="end" font-size="11" fill="#555" dominant-baseline="middle">{{ t.value }}</text>
          <text v-for="t in chart.xTicks" :key="'xt'+t.value" :x="t.x" :y="chart.plotBottom + 18" text-anchor="middle" font-size="11" fill="#555">{{ t.value }}</text>
          <text :x="14" :y="chart.yLabelY" text-anchor="middle" font-size="13" fill="#333" :transform="'rotate(-90, 14, ' + chart.yLabelY + ')'">水温/℃</text>
          <text :x="chart.margin.left + (chart.plotRight - chart.margin.left) / 2" :y="chart.plotBottom + 36" text-anchor="middle" font-size="13" fill="#333">时间/分</text>
          <polyline :points="chart.linePoints" fill="none" stroke="#4a90d9" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"/>
          <circle v-for="(pt, i) in chart.dataPoints" :key="'dp'+i" :cx="pt.x" :cy="pt.y" r="4" fill="#4a90d9"/>
          <text v-for="(pt, i) in chart.dataPoints" :key="'dt'+i" :x="pt.x" :y="pt.labelY" text-anchor="middle" font-size="10" fill="#333">{{ temps[i] }}</text>
        </svg>
      </div>

      <!-- Fill blanks -->
      <div class="fill-blank-paragraph">
        <p>
          加热前水温是
          <input type="text" v-model="q5[1]" class="blank-input" @input="onBlankInput(1)" />
          ℃，水加热到 60℃ 时，用了
          <input type="text" v-model="q5[2]" class="blank-input" @input="onBlankInput(2)" />
          分钟，烧开这壶水一共用了
          <input type="text" v-model="q5[3]" class="blank-input" @input="onBlankInput(3)" />
          分钟。如果持续加热到第 16 分钟，此时水温是
          <input type="text" v-model="q5[4]" class="blank-input" @input="onBlankInput(4)" />
          ℃。
        </p>
      </div>

      <!-- Thermometer visualization -->
      <div class="thermometer-area">
        <div class="thermometer">
          <div class="thermo-tube">
            <div class="thermo-mercury" :style="{ height: thermoHeight + '%' }"></div>
          </div>
          <div class="thermo-bulb">{{ thermoHeight >= 90 ? '💨' : '🌡️' }}</div>
        </div>
        <div class="thermo-labels">
          <span v-for="t in [100, 80, 60, 40, 20, 0]" :key="t">{{ t }}℃</span>
        </div>
        <div class="thermo-status">
          已完成 {{ filledCount }} / 4 个空
          <span v-if="filledCount === 4"> — {{ allCorrect ? '🎉 全部正确！水烧开了！' : '还有空不对哦，再检查一下' }}</span>
        </div>
      </div>

      <div class="nav-buttons">
        <router-link to="/level/4" class="btn-secondary">上一关</router-link>
        <router-link to="/submit-success" class="btn-primary">完成闯关！</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useStudentStore } from '../stores/student.js'
import { submitLevel } from '../api.js'

const store = useStudentStore()
const temps = [25, 28, 35, 46, 60, 73, 84, 90, 93, 96, 98, 100]
const correctAnswers = { 1: '25', 2: '4', 3: '11', 4: '100' }
const q5 = reactive({ 1: '', 2: '', 3: '', 4: '' })
const filledCount = ref(0)
const allCorrect = ref(false)

onMounted(() => {
  if (store.levels[5].answer) {
    Object.assign(q5, store.levels[5].answer)
    checkAnswers()
  }
})

function onBlankInput(subNo) {
  const filled = Object.values(q5).filter(v => v.trim() !== '').length
  filledCount.value = filled
  if (filled === 4) {
    checkAnswers()
    submitNow()
  }
}

function checkAnswers() {
  allCorrect.value = Object.entries(q5).every(([k, v]) => v.trim() === correctAnswers[k])
}

async function submitNow() {
  const answer = { ...q5 }
  const attempts = store.levels[5].attempts + 1
  const stars = allCorrect.value ? (attempts === 1 ? 3 : attempts === 2 ? 2 : 1) : 0
  store.setLevel(5, { answer, stars, attempts })
  try {
    await submitLevel(store.studentId, 5, answer, stars, attempts)
  } catch (e) { /* continue */ }
}

const thermoHeight = computed(() => {
  const filled = Object.values(q5).filter(v => v.trim() !== '').length
  const correct = Object.entries(q5).filter(([k, v]) => v.trim() === correctAnswers[k]).length
  return (correct / 4) * 100
})

// Chart config (reuse from old Q8)
const chart = computed(() => {
  const margin = { left: 50, top: 20, right: 20, bottom: 40 }
  const plotRight = 660, plotBottom = 420, plotTop = margin.top
  const plotW = plotRight - margin.left, plotH = plotBottom - plotTop
  const xScale = (t) => margin.left + (t / 12) * plotW
  const yScale = (v) => plotBottom - (v / 110) * plotH

  const yTickValues = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110]
  const xTickValues = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
  const gridY = yTickValues.map(v => ({ value: v, y: yScale(v) }))
  const gridX = xTickValues.map(v => ({ value: v, x: xScale(v) }))
  const yTicks = [0, 20, 40, 60, 80, 100].map(v => ({ value: v, y: yScale(v) }))
  const xTicks = [0, 2, 4, 6, 8, 10, 12].map(v => ({ value: v, x: xScale(v) }))

  const dataPoints = temps.map((t, i) => {
    const x = xScale(i), y = yScale(t)
    const offset = i >= 8 ? (i % 2 === 0 ? -14 : 18) : -14
    return { x, y, labelY: y + offset }
  })
  const linePoints = dataPoints.map(p => `${p.x},${p.y}`).join(' ')

  return { viewBox: '0 0 700 480', margin, plotRight, plotTop, plotBottom, gridY, gridX, yTicks, xTicks, dataPoints, linePoints, yLabelY: plotTop + (plotBottom - plotTop) / 2 }
})
</script>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views-student/Level5Thermometer.vue
git commit -m "feat: add Level 5 thermometer fill-blank game"
```

---

### Task 15: Frontend — Dashboard.vue + StudentDetail.vue (teacher views)

**Files:**
- Modify: `frontend/src/views-teacher/Dashboard.vue`
- Modify: `frontend/src/views-teacher/StudentDetail.vue`

- [ ] **Step 1: Update Dashboard.vue for 5 questions + stars + chart section**

Replace the template section after the stats-row (the table-wrapper div, lines 23–55) in `Dashboard.vue` with:

```html
      <div class="chart-section">
        <h3>📊 统计图生成</h3>
        <div class="chart-buttons">
          <button @click="showChart('questions')" class="btn-secondary">各题正确率柱状图</button>
          <button @click="showChart('stars')" class="btn-secondary">星星分布柱状图</button>
        </div>
        <div v-if="chartSrc" class="chart-preview">
          <img :src="chartSrc" alt="统计图" />
          <br/>
          <a :href="chartSrc" download class="btn-small" style="margin-top:8px;display:inline-block;">下载图片</a>
        </div>
      </div>

      <div class="table-wrapper">
        <table class="dashboard-table">
          <thead>
            <tr>
              <th>姓名</th>
              <th v-for="q in 5" :key="q">Q{{ q }}</th>
              <th>星星</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="s in students" :key="s.id">
              <td class="name-cell">{{ s.name }}</td>
              <td v-for="q in 5" :key="q" class="score-cell">
                <span v-if="q === 5">
                  <span v-if="getQ5Summary(s) !== null" :class="getQ5Summary(s) === 4 ? 'correct' : 'wrong'">{{ getQ5Summary(s) }}/4</span>
                  <span v-else class="empty">-</span>
                </span>
                <span v-else-if="q === 2">
                  <span v-if="getQ2Summary(s) !== null" :class="getQ2Summary(s) === 2 ? 'correct' : 'wrong'">{{ getQ2Summary(s) }}/2</span>
                  <span v-else class="empty">-</span>
                </span>
                <span v-else>
                  <span v-if="scoresVal(s, q) === true" class="correct">&#10003;</span>
                  <span v-else-if="scoresVal(s, q) === false" class="wrong">&#10007;</span>
                  <span v-else class="empty">-</span>
                </span>
              </td>
              <td class="score-cell">
                <span v-if="s.total_stars > 0" class="correct">{{ s.total_stars }}/15</span>
                <span v-else class="empty">-</span>
              </td>
              <td class="action-cell">
                <router-link :to="'/teacher/student/' + s.id" class="view-link">查看</router-link>
                <button @click="confirmDelete(s)" class="btn-delete">删除</button>
              </td>
            </tr>
            <tr v-if="students.length === 0">
              <td colspan="8" class="empty-row">暂无学生数据</td>
            </tr>
          </tbody>
        </table>
      </div>
```

Replace the script section's `getQ8Summary` function with:

```javascript
const chartSrc = ref('')

function scoresVal(s, q) {
  if (s.scores[q] !== undefined) return s.scores[q]
  return null
}

function getQ2Summary(s) {
  const keys = ['2_1', '2_2']
  const hasAny = keys.some(k => k in s.scores)
  if (!hasAny) return null
  return keys.filter(k => s.scores[k] === true).length
}

function getQ5Summary(s) {
  const keys = ['5_1', '5_2', '5_3', '5_4']
  const hasAny = keys.some(k => k in s.scores)
  if (!hasAny) return null
  return keys.filter(k => s.scores[k] === true).length
}

function showChart(type) {
  chartSrc.value = `/api/teacher/chart?type=${type}&t=${Date.now()}`
}
```

- [ ] **Step 2: Update StudentDetail.vue for 5 questions + stars**

Replace the entire `<template>` section of `StudentDetail.vue`:

```html
<template>
  <div class="dashboard-container">
    <header class="dashboard-header">
      <h1>{{ detail?.name }} · 答题详情</h1>
      <router-link to="/teacher/dashboard" class="btn-small">← 返回概览</router-link>
    </header>

    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="detail" class="detail-content">
      <div class="content-card">
        <h3>答题记录</h3>
        <table class="data-table">
          <thead><tr><th>题号</th><th>子题</th><th>学生答案</th><th>正确答案</th><th>结果</th></tr></thead>
          <tbody>
            <tr v-for="a in detail.answers" :key="a.question_no + '_' + a.sub_no">
              <td>Q{{ a.question_no }}</td>
              <td>{{ a.sub_no > 0 ? '第' + a.sub_no + '空' : '-' }}</td>
              <td>{{ a.answer || '-' }}</td>
              <td>{{ getCorrectAnswerDisplay(a.question_no, a.sub_no) }}</td>
              <td :class="a.is_correct ? 'correct' : 'wrong'">{{ a.is_correct ? '✓' : '✗' }}</td>
            </tr>
          </tbody>
        </table>

        <h3 v-if="detail.stars && detail.stars.length > 0" style="margin-top: 20px;">闯关星级</h3>
        <table v-if="detail.stars && detail.stars.length > 0" class="data-table">
          <thead><tr><th>关卡</th><th>星级</th><th>尝试次数</th></tr></thead>
          <tbody>
            <tr v-for="s in detail.stars" :key="s.level_no">
              <td>第{{ s.level_no }}关</td>
              <td>
                <span v-for="i in 3" :key="i" :style="{ color: i <= s.stars ? '#f5a623' : '#ddd' }">&#9733;</span>
                ({{ s.stars }}/3)
              </td>
              <td>{{ s.attempts }} 次</td>
            </tr>
          </tbody>
        </table>
        <p v-if="detail.total_stars !== undefined" style="margin-top: 12px; font-weight: 600;">
          总星数：{{ detail.total_stars }} / 15
        </p>
      </div>
    </div>
  </div>
</template>
```

Replace the `<script setup>` section:

```javascript
<script setup>
import { ref, onMounted } from 'vue'
import { getStudentDetail } from '../api.js'

const props = defineProps({ id: String })
const detail = ref(null)
const loading = ref(true)
const error = ref('')

const correctAnswers = {
  1: { 0: 'A' },
  2: { 1: 'A', 2: 'B' },
  3: { 0: 'D' },
  4: { 0: 'A' },
  5: { 1: '25', 2: '4', 3: '11', 4: '100' },
}

function getCorrectAnswerDisplay(qno, subNo) {
  const q = correctAnswers[qno]
  if (!q) return '-'
  return q[subNo] || '-'
}

onMounted(async () => {
  try {
    const res = await getStudentDetail(props.id)
    detail.value = res.data
  } catch (e) {
    error.value = '加载失败'
  } finally {
    loading.value = false
  }
})
</script>
```

- [ ] **Step 3: Verify both pages**

Run frontend dev server, login as teacher, verify dashboard shows 5 questions + stars + chart buttons.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/views-teacher/Dashboard.vue frontend/src/views-teacher/StudentDetail.vue
git commit -m "feat: update teacher views for 5 levels and bar chart"
```

---

### Task 16: Frontend — style.css (game-specific styles)

**Files:**
- Modify: `frontend/src/style.css`

- [ ] **Step 1: Append game-specific CSS classes**

Add the following CSS after the existing responsive section at the end of `style.css`:

```css
/* ===== Level Game Styles ===== */
.level-container { max-width: 1000px; margin: 0 auto; padding: 20px; }
.level-header { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.level-badge { background: var(--primary-dark); color: #fff; padding: 4px 16px; border-radius: 16px; font-size: 15px; font-weight: 600; }
.level-title { font-size: 22px; font-weight: 700; color: var(--text); }
.star-display { margin-left: auto; font-size: 22px; }
.star-filled { color: #f5a623; }
.star-empty { color: #ddd; }

.game-card { background: var(--card-bg); border-radius: var(--radius); box-shadow: var(--shadow); padding: 36px; }

/* Balloon game (Level 1) */
.balloon-field { display: flex; justify-content: center; gap: 40px; margin: 32px 0; flex-wrap: wrap; }
.balloon-pair { display: flex; flex-direction: column; align-items: center; gap: 8px; cursor: pointer; transition: transform 0.3s; }
.balloon-pair:hover { transform: scale(1.05); }
.balloon { display: flex; flex-direction: column; align-items: center; }
.balloon-body { width: 90px; height: 110px; border-radius: 50% 50% 50% 50% / 40% 40% 60% 60%; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 2px; transition: all 0.3s; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
.balloon-label { font-size: 11px; color: rgba(255,255,255,0.85); font-weight: 600; }
.balloon-text { font-size: 13px; color: #fff; font-weight: 700; text-align: center; padding: 0 8px; }
.balloon-string { width: 2px; height: 30px; background: #999; }
.pair-letter { font-size: 22px; font-weight: 800; color: var(--primary-dark); margin-top: 4px; }
.balloon-hit { animation: balloonPop 0.4s ease-out forwards; }
.balloon-hit .balloon-body { transform: scale(0); opacity: 0; }
.balloon-shake { animation: balloonShake 0.5s ease; }
@keyframes balloonPop {
  0% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.2); opacity: 0.5; }
  100% { transform: scale(0); opacity: 0; }
}
@keyframes balloonShake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-8px); }
  75% { transform: translateX(8px); }
}

/* Drag drop game (Level 2) */
.drag-cards { display: flex; gap: 20px; margin: 20px 0; justify-content: center; flex-wrap: wrap; }
.drag-card { padding: 20px 28px; background: #fff; border: 2px dashed var(--primary); border-radius: 10px; cursor: grab; font-size: 15px; font-weight: 500; text-align: center; white-space: pre-line; transition: all 0.2s; user-select: none; }
.drag-card:hover { background: #f0f6ff; }
.drag-card:active { cursor: grabbing; }
.drag-card.card-placed { pointer-events: none; }
.drag-card.card-correct { border-color: var(--success); background: #e6f4ea; }
.drag-card.card-wrong { border-color: var(--danger); background: #fce4ec; }
.drop-zones { display: flex; gap: 20px; margin: 20px 0; justify-content: center; flex-wrap: wrap; }
.drop-zone { flex: 1; min-width: 200px; max-width: 320px; padding: 24px; border: 3px dashed var(--border); border-radius: 12px; text-align: center; transition: all 0.2s; }
.drop-zone.zone-hover { border-color: var(--primary); background: #f0f6ff; }
.drop-zone.zone-filled { border-style: solid; }
.zone-icon { font-size: 36px; margin-bottom: 8px; }
.zone-label { font-size: 18px; font-weight: 600; margin-bottom: 4px; }
.zone-hint { font-size: 13px; color: var(--text-secondary); }
.zone-result { margin-top: 12px; font-size: 15px; font-weight: 600; padding: 6px 12px; border-radius: 6px; }
.zone-result.correct { background: #e6f4ea; color: #1b7a3d; }
.zone-result.wrong { background: #fce4ec; color: #c0392b; }

/* Car animation (Level 3) */
.car-animation-area { margin: 20px 0; padding: 16px; background: #fafbfc; border-radius: 8px; border: 1px solid var(--border); }
.car-scene-svg { display: block; width: 100%; height: auto; }
.car-group { transition: none; }
.car-controls { text-align: center; margin-top: 8px; }
.play-btn { width: auto !important; padding: 10px 32px !important; font-size: 18px !important; }
.phase-label { font-size: 16px; color: var(--primary-dark); font-weight: 600; }
.phase-desc { margin-top: 8px; font-size: 14px; color: var(--text-secondary); text-align: center; }

/* Tank animation (Level 4) */
.tank-animation-area { margin: 20px 0; padding: 16px; background: #fafbfc; border-radius: 8px; border: 1px solid var(--border); text-align: center; }
.tank-svg { display: block; margin: 0 auto; max-width: 300px; }
.tank-controls { margin-top: 8px; }
.insight-box { padding: 14px 18px; background: #fff8e1; border-left: 4px solid #f5a623; border-radius: 6px; margin: 16px 0; font-size: 15px; color: #8d6e00; }
.chart-desc-text { font-size: 12px; color: var(--text-secondary); margin-top: 4px; text-align: center; }

/* Thermometer (Level 5) */
.thermometer-area { display: flex; align-items: flex-end; gap: 16px; margin: 20px 0; padding: 16px; background: #fafbfc; border-radius: 8px; }
.thermometer { display: flex; flex-direction: column; align-items: center; }
.thermo-tube { width: 30px; height: 180px; background: #eee; border-radius: 15px; overflow: hidden; position: relative; border: 2px solid #ccc; }
.thermo-mercury { position: absolute; bottom: 0; width: 100%; background: linear-gradient(to top, #e74c3c, #ff6b6b); border-radius: 0 0 13px 13px; transition: height 0.5s ease; }
.thermo-bulb { font-size: 24px; margin-top: 4px; }
.thermo-labels { display: flex; flex-direction: column; justify-content: space-between; height: 180px; font-size: 12px; color: var(--text-secondary); }
.thermo-status { font-size: 15px; color: var(--text); margin-left: 16px; }
.thermo-status span { font-weight: 600; }

/* Feedback */
.feedback-correct { padding: 14px 18px; background: #e6f4ea; color: #1b7a3d; border-radius: 8px; font-size: 17px; font-weight: 600; text-align: center; margin: 16px 0; }
.feedback-wrong { padding: 14px 18px; background: #fff3cd; color: #856404; border-radius: 8px; font-size: 16px; text-align: center; margin: 16px 0; }

/* Stars breakdown (SubmitSuccess) */
.stars-breakdown { margin: 20px 0; text-align: left; }
.star-row { display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid var(--border); }
.star-level { font-size: 16px; font-weight: 500; }

/* Chart download area (Dashboard) */
.chart-section { background: var(--card-bg); border-radius: var(--radius); box-shadow: var(--shadow); padding: 20px 24px; margin-bottom: 20px; }
.chart-section h3 { font-size: 18px; color: var(--primary-dark); margin-bottom: 12px; }
.chart-buttons { display: flex; gap: 12px; flex-wrap: wrap; }
.chart-preview { margin-top: 16px; text-align: center; }
.chart-preview img { max-width: 100%; border-radius: 8px; border: 1px solid var(--border); }

/* Disabled button */
.btn-disabled { opacity: 0.5; pointer-events: none; }
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/style.css
git commit -m "feat: add game-specific CSS styles for 5 levels"
```

---

### Task 17: Cleanup — remove old components

**Files:**
- Delete: `frontend/src/views-student/DataPreview.vue`
- Delete: `frontend/src/views-student/ChoiceQuestions.vue`
- Delete: `frontend/src/views-student/FillBlankQuestion.vue`
- Delete: `frontend/src/views-student/DrawingQuestion.vue`
- Delete: `frontend/src/views-student/SelfCheck.vue`

- [ ] **Step 1: Delete old student view components**

```bash
rm frontend/src/views-student/DataPreview.vue
rm frontend/src/views-student/ChoiceQuestions.vue
rm frontend/src/views-student/FillBlankQuestion.vue
rm frontend/src/views-student/DrawingQuestion.vue
rm frontend/src/views-student/SelfCheck.vue
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views-student/
git commit -m "chore: remove old student view components"
```

---

### Task 18: End-to-end verification

- [ ] **Step 1: Start backend and verify API**

```bash
cd backend && python3 app.py &
sleep 2
# Test login
curl -s -X POST http://localhost:5001/api/student/login -H 'Content-Type: application/json' -d '{"name":"test_student"}'
# Test level submit
curl -s -X POST http://localhost:5001/api/level/submit -H 'Content-Type: application/json' -d '{"student_id":1,"level_no":1,"answer":"A","stars":3,"attempts":1}'
# Test chart (requires teacher login first, skip if session management is complex)
```

- [ ] **Step 2: Build frontend and verify no compile errors**

```bash
cd frontend && npm run build
```
Expected: Build succeeds with no errors. Output in `backend/static/`.

- [ ] **Step 3: Test full student flow in browser**

- Open `http://localhost:5001`
- Login as a new student
- Navigate through all 5 levels
- Verify each level's game mechanics work
- Verify /submit-success shows star summary

- [ ] **Step 4: Test teacher flow in browser**

- Open `http://localhost:5001/teacher`
- Login as admin/password
- Verify dashboard shows student data with 5 questions
- Verify chart generation buttons work
- Verify student detail page

- [ ] **Step 5: Commit any final fixes**

```bash
git add -A
git commit -m "chore: final adjustments after E2E testing"
```
