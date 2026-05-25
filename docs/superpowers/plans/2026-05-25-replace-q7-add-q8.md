# Replace Q7 + Add Q8 Fill-Blank — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace Q7 (prediction question) with a car-travel multiple-choice question and add Q8 as a fill-in-the-blank question (water heating experiment) between the choice questions and drawing page.

**Architecture:** Extend the existing `answers` table with a `sub_no` column to represent Q8's 4 sub-blanks. Add a new `FillBlankQuestion.vue` page with card-style layout. The store, API, submit endpoint, and teacher views all gain fill-blank awareness.

**Tech Stack:** Vue 3 (Composition API) + Pinia + Vue Router + Flask + SQLite

---

### Task 1: Update backend data models and reference answers

**Files:**
- Modify: `backend/models.py`

- [ ] **Step 1: Update init_db() table schema**

Replace the `answers` table definition in the `init_db()` `executescript` call. Add `sub_no` column and widen the CHECK constraint, then append a migration block for existing databases.

In `backend/models.py`, replace the `answers` table in the `executescript` block (lines 27-36):

```python
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
```

After the `executescript` call (after line 57), add migration logic for existing databases:

```python
    # Migration: add sub_no column and widen CHECK for existing databases
    cols = [c[1] for c in conn.execute("PRAGMA table_info(answers)").fetchall()]
    if 'sub_no' not in cols:
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
```

- [ ] **Step 2: Update REFERENCE_ANSWERS and add FILL_BLANK_ANSWERS**

Replace the existing `REFERENCE_ANSWERS` line (line 63) and add `FILL_BLANK_ANSWERS` below it:

```python
REFERENCE_ANSWERS = {1: 'A', 2: 'B', 3: 'A', 4: 'B', 5: 'A', 6: 'A', 7: 'D'}

FILL_BLANK_ANSWERS = {8: {1: '25', 2: '4', 3: '11', 4: '100'}}
```

- [ ] **Step 3: Commit**

```bash
git add backend/models.py
git commit -m "feat: extend answers table for Q8 fill-blank support, update reference answers"
```

---

### Task 2: Update student login to restore Q8 data

**Files:**
- Modify: `backend/auth.py`

- [ ] **Step 1: Load existing fill-blank answers on re-login**

In `backend/auth.py`, replace the existing answers query (lines 32-36) to also fetch `sub_no`:

```python
        ans_rows = conn.execute(
            'SELECT question_no, answer, sub_no FROM answers WHERE student_id = ?', (student_id,)
        ).fetchall()
        for r in ans_rows:
            qno = str(r['question_no'])
            if r['sub_no'] > 0:
                if qno not in existing_answers:
                    existing_answers[qno] = {}
                existing_answers[qno][str(r['sub_no'])] = r['answer']
            else:
                existing_answers[qno] = r['answer']
```

- [ ] **Step 2: Commit**

```bash
git add backend/auth.py
git commit -m "feat: restore existing fill-blank answers on student re-login"
```

---

### Task 3: Update submit endpoint for Q8 fill-blank

**Files:**
- Modify: `backend/submit.py`

- [ ] **Step 1: Handle fill_blank in submit endpoint**

In `backend/submit.py`, update the import line (line 4) to include `FILL_BLANK_ANSWERS`:

```python
from models import get_db, REFERENCE_ANSWERS, FILL_BLANK_ANSWERS, grade_drawing
```

After the answers loop (after line 38, before the drawing section), add fill_blank handling:

```python
    # 1b. Save fill-blank answers (Q8)
    fill_blank = data.get('fill_blank', {})
    for qno_str, sub_answers in fill_blank.items():
        qno = int(qno_str)
        for sub_str, sub_ans in sub_answers.items():
            sub_no = int(sub_str)
            expected = FILL_BLANK_ANSWERS.get(qno, {}).get(sub_no)
            is_correct = 1 if (expected and str(sub_ans).strip() == expected) else 0
            scores[f'{qno}_{sub_no}'] = bool(is_correct)
            conn.execute("""
                INSERT INTO answers (student_id, question_no, answer, is_correct, sub_no, updated_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(student_id, question_no, sub_no)
                DO UPDATE SET answer = excluded.answer, is_correct = excluded.is_correct, updated_at = CURRENT_TIMESTAMP
            """, (student_id, qno, str(sub_ans).strip(), is_correct, sub_no))
```

- [ ] **Step 2: Commit**

```bash
git add backend/submit.py
git commit -m "feat: handle fill-blank answers in submit endpoint with per-sub grading"
```

---

### Task 4: Update teacher endpoints for Q8

**Files:**
- Modify: `backend/teacher.py`

- [ ] **Step 1: Update dashboard to include Q8 sub-scores**

In `backend/teacher.py`, update the dashboard query (lines 27-33) to include `sub_no`. Replace the `ans_rows` query and processing:

```python
        ans_rows = conn.execute(
            'SELECT question_no, answer, is_correct, sub_no FROM answers WHERE student_id = ?', (s['id'],)
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
```

Also update the import at line 21:

```python
    from models import get_db, REFERENCE_ANSWERS, FILL_BLANK_ANSWERS
```

- [ ] **Step 2: Update student_detail to include Q8 sub-answers**

Replace the `ans_rows` query in `student_detail` (lines 67-71):

```python
    ans_rows = conn.execute(
        'SELECT question_no, answer, is_correct, sub_no FROM answers WHERE student_id = ? ORDER BY question_no, sub_no',
        (student_id,)
    ).fetchall()
    answers = [{'question_no': r['question_no'], 'answer': r['answer'], 'is_correct': bool(r['is_correct']), 'sub_no': r['sub_no']} for r in ans_rows]
```

- [ ] **Step 3: Commit**

```bash
git add backend/teacher.py
git commit -m "feat: include Q8 fill-blank data in teacher dashboard and student detail"
```

---

### Task 5: Update frontend store and API

**Files:**
- Modify: `frontend/src/stores/student.js`
- Modify: `frontend/src/api.js`

- [ ] **Step 1: Add fillBlank state to student store**

In `frontend/src/stores/student.js`, add `fillBlank` state and setter after the existing `drawingPoints` line:

```js
  const fillBlank = ref({})
```

Add setter after `setDrawing`:

```js
  function setFillBlank(data) { fillBlank.value = { ...fillBlank.value, ...data } }
```

Update `reset()` to clear `fillBlank`:

```js
  function reset() {
    studentId.value = null; name.value = ''
    answers.value = {}
    drawingPoints.value = []
    fillBlank.value = {}
    selfCheck.pointCheck = ''; selfCheck.lineCheck = ''; selfCheck.drawCheck = ''; selfCheck.note = ''
  }
```

Update the return statement to export `fillBlank` and `setFillBlank`:

```js
  return { studentId, name, answers, drawingPoints, fillBlank, selfCheck, setStudent, setAnswer, setDrawing, setFillBlank, setSelfCheck, reset }
```

- [ ] **Step 2: Update submitAll to include fill_blank**

In `frontend/src/api.js`, update the `submitAll` function signature and body:

```js
export function submitAll(studentId, answers, fillBlank, drawingPoints, selfCheck) {
  const fillBlankPayload = {}
  if (fillBlank && Object.keys(fillBlank).length > 0) {
    fillBlankPayload[8] = fillBlank[8] || {}
  }
  return api.post('/submit', {
    student_id: studentId,
    answers: Object.entries(answers).map(([qno, ans]) => ({ question_no: parseInt(qno), answer: ans })),
    fill_blank: fillBlankPayload,
    drawing_points: drawingPoints,
    self_check: {
      point_check: selfCheck.pointCheck || '',
      line_check: selfCheck.lineCheck || '',
      draw_check: selfCheck.drawCheck || '',
      note: selfCheck.note || '',
    },
  })
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/stores/student.js frontend/src/api.js
git commit -m "feat: add fillBlank state to store and wire into submitAll API"
```

---

### Task 6: Update router and ChoiceQuestions page

**Files:**
- Modify: `frontend/src/router/index.js`
- Modify: `frontend/src/views-student/ChoiceQuestions.vue`

- [ ] **Step 1: Add /fill-blank route**

In `frontend/src/router/index.js`, add the route between `/questions` and `/drawing`:

```js
  { path: '/questions', name: 'ChoiceQuestions', component: () => import('../views-student/ChoiceQuestions.vue') },
  { path: '/fill-blank', name: 'FillBlankQuestion', component: () => import('../views-student/FillBlankQuestion.vue') },
  { path: '/drawing', name: 'DrawingQuestion', component: () => import('../views-student/DrawingQuestion.vue') },
```

- [ ] **Step 2: Replace Q7 text and options, update navigation**

In `frontend/src/views-student/ChoiceQuestions.vue`, replace the last element in the `questions` array (lines 89-97):

```js
  { text: '小明一家周末驾车去湿地公园游玩。汽车以50千米/时的速度行驶1小时到达湿地公园。他们一家在湿地公园玩了3小时后，驾车以原来的速度返回。以下图像中，正确的是（ ）', options: {
    A: '0～1小时离家距离从0增加到50千米；1～4小时保持50千米不变；4～5小时从50千米增加到100千米',
    B: '0～1小时离家距离从0增加到50千米；1～3小时保持50千米不变；3～4小时从50千米增加到100千米',
    C: '0～1小时离家距离从0增加到50千米；1～4小时保持50千米不变；4～5小时从50千米增加到100千米，纵轴标注为"离家距离/千米"',
    D: '0～1小时离家距离从0增加到50千米；1～4小时保持50千米不变；4～6小时从50千米下降到0千米，纵轴标注为"离家距离/千米"',
  } },
```

Replace the "进入绘图题" button (lines 65-72):

```html
        <button
          v-else
          @click="goToFillBlank"
          class="btn-primary"
          :disabled="!hasAnswered"
        >
          {{ hasAnswered ? '进入填空题' : '请先选择答案' }}
        </button>
```

Replace the `goToDrawing` function (line 102) with:

```js
function goToFillBlank() { router.push('/fill-blank') }
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/router/index.js frontend/src/views-student/ChoiceQuestions.vue
git commit -m "feat: replace Q7 with car-travel question, add /fill-blank route"
```

---

### Task 7: Create FillBlankQuestion page

**Files:**
- Create: `frontend/src/views-student/FillBlankQuestion.vue`

- [ ] **Step 1: Write the FillBlankQuestion component**

Create `frontend/src/views-student/FillBlankQuestion.vue`:

```html
<template>
  <div class="page-container">
    <div class="page-header">
      <span class="student-badge">{{ store.name }} 同学</span>
    </div>

    <div class="content-card">
      <div class="question-header">
        <span class="question-number">第8题</span>
        <span class="question-type">填空题</span>
      </div>

      <p class="question-text">小宁在做"一壶水加热"实验时，记录了水温变化情况，并制成统计图。</p>

      <div class="table-section">
        <h4>小宁做一壶水加热实验 — 水温变化统计表</h4>
        <table class="data-table">
          <thead>
            <tr><th v-for="t in times" :key="t">时间/分</th></tr>
            <tr><th v-for="(_, i) in temps" :key="i">{{ i }}</th></tr>
          </thead>
          <tbody>
            <tr><td v-for="t in temps" :key="t">水温/℃</td></tr>
            <tr><td v-for="t in temps" :key="t">{{ t }}</td></tr>
          </tbody>
        </table>
      </div>

      <div class="fill-blank-section">
        <div class="fill-blank-item">
          <label>加热前水温是 <input type="text" v-model="q8[1]" class="blank-input" placeholder="___" /> ℃</label>
        </div>
        <div class="fill-blank-item">
          <label>水加热到 60℃ 时，用了 <input type="text" v-model="q8[2]" class="blank-input" placeholder="___" /> 分钟</label>
        </div>
        <div class="fill-blank-item">
          <label>烧开这壶水一共用了 <input type="text" v-model="q8[3]" class="blank-input" placeholder="___" /> 分钟</label>
        </div>
        <div class="fill-blank-item">
          <label>如果持续加热到第 16 分钟，此时水温是 <input type="text" v-model="q8[4]" class="blank-input" placeholder="___" /> ℃</label>
        </div>
      </div>

      <div class="nav-buttons">
        <button @click="$router.push('/questions')" class="btn-secondary">上一题</button>
        <button @click="goToDrawing" class="btn-primary">
          进入绘图题
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useStudentStore } from '../stores/student.js'

const router = useRouter()
const store = useStudentStore()

const temps = [25, 28, 35, 46, 60, 73, 84, 90, 93, 96, 98, 100]
const times = temps.map((_, i) => i)

const q8 = reactive({ 1: '', 2: '', 3: '', 4: '' })

onMounted(() => {
  if (store.fillBlank && store.fillBlank[8]) {
    Object.assign(q8, store.fillBlank[8])
  }
})

function goToDrawing() {
  store.setFillBlank({ 8: { ...q8 } })
  router.push('/drawing')
}
</script>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views-student/FillBlankQuestion.vue
git commit -m "feat: add FillBlankQuestion page for Q8 water heating experiment"
```

---

### Task 8: Update StudentLogin and SelfCheck for fill-blank flow

**Files:**
- Modify: `frontend/src/views-student/StudentLogin.vue`
- Modify: `frontend/src/views-student/SelfCheck.vue`

- [ ] **Step 1: Restore fill-blank answers on re-login**

In `frontend/src/views-student/StudentLogin.vue`, after the existing `existing_answers` restoration block (after line 64, inside `handleLogin`), add:

```js
    if (d.existing_answers) {
      for (const [qno, ans] of Object.entries(d.existing_answers)) {
        if (typeof ans === 'object') {
          store.setFillBlank({ [parseInt(qno)]: ans })
        } else {
          store.setAnswer(parseInt(qno), ans)
        }
      }
    }
```

- [ ] **Step 2: Pass fillBlank to submitAll in SelfCheck**

In `frontend/src/views-student/SelfCheck.vue`, update the `submitAll` call (line 67-72) to pass `store.fillBlank`:

```js
    await submitAll(
      store.studentId,
      store.answers,
      store.fillBlank,
      store.drawingPoints,
      { pointCheck: pointCheck.value, lineCheck: lineCheck.value, drawCheck: drawCheck.value, note: note.value }
    )
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views-student/StudentLogin.vue frontend/src/views-student/SelfCheck.vue
git commit -m "feat: restore Q8 fill-blank on re-login and include in submit"
```

---

### Task 9: Update teacher views for Q8 display

**Files:**
- Modify: `frontend/src/views-teacher/Dashboard.vue`
- Modify: `frontend/src/views-teacher/StudentDetail.vue`

- [ ] **Step 1: Update Dashboard table for 8 questions**

In `frontend/src/views-teacher/Dashboard.vue`, update the table header to show 8 questions (lines 28-29):

```html
              <th v-for="q in 8" :key="q">Q{{ q }}</th>
```

Update the score cells (lines 36-40):

```html
              <td v-for="q in 8" :key="q" class="score-cell">
                <span v-if="s.scores[q] === true || s.scores[q + '_1'] !== undefined" class="correct">&#10003;</span>
                <span v-else-if="s.scores[q] === false" class="wrong">&#10007;</span>
                <span v-else class="empty">-</span>
              </td>
```

- [ ] **Step 2: Update StudentDetail for Q7 corrected answer and Q8 display**

In `frontend/src/views-teacher/StudentDetail.vue`, update `correctAnswers` (line 93):

```js
const correctAnswers = { 1: 'A', 2: 'B', 3: 'A', 4: 'B', 5: 'A', 6: 'A', 7: 'D' }
```

Replace the answers table template (lines 12-23) to split choice and fill-blank answers:

```html
        <h3>选择题答案</h3>
        <table class="data-table">
          <thead><tr><th>题号</th><th>学生答案</th><th>正确答案</th><th>结果</th></tr></thead>
          <tbody>
            <tr v-for="a in choiceAnswers" :key="a.question_no">
              <td>{{ a.question_no }}</td>
              <td>{{ a.answer || '-' }}</td>
              <td>{{ correctAnswers[a.question_no] }}</td>
              <td :class="a.is_correct ? 'correct' : 'wrong'">{{ a.is_correct ? '✓' : '✗' }}</td>
            </tr>
          </tbody>
        </table>

        <h3 v-if="fillBlankAnswers.length > 0" style="margin-top: 20px;">填空题答案（第8题）</h3>
        <table v-if="fillBlankAnswers.length > 0" class="data-table">
          <thead><tr><th>子题号</th><th>学生答案</th><th>正确答案</th><th>结果</th></tr></thead>
          <tbody>
            <tr v-for="a in fillBlankAnswers" :key="'fb' + a.sub_no">
              <td>第{{ a.sub_no }}空</td>
              <td>{{ a.answer || '-' }}</td>
              <td>{{ fillBlankKeys[a.sub_no] }}</td>
              <td :class="a.is_correct ? 'correct' : 'wrong'">{{ a.is_correct ? '✓' : '✗' }}</td>
            </tr>
          </tbody>
        </table>
```

In the `<script setup>`, update the `vue` import (line 85) to add `computed`:

```js
import { ref, onMounted, computed } from 'vue'
```

After the `correctAnswers` line, add the computed properties:

```js
const choiceAnswers = computed(() => (detail.value?.answers || []).filter(a => a.sub_no === 0))
const fillBlankAnswers = computed(() => (detail.value?.answers || []).filter(a => a.sub_no > 0))
const fillBlankKeys = { 1: '25', 2: '4', 3: '11', 4: '100' }
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views-teacher/Dashboard.vue frontend/src/views-teacher/StudentDetail.vue
git commit -m "feat: update teacher views for Q7 answer change and Q8 fill-blank display"
```

---

### Task 10: Verify end-to-end

- [ ] **Step 1: Start backend and verify DB migration**

```bash
cd backend && python3 app.py &
sleep 2
# Check that app starts without errors, DB migration runs
```

- [ ] **Step 2: Start frontend dev server**

```bash
cd frontend && npm run dev &
sleep 3
```

- [ ] **Step 3: Verify student flow**

Open the browser and verify:
1. Login → DataPreview → Q1-Q7 (Q7 shows car-travel question)
2. Q7 "进入填空题" button goes to `/fill-blank`
3. FillBlankQuestion shows data table + 4 inputs
4. "进入绘图题" goes to `/drawing`
5. Drawing → SelfCheck → Submit

- [ ] **Step 4: Verify teacher views**

1. Login to teacher: admin/password
2. Dashboard shows Q1-Q8 columns
3. Click "查看" on a student — detail shows Q1-Q7 choice answers and Q8 fill-blank table

- [ ] **Step 5: Verify re-login restores Q8 data**

Log in as the same student again — Q8 fill-blank answers should be pre-filled.

- [ ] **Step 6: Commit if any final fixes needed**

```bash
git add -A
git commit -m "chore: final adjustments for Q8 fill-blank feature"
```
