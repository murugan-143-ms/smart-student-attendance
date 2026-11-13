from flask import Blueprint, render_template, request, redirect, url_for, flash
from routes.auth_routes import login_required
from db import query_all, query_one, execute

performance_bp = Blueprint('performance', __name__)

def determine_grade(pct):
    if pct >= 90.0: return 'O'
    if pct >= 80.0: return 'A+'
    if pct >= 70.0: return 'A'
    if pct >= 60.0: return 'B+'
    if pct >= 50.0: return 'B'
    if pct >= 40.0: return 'C'
    return 'F'

@performance_bp.route('/performance')
@login_required
def index():
    course_filter = request.args.get('course_id', '')
    exam_filter = request.args.get('exam_id', '')
    grade_filter = request.args.get('grade', '')

    sql = """
        SELECT p.performance_id, p.internal_marks, p.assignment_marks, p.exam_marks,
               p.total_marks, p.percentage, p.grade, p.remarks, p.created_at,
               s.student_id, s.register_number, s.name AS student_name,
               d.dept_code, c.course_id, c.course_code, c.course_name,
               e.exam_id, e.exam_name, e.exam_type
        FROM performances p
        JOIN students s ON p.student_id = s.student_id
        JOIN departments d ON s.dept_id = d.dept_id
        JOIN courses c ON p.course_id = c.course_id
        JOIN exams e ON p.exam_id = e.exam_id
        WHERE 1=1
    """
    params = []
    if course_filter:
        sql += " AND p.course_id = %s"
        params.append(course_filter)
    if exam_filter:
        sql += " AND p.exam_id = %s"
        params.append(exam_filter)
    if grade_filter:
        sql += " AND p.grade = %s"
        params.append(grade_filter)

    sql += " ORDER BY p.total_marks DESC"

    performances = query_all(sql, params)
    courses = query_all("SELECT * FROM courses ORDER BY course_name ASC")
    exams = query_all("SELECT * FROM exams ORDER BY exam_name ASC")
    assignments = query_all("SELECT * FROM assignments ORDER BY title ASC")
    students = query_all("SELECT s.student_id, s.register_number, s.name, d.dept_code FROM students s JOIN departments d ON s.dept_id = d.dept_id ORDER BY s.register_number ASC")

    return render_template(
        'performance.html',
        performances=performances,
        courses=courses,
        exams=exams,
        assignments=assignments,
        students=students,
        selected_course=course_filter,
        selected_exam=exam_filter,
        selected_grade=grade_filter
    )

@performance_bp.route('/performance/add', methods=['POST'])
@login_required
def add():
    student_id = request.form.get('student_id')
    course_id = request.form.get('course_id')
    exam_id = request.form.get('exam_id')
    assignment_id = request.form.get('assignment_id') or None
    
    try:
        internal_marks = float(request.form.get('internal_marks', 0.0))
        assignment_marks = float(request.form.get('assignment_marks', 0.0))
        exam_marks = float(request.form.get('exam_marks', 0.0))
    except ValueError:
        flash('Invalid numeric format for marks.', 'danger')
        return redirect(url_for('performance.index'))

    # Range validations
    if internal_marks < 0 or internal_marks > 30:
        flash('Internal Assessment marks must be between 0 and 30.', 'danger')
        return redirect(url_for('performance.index'))
    if assignment_marks < 0 or assignment_marks > 20:
        flash('Assignment marks must be between 0 and 20.', 'danger')
        return redirect(url_for('performance.index'))
    if exam_marks < 0 or exam_marks > 50:
        flash('Exam marks must be between 0 and 50.', 'danger')
        return redirect(url_for('performance.index'))

    # Check duplicate
    existing = query_one(
        "SELECT performance_id FROM performances WHERE student_id = %s AND course_id = %s AND exam_id = %s",
        (student_id, course_id, exam_id)
    )
    if existing:
        flash('Marks already recorded for this Student, Course, and Exam. Use Edit to modify.', 'warning')
        return redirect(url_for('performance.index'))

    total_marks = round(internal_marks + assignment_marks + exam_marks, 2)
    percentage = total_marks
    grade = determine_grade(percentage)
    remarks = 'Excellent Academic Standing' if percentage >= 85 else ('Needs Academic Improvement' if percentage < 50 else 'Satisfactory Progress')

    try:
        execute("""
            INSERT INTO performances (student_id, course_id, exam_id, assignment_id, internal_marks, assignment_marks, exam_marks, total_marks, percentage, grade, remarks)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (student_id, course_id, exam_id, assignment_id, internal_marks, assignment_marks, exam_marks, total_marks, percentage, grade, remarks))
        flash(f'Marks recorded successfully: Total = {total_marks}/100 (Grade: {grade})!', 'success')
    except Exception as e:
        flash(f'Error saving performance marks: {str(e)}', 'danger')

    return redirect(url_for('performance.index'))

@performance_bp.route('/performance/edit/<int:performance_id>', methods=['POST'])
@login_required
def edit(performance_id):
    try:
        internal_marks = float(request.form.get('internal_marks', 0.0))
        assignment_marks = float(request.form.get('assignment_marks', 0.0))
        exam_marks = float(request.form.get('exam_marks', 0.0))
    except ValueError:
        flash('Invalid numeric marks input.', 'danger')
        return redirect(url_for('performance.index'))

    total_marks = round(internal_marks + assignment_marks + exam_marks, 2)
    percentage = total_marks
    grade = determine_grade(percentage)
    remarks = 'Excellent Academic Standing' if percentage >= 85 else ('Needs Academic Improvement' if percentage < 50 else 'Satisfactory Progress')

    try:
        execute("""
            UPDATE performances
            SET internal_marks = %s, assignment_marks = %s, exam_marks = %s,
                total_marks = %s, percentage = %s, grade = %s, remarks = %s
            WHERE performance_id = %s
        """, (internal_marks, assignment_marks, exam_marks, total_marks, percentage, grade, remarks, performance_id))
        flash(f'Performance marks updated. Recalculated Total = {total_marks} (Grade: {grade})', 'success')
    except Exception as e:
        flash(f'Error updating performance: {str(e)}', 'danger')

    return redirect(url_for('performance.index'))

@performance_bp.route('/performance/delete/<int:performance_id>', methods=['POST'])
@login_required
def delete(performance_id):
    try:
        execute("DELETE FROM performances WHERE performance_id = %s", (performance_id,))
        flash('Academic performance entry removed.', 'info')
    except Exception as e:
        flash(f'Delete failed: {str(e)}', 'danger')

    return redirect(url_for('performance.index'))

