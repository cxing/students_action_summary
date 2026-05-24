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
    conn.execute('DELETE FROM drawings WHERE student_id = ?', (student_id,))
    conn.execute('DELETE FROM self_check WHERE student_id = ?', (student_id,))
    conn.commit()
    conn.close()

    return jsonify({'ok': True})
