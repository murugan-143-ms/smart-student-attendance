from flask import Blueprint, render_template, request, redirect, url_for, flash
from routes.auth_routes import login_required
from db import query_all, query_one, execute

student_bp = Blueprint('students', __name__)

@student_bp.route('/students')
@login_required
def index():
    search = request.args.get('search', '').strip()
    dept_filter = request.args.get('dept', '')
    year_filter = request.args.get('year', '')

    sql = """
        SELECT s.student_id, s.register_number, s.name, s.email, s.phone,
               s.year, s.semester, s.section, s.gender,
               d.dept_id, d.dept_code, d.dept_name,
               ROUND(COALESCE(att.pct, 0), 2) AS attendance_percentage,
               ROUND(COALESCE(perf.avg_marks, 0), 2) AS avg_marks
        FROM students s
        JOIN departments d ON s.dept_id = d.dept_id
        LEFT JOIN (
            SELECT student_id, (SUM(CASE WHEN status='Present' THEN 1 ELSE 0 END)*100.0/COUNT(*)) AS pct
            FROM attendance GROUP BY student_id
        ) att ON s.student_id = att.student_id
        LEFT JOIN (
            SELECT student_id, AVG(total_marks) AS avg_marks
            FROM performances GROUP BY student_id
        ) perf ON s.student_id = perf.student_id
        WHERE 1=1
    """
    params = []

    if search:
        sql += " AND (s.register_number LIKE %s OR s.name LIKE %s OR s.email LIKE %s)"
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

    if dept_filter:
        sql += " AND s.dept_id = %s"
        params.append(dept_filter)

    if year_filter:
        sql += " AND s.year = %s"
        params.append(year_filter)

    sql += " ORDER BY s.register_number ASC"

    students = query_all(sql, params)
    departments = query_all("SELECT * FROM departments ORDER BY dept_name ASC")

    return render_template(
        'students.html',
        students=students,
        departments=departments,
        search=search,
        selected_dept=dept_filter,
        selected_year=year_filter
    )

@student_bp.route('/students/add', methods=['POST'])
@login_required
def add():
    reg_no = request.form.get('register_number', '').strip()
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    phone = request.form.get('phone', '').strip()
    dept_id = request.form.get('dept_id')
    year = request.form.get('year')
    semester = request.form.get('semester')
    section = request.form.get('section', 'A').strip()
    gender = request.form.get('gender', 'Male')

    # Validations
    if not reg_no or not name or not email or not dept_id or not year or not semester:
        flash('Please fill in all mandatory fields.', 'danger')
        return redirect(url_for('students.index'))

    # Check duplicates
    existing = query_one(
        "SELECT * FROM students WHERE register_number = %s OR email = %s",
        (reg_no, email)
    )
    if existing:
        flash(f'Duplicate Record! Student with Register Number "{reg_no}" or Email "{email}" already exists.', 'danger')
        return redirect(url_for('students.index'))

    try:
        execute("""
            INSERT INTO students (register_number, name, email, phone, dept_id, year, semester, section, gender)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (reg_no, name, email, phone, dept_id, year, semester, section, gender))
        flash(f'Student "{name}" (Reg: {reg_no}) added successfully into database!', 'success')
    except Exception as e:
        flash(f'Database Error while adding student: {str(e)}', 'danger')

    return redirect(url_for('students.index'))

@student_bp.route('/students/edit/<int:student_id>', methods=['POST'])
@login_required
def edit(student_id):
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    phone = request.form.get('phone', '').strip()
    dept_id = request.form.get('dept_id')
    year = request.form.get('year')
    semester = request.form.get('semester')
    section = request.form.get('section', 'A').strip()
    gender = request.form.get('gender', 'Male')

    if not name or not email or not dept_id:
        flash('Required student fields cannot be blank.', 'danger')
        return redirect(url_for('students.index'))

    # Duplicate email check for other students
    existing = query_one(
        "SELECT * FROM students WHERE email = %s AND student_id != %s",
        (email, student_id)
    )
    if existing:
        flash(f'Email "{email}" is already used by another student.', 'danger')
        return redirect(url_for('students.index'))

    try:
        execute("""
            UPDATE students 
            SET name = %s, email = %s, phone = %s, dept_id = %s,
                year = %s, semester = %s, section = %s, gender = %s
            WHERE student_id = %s
        """, (name, email, phone, dept_id, year, semester, section, gender, student_id))
        flash(f'Student details for "{name}" updated successfully.', 'success')
    except Exception as e:
        flash(f'Error updating student: {str(e)}', 'danger')

    return redirect(url_for('students.index'))

@student_bp.route('/students/delete/<int:student_id>', methods=['POST'])
@login_required
def delete(student_id):
    student = query_one("SELECT name, register_number FROM students WHERE student_id = %s", (student_id,))
    if not student:
        flash('Student not found.', 'danger')
        return redirect(url_for('students.index'))

    try:
        execute("DELETE FROM students WHERE student_id = %s", (student_id,))
        flash(f'Student "{student["name"]}" ({student["register_number"]}) was permanently removed.', 'info')
    except Exception as e:
        flash(f'Cannot delete student: {str(e)}', 'danger')

    return redirect(url_for('students.index'))

@student_bp.route('/students/view/<int:student_id>')
@login_required
def view_profile(student_id):
    student = query_one("""
        SELECT s.*, d.dept_name, d.dept_code
        FROM students s
        JOIN departments d ON s.dept_id = d.dept_id
        WHERE s.student_id = %s
    """, (student_id,))

    if not student:
        flash('Student record not found.', 'warning')
        return redirect(url_for('students.index'))

    # Attendance logs
    attendance_records = query_all("""
        SELECT a.attendance_id, a.attendance_date, a.status, a.remarks,
               c.course_code, c.course_name
        FROM attendance a
        JOIN courses c ON a.course_id = c.course_id
        WHERE a.student_id = %s
        ORDER BY a.attendance_date DESC
    """, (student_id,))

    # Attendance summary
    att_summary = query_all("""
        SELECT c.course_code, c.course_name,
               COUNT(a.attendance_id) AS total_sessions,
               SUM(CASE WHEN a.status='Present' THEN 1 ELSE 0 END) AS present_count,
               SUM(CASE WHEN a.status='Absent' THEN 1 ELSE 0 END) AS absent_count,
               COALESCE(ROUND(SUM(CASE WHEN a.status='Present' THEN 1 ELSE 0 END)*100.0/NULLIF(COUNT(a.attendance_id),0), 2), 0.0) AS percentage
        FROM courses c
        LEFT JOIN attendance a ON c.course_id = a.course_id AND a.student_id = %s
        WHERE c.dept_id = %s
        GROUP BY c.course_id, c.course_code, c.course_name
    """, (student_id, student['dept_id']))

    # Performance marks
    performances = query_all("""
        SELECT p.*, c.course_code, c.course_name, e.exam_name, e.exam_type
        FROM performances p
        JOIN courses c ON p.course_id = c.course_id
        JOIN exams e ON p.exam_id = e.exam_id
        WHERE p.student_id = %s
        ORDER BY e.exam_date DESC
    """, (student_id,))

    # Overall calculation
    tot_classes = len(attendance_records)
    tot_present = sum(1 for a in attendance_records if a['status'] == 'Present')
    overall_att_pct = round((tot_present / tot_classes * 100.0), 2) if tot_classes > 0 else 0.0

    avg_marks = round(sum(p['total_marks'] for p in performances) / len(performances), 2) if performances else 0.0

    return render_template(
        'student_profile.html',
        student=student,
        attendance_records=attendance_records,
        att_summary=att_summary,
        performances=performances,
        overall_att_pct=overall_att_pct,
        avg_marks=avg_marks
    )
