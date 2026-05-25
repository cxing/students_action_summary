# 折线统计图学习单 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Vue 3 + Flask + SQLite web app where students complete a line-chart learning sheet (7 multiple-choice + 1 drawing + self-check) and teachers view class-wide results.

**Architecture:** Flask serves REST API endpoints backed by SQLite. Vue 3 SPA consumes the API via Axios. Two route groups (student, teacher) share one Vue app. Vite dev server proxies `/api` to Flask. Production: Flask serves the built static files.

**Tech Stack:** Python 3, Flask, SQLite, Vue 3 (Composition API), Vue Router, Pinia, Axios, Vite, HTML5 Canvas

---

## File Structure

```
students_action_summary/
├── backend/
│   ├── app.py              # Flask entry: create_app, register blueprints, CORS
│   ├── models.py           # SQLite schema init + helper functions
│   ├── auth.py             # Login blueprints (student + teacher)
│   ├── submit.py           # Submit blueprint (answers + drawing + self_check)
│   ├── teacher.py          # Teacher dashboard blueprints
│   └── requirements.txt    # Flask, flask-cors
├── frontend/
│   ├── index.html
│   ├── vite.config.js
│   ├── package.json
│   └── src/
│       ├── main.js
│       ├── App.vue
│       ├── style.css                # Global styles
│       ├── api.js                   # Axios instance + API functions
│       ├── router/
│       │   └── index.js             # Student + teacher routes
│       ├── stores/
│       │   ├── student.js           # Pinia: student_id, name, answers, drawing, selfCheck
│       │   └── teacher.js           # Pinia: teacher auth state
│       ├── views-student/
│       │   ├── StudentLogin.vue
│       │   ├── DataPreview.vue
│       │   ├── ChoiceQuestions.vue
│       │   ├── DrawingQuestion.vue
│       │   ├── SelfCheck.vue
│       │   └── SubmitSuccess.vue
│       └── views-teacher/
│           ├── TeacherLogin.vue
│           ├── Dashboard.vue
│           └── StudentDetail.vue
└── data/                            # gitignored, created at runtime
```

---

### Task 1: Backend — Project Scaffolding & Requirements

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/app.py`

- [ ] **Step 1: Create requirements.txt**

```text
flask==3.1.1
flask-cors==5.0.1
```

- [ ] **Step 2: Install dependencies**

Run: `cd backend && pip install -r requirements.txt`

- [ ] **Step 3: Create Flask app skeleton**

```python
# backend/app.py
from flask import Flask
from flask_cors import CORS


def create_app():
    app = Flask(__name__)
    app.secret_key = 'change-me-in-production'
    CORS(app, supports_credentials=True, origins=['http://localhost:5173'])

    @app.route('/api/health')
    def health():
        return {'ok': True}

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
```

- [ ] **Step 4: Verify Flask starts**

Run: `cd backend && python app.py`
Expected: Flask running on port 5000, `/api/health` returns `{"ok":true}`.
Then stop the server (Ctrl+C).

- [ ] **Step 5: Commit**

```bash
git add backend/requirements.txt backend/app.py
git commit -m "feat: scaffold Flask backend with CORS"
```

---

### Task 2: Backend — Database Models & Init

**Files:**
- Create: `backend/models.py`

- [ ] **Step 1: Write models.py with schema and helpers**

```python
# backend/models.py
import sqlite3
import os
from datetime import datetime, timezone

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
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
            question_no INTEGER NOT NULL CHECK(question_no BETWEEN 1 AND 7),
            answer TEXT NOT NULL,
            is_correct INTEGER NOT NULL DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(id),
            UNIQUE(student_id, question_no)
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
    conn.close()


# Reference answers for grading
REFERENCE_ANSWERS = {1: 'A', 2: 'B', 3: 'A', 4: 'B', 5: 'A', 6: 'A', 7: 'A'}

# Standard drawing coordinates: (day_index 0-5) -> expected data value
DRAWING_STANDARD = {0: 30, 1: 32, 2: 35, 3: 36, 4: 39, 5: 42}
DRAWING_TOLERANCE = 2

# X-axis labels for drawing
DAY_LABELS = ['周一', '周二', '周三', '周四', '周五', '周六']


def grade_drawing(points):
    """points: list of [x_canvas, y_canvas] — 6 points.
    x_canvas is used to determine day index (nearest vertical grid line).
    y_canvas is converted to data value and checked against standard ±tolerance.
    Returns auto_score dict.
    """
    if len(points) != 6:
        return {'points_correct': False, 'labels_complete': False, 'in_order': False, 'trend': '无法判断'}

    # Check if points are roughly in order by x-coordinate (left to right)
    xs = [p[0] for p in points]
    in_order = all(xs[i] < xs[i+1] for i in range(len(xs)-1))

    # Since the frontend maps canvas clicks to data values before sending,
    # we receive points as [[day_index, value], ...] or canvas coords.
    # For grading, we expect the frontend to send data values: [[0, 30], [1, 32], ...]
    # where day_index is 0-5 and value is the y-axis value.
    points_correct = True
    for i, pt in enumerate(points):
        expected = DRAWING_STANDARD.get(i)
        if expected is None:
            points_correct = False
            break
        value = pt[1] if isinstance(pt, (list, tuple)) and len(pt) >= 2 else pt
        if abs(value - expected) > DRAWING_TOLERANCE:
            points_correct = False
            break

    labels_complete = True  # frontend always includes labels
    trend = '上升' if in_order and points_correct else '无法判断'

    return {
        'points_correct': points_correct,
        'labels_complete': labels_complete,
        'in_order': in_order,
        'trend': trend,
    }
```

- [ ] **Step 2: Verify DB initialization**

Run:
```bash
cd backend && python -c "
from models import init_db, get_db
init_db()
conn = get_db()
tables = conn.execute(\"SELECT name FROM sqlite_master WHERE type='table'\").fetchall()
print([t['name'] for t in tables])
conn.close()
"
```
Expected: `['students', 'answers', 'drawings', 'self_check']`

- [ ] **Step 3: Commit**

```bash
git add backend/models.py
git commit -m "feat: add SQLite models with schema init and grading logic"
```

---

### Task 3: Backend — Auth Endpoints (Student & Teacher Login)

**Files:**
- Create: `backend/auth.py`
- Modify: `backend/app.py`

- [ ] **Step 1: Write auth blueprint**

```python
# backend/auth.py
from flask import Blueprint, request, jsonify, session
from models import get_db

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/api/student/login', methods=['POST'])
def student_login():
    data = request.get_json()
    name = data.get('name', '').strip()
    if not name:
        return jsonify({'error': '姓名不能为空'}), 400

    conn = get_db()
    row = conn.execute('SELECT id, name FROM students WHERE name = ?', (name,)).fetchone()
    if row:
        student_id, student_name = row['id'], row['name']
    else:
        cur = conn.execute('INSERT INTO students (name) VALUES (?)', (name,))
        conn.commit()
        student_id = cur.lastrowid
        student_name = name
    conn.close()

    return jsonify({'student_id': student_id, 'name': student_name})


@auth_bp.route('/api/teacher/login', methods=['POST'])
def teacher_login():
    data = request.get_json()
    username = data.get('username', '')
    password = data.get('password', '')
    if username == 'admin' and password == 'password':
        session['teacher'] = True
        return jsonify({'ok': True})
    return jsonify({'error': '用户名或密码错误'}), 401


@auth_bp.route('/api/teacher/logout', methods=['POST'])
def teacher_logout():
    session.pop('teacher', None)
    return jsonify({'ok': True})


@auth_bp.route('/api/teacher/check', methods=['GET'])
def teacher_check():
    if session.get('teacher'):
        return jsonify({'ok': True})
    return jsonify({'ok': False}), 401
```

- [ ] **Step 2: Register blueprint in app.py**

```python
# backend/app.py — replace the create_app() function:
def create_app():
    app = Flask(__name__)
    app.secret_key = 'change-me-in-production'
    CORS(app, supports_credentials=True, origins=['http://localhost:5173'])

    from auth import auth_bp
    app.register_blueprint(auth_bp)

    @app.route('/api/health')
    def health():
        return {'ok': True}

    return app
```

- [ ] **Step 3: Verify login endpoints**

Run:
```bash
cd backend && python -c "
from app import create_app
app = create_app()
with app.test_client() as c:
    # Student login (new)
    r = c.post('/api/student/login', json={'name': '测试'})
    print('New student:', r.get_json())
    # Student login (existing)
    r = c.post('/api/student/login', json={'name': '测试'})
    print('Existing student:', r.get_json())
    # Teacher login success
    r = c.post('/api/teacher/login', json={'username': 'admin', 'password': 'password'})
    print('Teacher OK:', r.get_json())
    # Teacher login fail
    r = c.post('/api/teacher/login', json={'username': 'admin', 'password': 'wrong'})
    print('Teacher fail:', r.status_code, r.get_json())
"
```
Expected output shows student_id returned, teacher login ok/fail.

- [ ] **Step 4: Commit**

```bash
git add backend/auth.py backend/app.py
git commit -m "feat: add student and teacher login endpoints"
```

---

### Task 4: Backend — Submit Endpoint

**Files:**
- Create: `backend/submit.py`
- Modify: `backend/app.py`

- [ ] **Step 1: Write submit blueprint**

```python
# backend/submit.py
import json
from flask import Blueprint, request, jsonify
from models import get_db, REFERENCE_ANSWERS, grade_drawing

submit_bp = Blueprint('submit', __name__)


@submit_bp.route('/api/submit', methods=['POST'])
def submit():
    data = request.get_json()
    student_id = data.get('student_id')
    if not student_id:
        return jsonify({'error': '缺少 student_id'}), 400

    conn = get_db()

    # Verify student exists
    student = conn.execute('SELECT id FROM students WHERE id = ?', (student_id,)).fetchone()
    if not student:
        conn.close()
        return jsonify({'error': '学生不存在'}), 404

    # 1. Save answers
    answers = data.get('answers', [])
    scores = {}
    for item in answers:
        qno = item['question_no']
        ans = item['answer']
        expected = REFERENCE_ANSWERS.get(qno)
        is_correct = 1 if (expected and ans == expected) else 0
        scores[str(qno)] = bool(is_correct)
        conn.execute("""
            INSERT INTO answers (student_id, question_no, answer, is_correct, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(student_id, question_no)
            DO UPDATE SET answer = excluded.answer, is_correct = excluded.is_correct, updated_at = CURRENT_TIMESTAMP
        """, (student_id, qno, ans, is_correct))

    # 2. Save drawing
    drawing_points = data.get('drawing_points', [])
    drawing_score = {}
    if drawing_points:
        drawing_score = grade_drawing(drawing_points)
        conn.execute("""
            INSERT INTO drawings (student_id, points, auto_score, created_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(student_id)
            DO UPDATE SET points = excluded.points, auto_score = excluded.auto_score, created_at = CURRENT_TIMESTAMP
        """, (student_id, json.dumps(drawing_points), json.dumps(drawing_score)))

    # 3. Save self_check
    self_check = data.get('self_check', {})
    if self_check:
        conn.execute("""
            INSERT INTO self_check (student_id, point_check, line_check, draw_check, note, created_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(student_id)
            DO UPDATE SET point_check = excluded.point_check, line_check = excluded.line_check,
                          draw_check = excluded.draw_check, note = excluded.note, created_at = CURRENT_TIMESTAMP
        """, (
            student_id,
            self_check.get('point_check', ''),
            self_check.get('line_check', ''),
            self_check.get('draw_check', ''),
            self_check.get('note', ''),
        ))

    conn.commit()
    conn.close()

    return jsonify({
        'ok': True,
        'scores': scores,
        'drawing_score': drawing_score,
    })
```

- [ ] **Step 2: Register blueprint in app.py**

In `backend/app.py`, add after the auth blueprint registration:
```python
    from submit import submit_bp
    app.register_blueprint(submit_bp)
```

- [ ] **Step 3: Verify submit endpoint**

Run:
```bash
cd backend && python -c "
from app import create_app
app = create_app()
with app.test_client() as c:
    # Create student
    r = c.post('/api/student/login', json={'name': '测试'})
    sid = r.get_json()['student_id']
    # Submit
    r = c.post('/api/submit', json={
        'student_id': sid,
        'answers': [{'question_no': 1, 'answer': 'A'}, {'question_no': 2, 'answer': 'A'}],
        'drawing_points': [[0, 30], [1, 32], [2, 35], [3, 36], [4, 39], [5, 42]],
        'self_check': {'point_check': '能', 'line_check': '能', 'draw_check': '能', 'note': ''}
    })
    print(r.get_json())
"
```
Expected: `{'ok': True, 'scores': {'1': True, '2': False}, 'drawing_score': {...}}` (Q2 answer is 'B', not 'A').

- [ ] **Step 4: Commit**

```bash
git add backend/submit.py backend/app.py
git commit -m "feat: add submit endpoint with answers, drawing, and self_check"
```

---

### Task 5: Backend — Teacher Dashboard & Student Detail

**Files:**
- Create: `backend/teacher.py`
- Modify: `backend/app.py`

- [ ] **Step 1: Write teacher blueprint**

```python
# backend/teacher.py
import json
from functools import wraps
from flask import Blueprint, jsonify, session

teacher_bp = Blueprint('teacher', __name__)


def require_teacher(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('teacher'):
            return jsonify({'error': '请先登录'}), 401
        return f(*args, **kwargs)
    return decorated


@teacher_bp.route('/api/teacher/dashboard', methods=['GET'])
@require_teacher
def dashboard():
    from models import get_db, REFERENCE_ANSWERS
    conn = get_db()

    students = conn.execute('SELECT id, name FROM students ORDER BY id').fetchall()
    result = []
    for s in students:
        ans_rows = conn.execute(
            'SELECT question_no, answer, is_correct FROM answers WHERE student_id = ?', (s['id'],)
        ).fetchall()
        answers = {}
        scores = {}
        for row in ans_rows:
            answers[str(row['question_no'])] = row['answer']
            scores[str(row['question_no'])] = bool(row['is_correct'])

        drawing = conn.execute('SELECT id FROM drawings WHERE student_id = ?', (s['id'],)).fetchone()

        result.append({
            'id': s['id'],
            'name': s['name'],
            'answers': answers,
            'scores': scores,
            'drawing_submitted': drawing is not None,
        })

    total = len(result)
    submitted = sum(1 for r in result if len(r['answers']) > 0)
    conn.close()

    return jsonify({
        'students': result,
        'stats': {'submitted': submitted, 'total': total},
    })


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
        'SELECT question_no, answer, is_correct FROM answers WHERE student_id = ? ORDER BY question_no',
        (student_id,)
    ).fetchall()
    answers = [{'question_no': r['question_no'], 'answer': r['answer'], 'is_correct': bool(r['is_correct'])} for r in ans_rows]

    drawing = conn.execute('SELECT points, auto_score FROM drawings WHERE student_id = ?', (student_id,)).fetchone()
    drawing_data = None
    if drawing:
        drawing_data = {
            'points': json.loads(drawing['points']),
            'auto_score': json.loads(drawing['auto_score']),
        }

    sc = conn.execute('SELECT point_check, line_check, draw_check, note FROM self_check WHERE student_id = ?', (student_id,)).fetchone()
    self_check_data = None
    if sc:
        self_check_data = {
            'point_check': sc['point_check'],
            'line_check': sc['line_check'],
            'draw_check': sc['draw_check'],
            'note': sc['note'],
        }

    conn.close()
    return jsonify({
        'id': student['id'],
        'name': student['name'],
        'answers': answers,
        'drawing': drawing_data,
        'self_check': self_check_data,
    })
```

- [ ] **Step 2: Register blueprint in app.py**

In `backend/app.py`, add after the submit blueprint registration:
```python
    from teacher import teacher_bp
    app.register_blueprint(teacher_bp)
```

- [ ] **Step 3: Verify teacher endpoints**

Run:
```bash
cd backend && python -c "
from app import create_app
app = create_app()
with app.test_client() as c:
    # Login as teacher (session cookie is automatic)
    c.post('/api/teacher/login', json={'username': 'admin', 'password': 'password'})
    # Dashboard
    r = c.get('/api/teacher/dashboard')
    print('Dashboard:', r.get_json())
    # Student detail (student_id=1 from previous test)
    r = c.get('/api/teacher/student/1')
    print('Detail:', r.get_json())
"
```
Expected: Dashboard shows student list with stats; detail shows answers, drawing, self_check.

- [ ] **Step 4: Commit**

```bash
git add backend/teacher.py backend/app.py
git commit -m "feat: add teacher dashboard and student detail endpoints"
```

The final `backend/app.py` after all registrations should look like:

```python
# backend/app.py
from flask import Flask
from flask_cors import CORS


def create_app():
    app = Flask(__name__)
    app.secret_key = 'change-me-in-production'
    CORS(app, supports_credentials=True, origins=['http://localhost:5173'])

    from auth import auth_bp
    app.register_blueprint(auth_bp)

    from submit import submit_bp
    app.register_blueprint(submit_bp)

    from teacher import teacher_bp
    app.register_blueprint(teacher_bp)

    @app.route('/api/health')
    def health():
        return {'ok': True}

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
```

---

### Task 6: Frontend — Project Scaffolding (Vue 3 + Vite)

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.js`
- Create: `frontend/index.html`

- [ ] **Step 1: Create package.json**

```json
{
  "name": "students-action-summary",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "vue": "^3.5.13",
    "vue-router": "^4.5.0",
    "pinia": "^3.0.2",
    "axios": "^1.7.9"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.2.3",
    "vite": "^6.3.1"
  }
}
```

- [ ] **Step 2: Create vite.config.js**

```javascript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: '../backend/static',
    emptyOutDir: true,
  },
})
```

- [ ] **Step 3: Create index.html**

```html
<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>折线统计图 — 学习单</title>
  </head>
  <body>
    <div id="app"></div>
    <script type="module" src="/src/main.js"></script>
  </body>
</html>
```

- [ ] **Step 4: Install dependencies**

Run: `cd frontend && npm install`

- [ ] **Step 5: Commit**

```bash
git add frontend/package.json frontend/vite.config.js frontend/index.html frontend/package-lock.json
git commit -m "feat: scaffold Vue 3 + Vite frontend project"
```

---

### Task 7: Frontend — Vue Entry, Router, Stores, API Client

**Files:**
- Create: `frontend/src/main.js`
- Create: `frontend/src/App.vue`
- Create: `frontend/src/router/index.js`
- Create: `frontend/src/stores/student.js`
- Create: `frontend/src/stores/teacher.js`
- Create: `frontend/src/api.js`

- [ ] **Step 1: Create main.js**

```javascript
// frontend/src/main.js
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './style.css'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')
```

- [ ] **Step 2: Create App.vue**

```html
<!-- frontend/src/App.vue -->
<template>
  <router-view />
</template>
```

- [ ] **Step 3: Create router/index.js**

```javascript
// frontend/src/router/index.js
import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  // Student routes
  {
    path: '/',
    name: 'StudentLogin',
    component: () => import('../views-student/StudentLogin.vue'),
  },
  {
    path: '/preview',
    name: 'DataPreview',
    component: () => import('../views-student/DataPreview.vue'),
  },
  {
    path: '/questions',
    name: 'ChoiceQuestions',
    component: () => import('../views-student/ChoiceQuestions.vue'),
  },
  {
    path: '/drawing',
    name: 'DrawingQuestion',
    component: () => import('../views-student/DrawingQuestion.vue'),
  },
  {
    path: '/self-check',
    name: 'SelfCheck',
    component: () => import('../views-student/SelfCheck.vue'),
  },
  {
    path: '/submit-success',
    name: 'SubmitSuccess',
    component: () => import('../views-student/SubmitSuccess.vue'),
  },
  // Teacher routes
  {
    path: '/teacher',
    name: 'TeacherLogin',
    component: () => import('../views-teacher/TeacherLogin.vue'),
  },
  {
    path: '/teacher/dashboard',
    name: 'Dashboard',
    component: () => import('../views-teacher/Dashboard.vue'),
  },
  {
    path: '/teacher/student/:id',
    name: 'StudentDetail',
    component: () => import('../views-teacher/StudentDetail.vue'),
    props: true,
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
```

- [ ] **Step 4: Create student Pinia store**

```javascript
// frontend/src/stores/student.js
import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'

export const useStudentStore = defineStore('student', () => {
  const studentId = ref(null)
  const name = ref('')
  const answers = reactive({})       // { 1: 'A', 2: 'B', ... }
  const drawingPoints = ref([])       // [[x1,y1], ...] or [[day, value], ...]
  const selfCheck = reactive({
    pointCheck: '',
    lineCheck: '',
    drawCheck: '',
    note: '',
  })

  function setStudent(id, studentName) {
    studentId.value = id
    name.value = studentName
  }

  function setAnswer(questionNo, answer) {
    answers[questionNo] = answer
  }

  function setDrawing(points) {
    drawingPoints.value = points
  }

  function setSelfCheck(check) {
    selfCheck.pointCheck = check.pointCheck || ''
    selfCheck.lineCheck = check.lineCheck || ''
    selfCheck.drawCheck = check.drawCheck || ''
    selfCheck.note = check.note || ''
  }

  function reset() {
    studentId.value = null
    name.value = ''
    Object.keys(answers).forEach(k => delete answers[k])
    drawingPoints.value = []
    selfCheck.pointCheck = ''
    selfCheck.lineCheck = ''
    selfCheck.drawCheck = ''
    selfCheck.note = ''
  }

  return { studentId, name, answers, drawingPoints, selfCheck, setStudent, setAnswer, setDrawing, setSelfCheck, reset }
})
```

- [ ] **Step 5: Create teacher Pinia store**

```javascript
// frontend/src/stores/teacher.js
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useTeacherStore = defineStore('teacher', () => {
  const loggedIn = ref(false)

  function setLoggedIn(val) {
    loggedIn.value = val
  }

  return { loggedIn, setLoggedIn }
})
```

- [ ] **Step 6: Create api.js (Axios client)**

```javascript
// frontend/src/api.js
import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  withCredentials: true,
})

// Student API
export function studentLogin(name) {
  return api.post('/student/login', { name })
}

// Teacher API
export function teacherLogin(username, password) {
  return api.post('/teacher/login', { username, password })
}

export function teacherCheck() {
  return api.get('/teacher/check')
}

// Submit API
export function submitAll(studentId, answers, drawingPoints, selfCheck) {
  return api.post('/submit', {
    student_id: studentId,
    answers: Object.entries(answers).map(([qno, ans]) => ({ question_no: parseInt(qno), answer: ans })),
    drawing_points: drawingPoints,
    self_check: {
      point_check: selfCheck.pointCheck || '',
      line_check: selfCheck.lineCheck || '',
      draw_check: selfCheck.drawCheck || '',
      note: selfCheck.note || '',
    },
  })
}

// Teacher data API
export function getDashboard() {
  return api.get('/teacher/dashboard')
}

export function getStudentDetail(studentId) {
  return api.get(`/teacher/student/${studentId}`)
}
```

- [ ] **Step 7: Verify frontend starts**

Run: `cd frontend && npm run dev`
Expected: Vite dev server starts on port 5173, page loads with empty <router-view>.

- [ ] **Step 8: Commit**

```bash
git add frontend/src/main.js frontend/src/App.vue frontend/src/router/ frontend/src/stores/ frontend/src/api.js
git commit -m "feat: add Vue entry, router, Pinia stores, and API client"
```

---

### Task 8: Frontend — StudentLogin & DataPreview Views

**Files:**
- Create: `frontend/src/views-student/StudentLogin.vue`
- Create: `frontend/src/views-student/DataPreview.vue`

- [ ] **Step 1: Create StudentLogin.vue**

```html
<!-- frontend/src/views-student/StudentLogin.vue -->
<template>
  <div class="login-container">
    <div class="login-card">
      <h1>折线统计图 学习单</h1>
      <p class="subtitle">请输入你的姓名开始答题</p>
      <form @submit.prevent="handleLogin">
        <input
          v-model="name"
          type="text"
          placeholder="请输入你的姓名"
          class="name-input"
          autocomplete="off"
        />
        <button type="submit" class="btn-primary" :disabled="!name.trim() || loading">
          {{ loading ? '登录中...' : '开始答题' }}
        </button>
      </form>
      <p v-if="error" class="error">{{ error }}</p>
      <div class="teacher-link">
        <router-link to="/teacher">教师登录</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useStudentStore } from '../stores/student.js'
import { studentLogin } from '../api.js'

const router = useRouter()
const store = useStudentStore()
const name = ref('')
const loading = ref(false)
const error = ref('')

async function handleLogin() {
  if (!name.value.trim()) return
  loading.value = true
  error.value = ''
  try {
    const res = await studentLogin(name.value.trim())
    store.setStudent(res.data.student_id, res.data.name)
    router.push('/preview')
  } catch (e) {
    error.value = '登录失败，请重试'
  } finally {
    loading.value = false
  }
}
</script>
```

- [ ] **Step 2: Create DataPreview.vue**

```html
<!-- frontend/src/views-student/DataPreview.vue -->
<template>
  <div class="page-container">
    <div class="page-header">
      <span class="student-badge">{{ store.name }} 同学</span>
    </div>

    <div class="content-card">
      <h2>请先阅读下面两组统计数据</h2>

      <div class="table-section">
        <h3>统计表一：6名同学一分钟仰卧起坐个数统计表</h3>
        <table class="data-table">
          <thead>
            <tr>
              <th>姓名</th>
              <th>周子昂</th>
              <th>许明哲</th>
              <th>沈嘉诚</th>
              <th>叶思涵</th>
              <th>李欣怡</th>
              <th>吴俊杰</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>个数/个</td>
              <td>35</td>
              <td>42</td>
              <td>38</td>
              <td>40</td>
              <td>36</td>
              <td>33</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="table-section">
        <h3>统计表二：许明哲连续6天一分钟仰卧起坐成绩统计表</h3>
        <table class="data-table">
          <thead>
            <tr>
              <th>日期</th>
              <th>周一</th>
              <th>周二</th>
              <th>周三</th>
              <th>周四</th>
              <th>周五</th>
              <th>周六</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>个数/个</td>
              <td>30</td>
              <td>32</td>
              <td>35</td>
              <td>36</td>
              <td>39</td>
              <td>42</td>
            </tr>
          </tbody>
        </table>
      </div>

      <p class="hint">阅读完成后，点击下方按钮开始答题。</p>
      <button @click="$router.push('/questions')" class="btn-primary">开始答题</button>
    </div>
  </div>
</template>

<script setup>
import { useStudentStore } from '../stores/student.js'
const store = useStudentStore()
</script>
```

- [ ] **Step 3: Verify pages render**

Run `cd frontend && npm run dev`, open browser at `http://localhost:5173`. Verify:
- Login page shows (before redirect needed)
- Login with a name → DataPreview page shows
- Both tables display correctly

- [ ] **Step 4: Commit**

```bash
git add frontend/src/views-student/StudentLogin.vue frontend/src/views-student/DataPreview.vue
git commit -m "feat: add student login and data preview views"
```

---

### Task 9: Frontend — ChoiceQuestions View

**Files:**
- Create: `frontend/src/views-student/ChoiceQuestions.vue`

- [ ] **Step 1: Create ChoiceQuestions.vue**

The 7 questions data (from requirements.docx) with options:

```html
<!-- frontend/src/views-student/ChoiceQuestions.vue -->
<template>
  <div class="page-container">
    <div class="page-header">
      <span class="student-badge">{{ store.name }} 同学</span>
      <span class="progress">{{ current + 1 }} / {{ questions.length }}</span>
    </div>

    <div class="content-card">
      <div class="question-header">
        <span class="question-number">第{{ current + 1 }}题</span>
        <span class="question-type">选择题</span>
      </div>

      <p class="question-text">{{ questions[current].text }}</p>

      <div class="options-list">
        <label
          v-for="(opt, key) in questions[current].options"
          :key="key"
          class="option-item"
          :class="{ selected: store.answers[current + 1] === key }"
        >
          <input
            type="radio"
            :name="'q' + current"
            :value="key"
            :checked="store.answers[current + 1] === key"
            @change="selectAnswer(key)"
          />
          <span class="option-label">{{ key }}. {{ opt }}</span>
        </label>
      </div>

      <div class="nav-buttons">
        <button v-if="current > 0" @click="prev" class="btn-secondary">上一题</button>
        <span v-else></span>
        <button v-if="current < questions.length - 1" @click="next" class="btn-primary">下一题</button>
        <button v-else @click="goToDrawing" class="btn-primary">进入绘图题</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useStudentStore } from '../stores/student.js'

const router = useRouter()
const store = useStudentStore()
const current = ref(0)

const questions = [
  {
    text: '折线统计图中的"点"表示什么？',
    options: { A: '数量的多少', B: '图形的颜色', C: '统计图的标题' },
  },
  {
    text: '折线统计图中的"线"表示什么？',
    options: { A: '数量的单位', B: '数量的变化趋势', C: '横轴的长度' },
  },
  {
    text: '根据统计表一，要比较6名同学一分钟仰卧起坐个数的多少，最适合用什么统计图？',
    options: { A: '条形统计图', B: '折线统计图', C: '不需要统计图' },
  },
  {
    text: '根据统计表二，要表示许明哲连续6天一分钟仰卧起坐成绩的变化，最适合用什么统计图？',
    options: { A: '条形统计图', B: '折线统计图', C: '饼图' },
  },
  {
    text: '在折线统计图中，如果折线整体向上，通常表示什么？',
    options: { A: '数量在增加', B: '数量在减少', C: '数量没有变化' },
  },
  {
    text: '根据统计表二，许明哲连续6天一分钟仰卧起坐成绩的变化情况是：',
    options: { A: '成绩整体上升', B: '成绩整体下降', C: '成绩没有变化' },
  },
  {
    text: '能否预测许明哲周日的仰卧起坐成绩：',
    options: { A: '45', B: '50', C: '20' },
  },
]

function selectAnswer(key) {
  store.setAnswer(current.value + 1, key)
}

function next() {
  if (current.value < questions.length - 1) current.value++
}

function prev() {
  if (current.value > 0) current.value--
}

function goToDrawing() {
  router.push('/drawing')
}
</script>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views-student/ChoiceQuestions.vue
git commit -m "feat: add multiple-choice questions view (Q1-Q7)"
```

---

### Task 10: Frontend — DrawingQuestion View

**Files:**
- Create: `frontend/src/views-student/DrawingQuestion.vue`

This is the most complex component. Canvas grid with click-to-plot, snap-to-grid, sequential input, auto-label and auto-connect.

- [ ] **Step 1: Create DrawingQuestion.vue**

```html
<!-- frontend/src/views-student/DrawingQuestion.vue -->
<template>
  <div class="page-container">
    <div class="page-header">
      <span class="student-badge">{{ store.name }} 同学</span>
    </div>

    <div class="content-card">
      <h2>题目7（绘图题）</h2>
      <p class="subtitle">根据统计表二，在下方方格图中绘制"许明哲连续6天一分钟仰卧起坐成绩折线统计图"。</p>

      <div class="drawing-requirements">
        <span>要求：</span>①准确描点 ②在点旁标出数据 ③按时间顺序连线 ④观察趋势
      </div>

      <div class="canvas-wrapper">
        <div class="y-axis-label">个数/个</div>
        <canvas
          ref="canvasRef"
          :width="canvasWidth"
          :height="canvasHeight"
          @click="handleCanvasClick"
          class="drawing-canvas"
        ></canvas>
        <div class="x-axis-labels">
          <span v-for="day in dayLabels" :key="day" :class="{ active: plottedValue(dayLabels.indexOf(day)) !== null }">{{ day }}</span>
        </div>
      </div>

      <div class="drawing-info">
        <span class="plot-count">已描点：{{ plottedCount }} / 6</span>
        <span v-if="plottedCount === 6" class="trend-badge">趋势：{{ trendText }}</span>
      </div>

      <div class="nav-buttons">
        <button @click="resetDrawing" class="btn-secondary">重新描点</button>
        <button
          @click="goToSelfCheck"
          class="btn-primary"
          :disabled="plottedCount < 6"
        >
          {{ plottedCount < 6 ? `还有 ${6 - plottedCount} 个点未描` : '完成绘图，继续' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useStudentStore } from '../stores/student.js'

const router = useRouter()
const store = useStudentStore()

const dayLabels = ['周一', '周二', '周三', '周四', '周五', '周六']
const expectedValues = [30, 32, 35, 36, 39, 42]

// Canvas dimensions
const canvasWidth = 640
const canvasHeight = 420
const canvasRef = ref(null)

// Plot area padding
const padding = { top: 20, right: 30, bottom: 10, left: 10 }
const plotWidth = canvasWidth - padding.left - padding.right
const plotHeight = canvasHeight - padding.top - padding.bottom

// Plotted points as {x, y, value} where x,y are canvas coords
const plottedPoints = ref([])

const plottedCount = computed(() => plottedPoints.value.length)

const trendText = computed(() => {
  if (plottedPoints.value.length < 6) return ''
  const vals = plottedPoints.value.map(p => p.value)
  // Check if all consecutive pairs are increasing
  let increasing = true
  for (let i = 1; i < vals.length; i++) {
    if (vals[i] <= vals[i - 1]) { increasing = false; break }
  }
  return increasing ? '整体上升' : '需检查'
})

// Convert data value to canvas Y coordinate
function valueToY(val) {
  return padding.top + plotHeight - (val / 45) * plotHeight
}

// Convert day index to canvas X coordinate
function dayToX(dayIndex) {
  return padding.left + (dayIndex / 5) * plotWidth
}

// Convert canvas Y back to data value (for grading)
function yToValue(y) {
  return Math.round(((padding.top + plotHeight - y) / plotHeight) * 45)
}

function plottedValue(dayIndex) {
  const pt = plottedPoints.value[dayIndex]
  return pt ? pt.value : null
}

function drawGrid() {
  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  ctx.clearRect(0, 0, canvasWidth, canvasHeight)

  // Background
  ctx.fillStyle = '#fafbfc'
  ctx.fillRect(0, 0, canvasWidth, canvasHeight)

  // Plot area background
  ctx.fillStyle = '#fff'
  ctx.fillRect(padding.left, padding.top, plotWidth, plotHeight)

  // Y-axis grid lines and labels
  ctx.strokeStyle = '#e8e8e8'
  ctx.lineWidth = 1
  ctx.fillStyle = '#888'
  ctx.font = '12px sans-serif'
  ctx.textAlign = 'right'
  for (let val = 0; val <= 45; val += 5) {
    const y = valueToY(val)
    ctx.beginPath()
    ctx.moveTo(padding.left, y)
    ctx.lineTo(padding.left + plotWidth, y)
    ctx.stroke()
    ctx.fillText(val, padding.left - 6, y + 4)
  }

  // X-axis grid lines and labels
  ctx.textAlign = 'center'
  for (let i = 0; i < 6; i++) {
    const x = dayToX(i)
    ctx.strokeStyle = '#e8e8e8'
    ctx.beginPath()
    ctx.moveTo(x, padding.top)
    ctx.lineTo(x, padding.top + plotHeight)
    ctx.stroke()
  }

  // Axes
  ctx.strokeStyle = '#333'
  ctx.lineWidth = 1.5
  ctx.beginPath()
  ctx.moveTo(padding.left, padding.top)
  ctx.lineTo(padding.left, padding.top + plotHeight)
  ctx.lineTo(padding.left + plotWidth, padding.top + plotHeight)
  ctx.stroke()

  // Plot line connecting all points
  if (plottedPoints.value.length >= 2) {
    ctx.strokeStyle = '#e74c3c'
    ctx.lineWidth = 2.5
    ctx.lineJoin = 'round'
    ctx.beginPath()
    for (let i = 0; i < plottedPoints.value.length; i++) {
      const pt = plottedPoints.value[i]
      if (i === 0) ctx.moveTo(pt.x, pt.y)
      else ctx.lineTo(pt.x, pt.y)
    }
    ctx.stroke()
  }

  // Plot points and labels
  for (let i = 0; i < plottedPoints.value.length; i++) {
    const pt = plottedPoints.value[i]
    // Point
    ctx.fillStyle = '#e74c3c'
    ctx.beginPath()
    ctx.arc(pt.x, pt.y, 6, 0, Math.PI * 2)
    ctx.fill()
    ctx.strokeStyle = '#fff'
    ctx.lineWidth = 2
    ctx.stroke()
    // Value label
    ctx.fillStyle = '#333'
    ctx.font = 'bold 14px sans-serif'
    ctx.textAlign = 'center'
    ctx.fillText(pt.value, pt.x, pt.y - 14)
  }
}

function handleCanvasClick(e) {
  if (plottedPoints.value.length >= 6) return

  const canvas = canvasRef.value
  const rect = canvas.getBoundingClientRect()
  const scaleX = canvasWidth / rect.width
  const scaleY = canvasHeight / rect.height
  const clickX = (e.clientX - rect.left) * scaleX
  const clickY = (e.clientY - rect.top) * scaleY

  // Determine which day this click is for
  const dayIndex = plottedPoints.value.length

  // Snap X to the day's vertical grid line
  const x = dayToX(dayIndex)
  // Clamp Y to plot area and round to nearest grid line
  const clampedY = Math.max(padding.top, Math.min(padding.top + plotHeight, clickY))
  const snappedValue = Math.round(yToValue(clampedY) / 5) * 5
  const snappedY = valueToY(Math.min(45, Math.max(0, snappedValue)))

  plottedPoints.value.push({ x, y: snappedY, value: snappedValue })

  // Store as [dayIndex, value] for submission
  const drawingData = plottedPoints.value.map((p, i) => [i, p.value])
  store.setDrawing(drawingData)

  drawGrid()
}

function resetDrawing() {
  plottedPoints.value = []
  store.setDrawing([])
  drawGrid()
}

function goToSelfCheck() {
  router.push('/self-check')
}

onMounted(() => {
  // Restore any previously plotted points from store (for back-navigation)
  if (store.drawingPoints && store.drawingPoints.length > 0) {
    for (const [dayIndex, value] of store.drawingPoints) {
      const x = dayToX(dayIndex)
      const y = valueToY(value)
      plottedPoints.value.push({ x, y, value })
    }
  }
  drawGrid()
})
</script>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views-student/DrawingQuestion.vue
git commit -m "feat: add drawing question view with Canvas grid and click-to-plot"
```

---

### Task 11: Frontend — SelfCheck & SubmitSuccess Views

**Files:**
- Create: `frontend/src/views-student/SelfCheck.vue`
- Create: `frontend/src/views-student/SubmitSuccess.vue`

- [ ] **Step 1: Create SelfCheck.vue**

```html
<!-- frontend/src/views-student/SelfCheck.vue -->
<template>
  <div class="page-container">
    <div class="page-header">
      <span class="student-badge">{{ store.name }} 同学</span>
    </div>

    <div class="content-card">
      <h2>自我检查</h2>
      <p class="subtitle">请根据你的学习情况如实完成自我评价</p>

      <div class="check-section">
        <div class="check-item">
          <p>我能说出"点表示数量多少"。</p>
          <label class="check-option">
            <input type="radio" value="能" v-model="pointCheck" /> 能
          </label>
          <label class="check-option">
            <input type="radio" value="还不确定" v-model="pointCheck" /> 还不确定
          </label>
        </div>

        <div class="check-item">
          <p>我能说出"线表示变化趋势"。</p>
          <label class="check-option">
            <input type="radio" value="能" v-model="lineCheck" /> 能
          </label>
          <label class="check-option">
            <input type="radio" value="还不确定" v-model="lineCheck" /> 还不确定
          </label>
        </div>

        <div class="check-item">
          <p>我能根据统计表绘制折线统计图。</p>
          <label class="check-option">
            <input type="radio" value="能" v-model="drawCheck" /> 能
          </label>
          <label class="check-option">
            <input type="radio" value="还不确定" v-model="drawCheck" /> 还不确定
          </label>
        </div>

        <div class="check-item">
          <p>我绘制折线统计图时还需要注意：</p>
          <textarea
            v-model="note"
            placeholder="请在此填写..."
            class="note-input"
          ></textarea>
        </div>
      </div>

      <div class="nav-buttons">
        <button @click="$router.push('/drawing')" class="btn-secondary">返回绘图</button>
        <button @click="submit" class="btn-primary" :disabled="submitting">
          {{ submitting ? '提交中...' : '提交' }}
        </button>
      </div>
      <p v-if="error" class="error">{{ error }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useStudentStore } from '../stores/student.js'
import { submitAll } from '../api.js'

const router = useRouter()
const store = useStudentStore()

const pointCheck = ref(store.selfCheck.pointCheck || '')
const lineCheck = ref(store.selfCheck.lineCheck || '')
const drawCheck = ref(store.selfCheck.drawCheck || '')
const note = ref(store.selfCheck.note || '')
const submitting = ref(false)
const error = ref('')

async function submit() {
  submitting.value = true
  error.value = ''
  try {
    await submitAll(
      store.studentId,
      store.answers,
      store.drawingPoints,
      { pointCheck: pointCheck.value, lineCheck: lineCheck.value, drawCheck: drawCheck.value, note: note.value }
    )
    router.push('/submit-success')
  } catch (e) {
    error.value = '提交失败，请重试'
  } finally {
    submitting.value = false
  }
}
</script>
```

- [ ] **Step 2: Create SubmitSuccess.vue**

```html
<!-- frontend/src/views-student/SubmitSuccess.vue -->
<template>
  <div class="login-container">
    <div class="login-card success-card">
      <div class="success-icon">&#10003;</div>
      <h1>提交成功！</h1>
      <p>{{ store.name }} 同学，你的学习单已经提交完成。</p>
      <button @click="switchUser" class="btn-primary">切换用户</button>
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

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views-student/SelfCheck.vue frontend/src/views-student/SubmitSuccess.vue
git commit -m "feat: add self-check and submit success views"
```

---

### Task 12: Frontend — Teacher Views (Login, Dashboard, StudentDetail)

**Files:**
- Create: `frontend/src/views-teacher/TeacherLogin.vue`
- Create: `frontend/src/views-teacher/Dashboard.vue`
- Create: `frontend/src/views-teacher/StudentDetail.vue`

- [ ] **Step 1: Create TeacherLogin.vue**

```html
<!-- frontend/src/views-teacher/TeacherLogin.vue -->
<template>
  <div class="login-container">
    <div class="login-card">
      <h1>教师登录</h1>
      <form @submit.prevent="handleLogin">
        <input v-model="username" type="text" placeholder="用户名" class="name-input" />
        <input v-model="password" type="password" placeholder="密码" class="name-input" />
        <button type="submit" class="btn-primary" :disabled="loading">
          {{ loading ? '登录中...' : '登录' }}
        </button>
      </form>
      <p v-if="error" class="error">{{ error }}</p>
      <router-link to="/">返回学生登录</router-link>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useTeacherStore } from '../stores/teacher.js'
import { teacherLogin } from '../api.js'

const router = useRouter()
const teacherStore = useTeacherStore()
const username = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

async function handleLogin() {
  loading.value = true
  error.value = ''
  try {
    await teacherLogin(username.value, password.value)
    teacherStore.setLoggedIn(true)
    router.push('/teacher/dashboard')
  } catch (e) {
    error.value = e.response?.data?.error || '登录失败'
  } finally {
    loading.value = false
  }
}
</script>
```

- [ ] **Step 2: Create Dashboard.vue**

```html
<!-- frontend/src/views-teacher/Dashboard.vue -->
<template>
  <div class="dashboard-container">
    <header class="dashboard-header">
      <h1>折线统计图 — 答题情况</h1>
      <div class="header-actions">
        <span class="teacher-label">教师端</span>
        <button @click="$router.push('/')" class="btn-small">退出</button>
      </div>
    </header>

    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else class="dashboard-content">
      <div class="stats-row">
        <div class="stat-card green">
          <span class="stat-number">{{ stats.submitted }} / {{ stats.total }}</span>
          <span class="stat-label">已提交</span>
        </div>
      </div>

      <div class="table-wrapper">
        <table class="dashboard-table">
          <thead>
            <tr>
              <th>姓名</th>
              <th v-for="q in 7" :key="q">Q{{ q }}</th>
              <th>绘图</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="s in students" :key="s.id">
              <td class="name-cell">{{ s.name }}</td>
              <td v-for="q in 7" :key="q" class="score-cell">
                <span v-if="s.scores[q] === true" class="correct">✓</span>
                <span v-else-if="s.scores[q] === false" class="wrong">✗</span>
                <span v-else class="empty">-</span>
              </td>
              <td class="status-cell">
                <span v-if="s.drawing_submitted" class="correct">✓</span>
                <span v-else class="wrong">✗</span>
              </td>
              <td>
                <router-link :to="'/teacher/student/' + s.id" class="view-link">查看</router-link>
              </td>
            </tr>
            <tr v-if="students.length === 0">
              <td colspan="10" class="empty-row">暂无学生数据</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getDashboard } from '../api.js'

const students = ref([])
const stats = ref({ submitted: 0, total: 0 })
const loading = ref(true)
const error = ref('')

onMounted(async () => {
  try {
    const res = await getDashboard()
    students.value = res.data.students
    stats.value = res.data.stats
  } catch (e) {
    error.value = '加载失败，请重新登录'
  } finally {
    loading.value = false
  }
})
</script>
```

- [ ] **Step 3: Create StudentDetail.vue**

```html
<!-- frontend/src/views-teacher/StudentDetail.vue -->
<template>
  <div class="dashboard-container">
    <header class="dashboard-header">
      <h1>{{ detail?.name }} · 答题详情</h1>
      <router-link to="/teacher/dashboard" class="btn-small">← 返回概览</router-link>
    </header>

    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="detail" class="detail-content">
      <!-- Answers table -->
      <div class="content-card">
        <h3>选择题答案</h3>
        <table class="data-table">
          <thead>
            <tr><th>题号</th><th>学生答案</th><th>正确答案</th><th>结果</th></tr>
          </thead>
          <tbody>
            <tr v-for="a in detail.answers" :key="a.question_no">
              <td>{{ a.question_no }}</td>
              <td>{{ a.answer || '-' }}</td>
              <td>{{ correctAnswers[a.question_no] }}</td>
              <td :class="a.is_correct ? 'correct' : 'wrong'">{{ a.is_correct ? '✓' : '✗' }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Drawing -->
      <div class="content-card" v-if="detail.drawing">
        <h3>绘图题</h3>
        <div class="drawing-review">
          <canvas ref="reviewCanvas" :width="400" :height="260" class="review-canvas"></canvas>
        </div>
        <div class="drawing-score">
          <span :class="detail.drawing.auto_score.points_correct ? 'correct' : 'wrong'">
            {{ detail.drawing.auto_score.points_correct ? '✓' : '✗' }} 描点正确
          </span>
          <span :class="detail.drawing.auto_score.in_order ? 'correct' : 'wrong'">
            {{ detail.drawing.auto_score.in_order ? '✓' : '✗' }} 按序连线
          </span>
          <span>趋势：{{ detail.drawing.auto_score.trend }}</span>
        </div>
      </div>

      <!-- Self Check -->
      <div class="content-card" v-if="detail.self_check">
        <h3>自我检查</h3>
        <p>"点表示数量多少" — {{ detail.self_check.point_check || '未填' }}</p>
        <p>"线表示变化趋势" — {{ detail.self_check.line_check || '未填' }}</p>
        <p>"能绘制折线统计图" — {{ detail.self_check.draw_check || '未填' }}</p>
        <p v-if="detail.self_check.note">还需注意：{{ detail.self_check.note }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getStudentDetail } from '../api.js'

const props = defineProps({ id: String })
const detail = ref(null)
const loading = ref(true)
const error = ref('')
const reviewCanvas = ref(null)
const correctAnswers = { 1: 'A', 2: 'B', 3: 'A', 4: 'B', 5: 'A', 6: 'A', 7: 'A' }

onMounted(async () => {
  try {
    const res = await getStudentDetail(props.id)
    detail.value = res.data

    // Draw student's drawing on review canvas
    if (detail.value.drawing) {
      setTimeout(() => drawReviewCanvas(), 50)
    }
  } catch (e) {
    error.value = '加载失败'
  } finally {
    loading.value = false
  }
})

function drawReviewCanvas() {
  const canvas = reviewCanvas.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  const w = 400, h = 260
  const pad = { top: 15, right: 20, bottom: 20, left: 30 }
  const pw = w - pad.left - pad.right
  const ph = h - pad.top - pad.bottom

  ctx.fillStyle = '#fff'
  ctx.fillRect(0, 0, w, h)

  // Grid
  ctx.strokeStyle = '#e8e8e8'
  ctx.lineWidth = 0.5
  for (let val = 0; val <= 45; val += 5) {
    const y = pad.top + ph - (val / 45) * ph
    ctx.beginPath(); ctx.moveTo(pad.left, y); ctx.lineTo(pad.left + pw, y); ctx.stroke()
  }
  for (let i = 0; i < 6; i++) {
    const x = pad.left + (i / 5) * pw
    ctx.beginPath(); ctx.moveTo(x, pad.top); ctx.lineTo(x, pad.top + ph); ctx.stroke()
  }

  const points = detail.value.drawing.points
  if (!points || points.length === 0) return

  // Draw line
  ctx.strokeStyle = '#e74c3c'
  ctx.lineWidth = 2
  ctx.beginPath()
  points.forEach((pt, i) => {
    const day = pt[0]
    const val = pt[1]
    const x = pad.left + (day / 5) * pw
    const y = pad.top + ph - (val / 45) * ph
    if (i === 0) ctx.moveTo(x, y)
    else ctx.lineTo(x, y)
  })
  ctx.stroke()

  // Draw points
  points.forEach(pt => {
    const day = pt[0]
    const val = pt[1]
    const x = pad.left + (day / 5) * pw
    const y = pad.top + ph - (val / 45) * ph
    ctx.fillStyle = '#e74c3c'
    ctx.beginPath(); ctx.arc(x, y, 4, 0, Math.PI * 2); ctx.fill()
    ctx.fillStyle = '#333'
    ctx.font = '10px sans-serif'
    ctx.textAlign = 'center'
    ctx.fillText(val, x, y - 8)
  })
}
</script>
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/views-teacher/
git commit -m "feat: add teacher views (login, dashboard, student detail)"
```

---

### Task 13: Global Styles & Visual Polish

**Files:**
- Create: `frontend/src/style.css`

- [ ] **Step 1: Create style.css**

```css
/* frontend/src/style.css */

:root {
  --primary: #4a90d9;
  --primary-dark: #3a7bc8;
  --success: #27ae60;
  --danger: #e74c3c;
  --bg: #f0f4f8;
  --card-bg: #ffffff;
  --text: #2c3e50;
  --text-secondary: #7f8c8d;
  --border: #e1e8ed;
  --radius: 12px;
  --shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
  background: var(--bg);
  color: var(--text);
  min-height: 100vh;
  line-height: 1.6;
}

/* ---- Login pages ---- */
.login-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 20px;
}

.login-card {
  background: var(--card-bg);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  padding: 40px;
  width: 100%;
  max-width: 400px;
  text-align: center;
}

.login-card h1 {
  font-size: 24px;
  margin-bottom: 8px;
  color: var(--primary-dark);
}

.subtitle {
  color: var(--text-secondary);
  font-size: 14px;
  margin-bottom: 24px;
}

.name-input {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid var(--border);
  border-radius: 8px;
  font-size: 16px;
  margin-bottom: 12px;
  outline: none;
  transition: border-color 0.2s;
}

.name-input:focus {
  border-color: var(--primary);
}

.btn-primary {
  width: 100%;
  padding: 12px;
  background: var(--primary);
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-primary:hover { background: var(--primary-dark); }
.btn-primary:disabled { background: #b0c4de; cursor: not-allowed; }

.btn-secondary {
  padding: 10px 20px;
  background: #fff;
  color: var(--primary);
  border: 2px solid var(--primary);
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-secondary:hover { background: #f0f6ff; }

.btn-small {
  padding: 6px 16px;
  background: var(--bg);
  color: var(--text-secondary);
  border: 1px solid var(--border);
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  text-decoration: none;
}

.error {
  color: var(--danger);
  font-size: 14px;
  margin-top: 12px;
}

.teacher-link {
  margin-top: 20px;
  font-size: 14px;
}

.teacher-link a {
  color: var(--text-secondary);
  text-decoration: none;
}

/* ---- Student pages ---- */
.page-container {
  max-width: 700px;
  margin: 0 auto;
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.student-badge {
  background: var(--primary);
  color: #fff;
  padding: 4px 16px;
  border-radius: 20px;
  font-size: 14px;
}

.progress {
  font-size: 14px;
  color: var(--text-secondary);
}

.content-card {
  background: var(--card-bg);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  padding: 32px;
}

.content-card h2 {
  font-size: 20px;
  margin-bottom: 8px;
  color: var(--primary-dark);
}

.content-card h3 {
  font-size: 16px;
  margin: 16px 0 8px;
  color: var(--text);
}

/* ---- Data tables ---- */
.table-section {
  margin: 20px 0;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
  margin-top: 8px;
}

.data-table th,
.data-table td {
  padding: 8px 10px;
  border: 1px solid var(--border);
  text-align: center;
}

.data-table th {
  background: #f5f7fa;
  font-weight: 600;
}

.hint {
  color: var(--text-secondary);
  font-size: 14px;
  margin: 16px 0;
}

/* ---- Questions ---- */
.question-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.question-number {
  font-weight: 600;
  color: var(--primary-dark);
  font-size: 16px;
}

.question-type {
  font-size: 12px;
  background: #f0f6ff;
  color: var(--primary);
  padding: 2px 10px;
  border-radius: 12px;
}

.question-text {
  font-size: 17px;
  margin-bottom: 20px;
  line-height: 1.6;
}

.options-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 24px;
}

.option-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 18px;
  border: 2px solid var(--border);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
}

.option-item:hover {
  border-color: var(--primary);
  background: #f8faff;
}

.option-item.selected {
  border-color: var(--primary);
  background: #eef4ff;
}

.option-item input[type="radio"] {
  accent-color: var(--primary);
  width: 18px;
  height: 18px;
}

.option-label {
  font-size: 16px;
}

.nav-buttons {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.nav-buttons .btn-primary {
  width: auto;
  padding: 10px 28px;
}

/* ---- Drawing ---- */
.drawing-requirements {
  background: #fff8e1;
  padding: 8px 14px;
  border-radius: 6px;
  font-size: 13px;
  color: #8d6e00;
  margin: 12px 0;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.canvas-wrapper {
  display: flex;
  align-items: stretch;
  gap: 0;
  margin: 20px 0;
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 8px;
  overflow: auto;
}

.y-axis-label {
  writing-mode: vertical-lr;
  text-orientation: mixed;
  text-align: center;
  padding: 8px;
  font-size: 13px;
  color: var(--text-secondary);
  background: #fafbfc;
  border-right: 1px solid var(--border);
  white-space: nowrap;
}

.drawing-canvas {
  flex: 1;
  cursor: crosshair;
  min-width: 450px;
}

.x-axis-labels {
  display: flex;
  justify-content: space-around;
  padding: 6px 20px 6px 40px;
  font-size: 13px;
  color: var(--text-secondary);
}

.x-axis-labels span.active {
  color: var(--primary-dark);
  font-weight: 600;
}

.drawing-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 8px 0;
}

.plot-count {
  font-size: 14px;
  color: var(--text-secondary);
}

.trend-badge {
  font-size: 14px;
  padding: 4px 14px;
  background: #e6f4ea;
  color: #1b7a3d;
  border-radius: 12px;
  font-weight: 600;
}

/* ---- Self Check ---- */
.check-section {
  margin: 20px 0;
}

.check-item {
  margin-bottom: 20px;
  padding: 16px;
  background: #fafbfc;
  border-radius: 8px;
}

.check-item p {
  font-size: 15px;
  margin-bottom: 10px;
  font-weight: 500;
}

.check-option {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-right: 24px;
  cursor: pointer;
  font-size: 14px;
}

.check-option input[type="radio"] {
  accent-color: var(--primary);
}

.note-input {
  width: 100%;
  height: 80px;
  padding: 10px 14px;
  border: 1px solid var(--border);
  border-radius: 8px;
  font-size: 14px;
  font-family: inherit;
  resize: vertical;
}

.note-input:focus {
  border-color: var(--primary);
  outline: none;
}

/* ---- Submit Success ---- */
.success-card h1 {
  margin: 12px 0;
}

.success-icon {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: #e6f4ea;
  color: var(--success);
  font-size: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto;
}

.success-card p {
  color: var(--text-secondary);
  margin-bottom: 24px;
}

/* ---- Teacher Dashboard ---- */
.dashboard-container {
  max-width: 1100px;
  margin: 0 auto;
  padding: 20px;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.dashboard-header h1 {
  font-size: 22px;
  color: var(--primary-dark);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.teacher-label {
  font-size: 13px;
  background: var(--primary-dark);
  color: #fff;
  padding: 4px 12px;
  border-radius: 12px;
}

.loading {
  text-align: center;
  padding: 40px;
  color: var(--text-secondary);
}

.stats-row {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
}

.stat-card {
  background: var(--card-bg);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  padding: 16px 24px;
  display: flex;
  flex-direction: column;
}

.stat-card.green { border-left: 4px solid var(--success); }

.stat-number {
  font-size: 28px;
  font-weight: 700;
  color: var(--success);
}

.stat-label {
  font-size: 13px;
  color: var(--text-secondary);
}

.table-wrapper {
  background: var(--card-bg);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  overflow-x: auto;
}

.dashboard-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.dashboard-table th {
  padding: 12px 8px;
  background: #f5f7fa;
  font-weight: 600;
  text-align: center;
  border-bottom: 2px solid var(--border);
  white-space: nowrap;
}

.dashboard-table td {
  padding: 10px 8px;
  text-align: center;
  border-bottom: 1px solid var(--border);
}

.name-cell { text-align: left !important; font-weight: 500; }

.score-cell { font-size: 16px; }

.correct { color: var(--success); font-weight: 600; }
.wrong { color: var(--danger); font-weight: 600; }
.empty { color: #ccc; }

.view-link {
  color: var(--primary);
  text-decoration: none;
  font-size: 13px;
}

.view-link:hover { text-decoration: underline; }

.empty-row {
  padding: 40px !important;
  color: var(--text-secondary);
}

/* ---- Student Detail ---- */
.detail-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.detail-content .content-card {
  margin: 0;
}

.drawing-review {
  margin: 12px 0;
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 8px;
  overflow: hidden;
}

.review-canvas {
  display: block;
  margin: 0 auto;
}

.drawing-score {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  font-size: 14px;
  margin: 8px 0;
}

.drawing-score span {
  padding: 4px 12px;
  background: #f5f7fa;
  border-radius: 6px;
}

/* ---- Responsive ---- */
@media (max-width: 640px) {
  .login-card { padding: 24px; }
  .content-card { padding: 20px; }
  .dashboard-container { padding: 10px; }
  .data-table { font-size: 12px; }
  .data-table th, .data-table td { padding: 6px 4px; }
  .canvas-wrapper { overflow-x: auto; }
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/style.css
git commit -m "feat: add global styles and visual polish for all views"
```

---

### Task 14: Integration — Wire Flask to Serve Frontend in Production

**Files:**
- Modify: `backend/app.py`

- [ ] **Step 1: Add static file serving to Flask**

In `backend/app.py`, update `create_app()` to serve frontend static files in production (when built):

```python
# backend/app.py — final version
from flask import Flask, send_from_directory
from flask_cors import CORS
import os


def create_app():
    app = Flask(__name__, static_folder='static', static_url_path='')
    app.secret_key = 'change-me-in-production'
    CORS(app, supports_credentials=True, origins=['http://localhost:5173'])

    from auth import auth_bp
    app.register_blueprint(auth_bp)

    from submit import submit_bp
    app.register_blueprint(submit_bp)

    from teacher import teacher_bp
    app.register_blueprint(teacher_bp)

    @app.route('/api/health')
    def health():
        return {'ok': True}

    # Serve frontend in production (static files from `frontend/dist`)
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    if os.path.isdir(static_dir):

        @app.route('/')
        def serve_index():
            return send_from_directory(static_dir, 'index.html')

        @app.route('/assets/<path:filename>')
        def serve_assets(filename):
            return send_from_directory(os.path.join(static_dir, 'assets'), filename)

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
```

- [ ] **Step 2: Build frontend**

Run: `cd frontend && npm run build`
Expected: static files generated in `backend/static/`.

- [ ] **Step 3: Verify production mode**

Run: `cd backend && python app.py`
Open `http://localhost:5000`. Verify the full app works — student login, answer questions, submit, and teacher dashboard — all served from a single Flask process.

- [ ] **Step 4: Commit**

```bash
git add backend/app.py
git commit -m "feat: add production static file serving to Flask"
```

---

### Task 15: End-to-End Smoke Test

- [ ] **Step 1: Start both servers in dev mode**

```bash
# Terminal 1
cd backend && python app.py

# Terminal 2
cd frontend && npm run dev
```

- [ ] **Step 2: Test student complete flow**

1. Open `http://localhost:5173` → Login page visible
2. Enter "测试学生" → See data preview page with two tables
3. Click "开始答题" → Q1 appears
4. Answer all 7 questions, verify prev/next works, verify selected answer persists
5. Reach Q7 (prediction: 45/50/20), select one, click "进入绘图题"
6. Click 6 points on canvas → points appear with labels, line auto-connects, trend shown
7. Click "重新描点" → points cleared
8. Click 6 new points → click "完成绘图，继续"
9. Self-check page: fill in all 3 radio groups + note text
10. Click "提交" → see success page with checkmark
11. Click "切换用户" → back to login page

- [ ] **Step 3: Test teacher flow**

1. Navigate to `http://localhost:5173/teacher` → Teacher login visible
2. Login with admin/password → Dashboard loads
3. See "测试学生" in the table with answers and scores
4. Click "查看" → Student detail page shows all answers, drawing replay, self-check
5. Click "← 返回概览" → Back to dashboard

- [ ] **Step 4: Test tablet sharing**

1. Login as "学生A", answer Q1-Q3, submit
2. Login as "学生B", answer all questions, submit
3. Teacher dashboard shows both students

- [ ] **Step 5: Commit any fixes**

```bash
git add -A
git commit -m "chore: final integration fixes from smoke test"
```
