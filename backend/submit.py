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
