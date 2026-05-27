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

    conn.close()

    return jsonify({
        'student_id': student_id,
        'name': student_name,
        'existing_levels': existing_levels,
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
