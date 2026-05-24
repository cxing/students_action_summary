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
