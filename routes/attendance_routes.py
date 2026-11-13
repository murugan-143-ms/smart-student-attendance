from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, flash
from routes.auth_routes import login_required
from db import query_all, query_one, execute

attendance_bp = Blueprint('attendance', __name__)

@attendance_bp.route('/attendance')
@login_required
def index():
    courses = query_all("SELECT * FROM courses ORDER BY course_name ASC")
    today_str = date.today().strftime('%Y-%m-%d')
    selected_course_id = request.args.get('course_id')
    selected_date = request.args.get('date', today_str)

    if not selected_course_id and courses:
        selected_course_id = str(courses[0]['course_id'])

    # Fetch students for the selected course
    students_in_course = []
    attendance_map = {}
    if selected_course_id:
        course = query_one("SELECT * FROM courses WHERE course_id = %s", (selected_course_id,))
        if course:
            students_in_course = query_all("""
                SELECT s.student_id, s.register_number, s.name, s.section, d.dept_code
                FROM students s
                JOIN departments d ON s.dept_id = d.dept_id
                WHERE s.dept_id = %s AND s.semester = %s
                ORDER BY s.register_number ASC
            """, (course['dept_id'], course['semester']))

            # Check if attendance already marked for this date
            existing_records = query_all("""
                SELECT student_id, status, remarks
                FROM attendance
                WHERE course_id = %s AND attendance_date = %s
            """, (selected_course_id, selected_date))

            for rec in existing_records:
                attendance_map[rec['student_id']] = rec

    return render_template(
        'attendance.html',
        courses=courses,
        selected_course_id=int(selected_course_id) if selected_course_id else None,
        selected_date=selected_date,
        students=students_in_course,
        attendance_map=attendance_map
    )

@attendance_bp.route('/attendance/mark-batch', methods=['POST'])
@login_required
def mark_batch():
    course_id = request.form.get('course_id')
    attendance_date = request.form.get('attendance_date')
    student_ids = request.form.getlist('student_ids')

    if not course_id or not attendance_date:
        flash('Course and Date are required.', 'danger')
        return redirect(url_for('attendance.index'))

    # All students marked Present will have their id in 'present_ids'
    present_ids = set(request.form.getlist('present_ids'))

    count_marked = 0
    for s_id in student_ids:
        status = 'Present' if s_id in present_ids else 'Absent'
        remarks = request.form.get(f'remarks_{s_id}', 'Recorded by Admin')

        # Check if record exists
        existing = query_one(
            "SELECT attendance_id FROM attendance WHERE student_id = %s AND course_id = %s AND attendance_date = %s",
            (s_id, course_id, attendance_date)
        )

        if existing:
            execute("""
                UPDATE attendance
                SET status = %s, remarks = %s, marked_at = CURRENT_TIMESTAMP
                WHERE attendance_id = %s
            """, (status, remarks, existing['attendance_id']))
        else:
            execute("""
                INSERT INTO attendance (student_id, course_id, attendance_date, status, remarks)
                VALUES (%s, %s, %s, %s, %s)
            """, (s_id, course_id, attendance_date, status, remarks))
        count_marked += 1

    flash(f'Attendance recorded successfully for {count_marked} students on {attendance_date}!', 'success')
    return redirect(url_for('attendance.index', course_id=course_id, date=attendance_date))

@attendance_bp.route('/attendance/view')
@login_required
def view_records():
    filter_date = request.args.get('date', '')
    filter_course = request.args.get('course_id', '')

    sql = """
        SELECT a.attendance_id, a.attendance_date, a.status, a.remarks, a.marked_at,
               s.student_id, s.register_number, s.name AS student_name,
               d.dept_code, c.course_code, c.course_name
        FROM attendance a
        JOIN students s ON a.student_id = s.student_id
        JOIN departments d ON s.dept_id = d.dept_id
        JOIN courses c ON a.course_id = c.course_id
        WHERE 1=1
    """
    params = []
    if filter_date:
        sql += " AND a.attendance_date = %s"
        params.append(filter_date)
    if filter_course:
        sql += " AND a.course_id = %s"
        params.append(filter_course)

    sql += " ORDER BY a.attendance_date DESC, s.register_number ASC LIMIT 200"

    records = query_all(sql, params)
    courses = query_all("SELECT * FROM courses ORDER BY course_name ASC")

    # Dates list for quick filter
    available_dates = query_all("SELECT DISTINCT attendance_date FROM attendance ORDER BY attendance_date DESC LIMIT 30")

    return render_template(
        'attendance_view.html',
        records=records,
        courses=courses,
        available_dates=available_dates,
        filter_date=filter_date,
        filter_course=filter_course
    )

@attendance_bp.route('/attendance/summary')
@login_required
def summary():
    filter_dept = request.args.get('dept_id', '')
    filter_status = request.args.get('status', '') # 'low' or 'eligible'

    sql = """
        SELECT s.student_id, s.register_number, s.name AS student_name,
               d.dept_code, d.dept_name, s.year, s.semester, s.section,
               COUNT(a.attendance_id) AS total_classes,
               SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) AS present_count,
               SUM(CASE WHEN a.status = 'Absent' THEN 1 ELSE 0 END) AS absent_count,
               ROUND(
                   COALESCE(
                       (CAST(SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) AS REAL) / NULLIF(COUNT(a.attendance_id), 0)) * 100, 
                       0
                   ), 2
               ) AS attendance_percentage,
               CASE 
                   WHEN ROUND((CAST(SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) AS REAL) / NULLIF(COUNT(a.attendance_id), 0)) * 100, 2) >= 75.00 THEN 'Eligible'
                   ELSE 'Detained / Low Attendance'
               END AS eligibility_status
        FROM students s
        JOIN departments d ON s.dept_id = d.dept_id
        LEFT JOIN attendance a ON s.student_id = a.student_id
        WHERE 1=1
    """
    params = []
    if filter_dept:
        sql += " AND s.dept_id = %s"
        params.append(filter_dept)

    sql += " GROUP BY s.student_id, s.register_number, s.name, d.dept_code, d.dept_name, s.year, s.semester, s.section"

    if filter_status == 'low':
        sql += " HAVING attendance_percentage < 75.0"
    elif filter_status == 'eligible':
        sql += " HAVING attendance_percentage >= 75.0"

    sql += " ORDER BY attendance_percentage ASC"

    summary_list = query_all(sql, params)
    departments = query_all("SELECT * FROM departments ORDER BY dept_name ASC")

    return render_template(
        'attendance_summary.html',
        summary_list=summary_list,
        departments=departments,
        filter_dept=filter_dept,
        filter_status=filter_status
    )

