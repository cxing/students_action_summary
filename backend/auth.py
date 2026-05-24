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
