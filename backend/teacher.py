# backend/teacher.py
from functools import wraps
from flask import Blueprint, jsonify, session, request

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
        labels = ['Q1 点与线', 'Q2 条形vs折线', 'Q3 汽车行程', 'Q4 铁棒入水', 'Q5 水温加热']
        correct_counts = []
        total_students = conn.execute('SELECT COUNT(*) FROM students').fetchone()[0] or 1

        for qno in range(1, 6):
            if qno in (2, 5):
                total_subs = len([k for k in REFERENCE_ANSWERS.get(qno, {}) if k > 0])
                if qno == 5:
                    total_subs = 4
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
