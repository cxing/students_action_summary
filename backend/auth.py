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
        is_new = False
    else:
        cur = conn.execute('INSERT INTO students (name) VALUES (?)', (name,))
        conn.commit()
        student_id = cur.lastrowid
        student_name = name
        is_new = True

    # Load existing answers, drawing, self_check for returning students
    existing_answers = {}
    existing_drawing = None
    existing_self_check = None
    if not is_new:
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

        drawing = conn.execute('SELECT points FROM drawings WHERE student_id = ?', (student_id,)).fetchone()
        if drawing:
            import json
            existing_drawing = json.loads(drawing['points'])

        sc = conn.execute(
            'SELECT point_check, line_check, draw_check, note FROM self_check WHERE student_id = ?', (student_id,)
        ).fetchone()
        if sc:
            existing_self_check = {
                'pointCheck': sc['point_check'],
                'lineCheck': sc['line_check'],
                'drawCheck': sc['draw_check'],
                'note': sc['note'],
            }

    conn.close()

    return jsonify({
        'student_id': student_id,
        'name': student_name,
        'existing_answers': existing_answers,
        'existing_drawing': existing_drawing or [],
        'existing_self_check': existing_self_check,
    })


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
