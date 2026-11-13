import csv
import io
from flask import Blueprint, render_template, request, Response, make_response
from routes.auth_routes import login_required
from db import query_all, query_one

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/reports')
@login_required
def index():
    report_type = request.args.get('type', 'general')
    dept_filter = request.args.get('dept_id', '')

    # Students for student-wise report dropdown
    students = query_all("SELECT student_id, register_number, name FROM students ORDER BY register_number ASC")

    # Low attendance report
    low_att_records = query_all("""
        SELECT s.student_id, s.register_number, s.name, s.email, d.dept_code, s.year, s.section,
               COUNT(a.attendance_id) AS total_sessions,
               SUM(CASE WHEN a.status='Present' THEN 1 ELSE 0 END) AS present_count,
               ROUND(COALESCE((CAST(SUM(CASE WHEN a.status='Present' THEN 1 ELSE 0 END) AS REAL) / NULLIF(COUNT(a.attendance_id),0))*100, 0), 2) AS attendance_pct,
               ROUND(COALESCE(perf.avg_score, 0), 2) AS avg_marks
        FROM students s
        JOIN departments d ON s.dept_id = d.dept_id
        LEFT JOIN attendance a ON s.student_id = a.student_id
        LEFT JOIN (
            SELECT student_id, AVG(total_marks) AS avg_score
            FROM performances GROUP BY student_id
        ) perf ON s.student_id = perf.student_id
        GROUP BY s.student_id, s.register_number, s.name, s.email, d.dept_code, s.year, s.section, perf.avg_score
        HAVING attendance_pct < 75.0
        ORDER BY attendance_pct ASC
    """)

    # Top Rankers report
    top_rankers = query_all("""
        SELECT s.student_id, s.register_number, s.name, d.dept_code, s.year,
               ROUND(AVG(p.total_marks), 2) AS average_marks,
               ROUND(COALESCE(att.pct, 0), 2) AS attendance_percentage,
               COUNT(p.performance_id) AS subjects_evaluated
        FROM students s
        JOIN departments d ON s.dept_id = d.dept_id
        JOIN performances p ON s.student_id = p.student_id
        LEFT JOIN (
            SELECT student_id, (SUM(CASE WHEN status='Present' THEN 1 ELSE 0 END)*100.0/COUNT(*)) AS pct
            FROM attendance GROUP BY student_id
        ) att ON s.student_id = att.student_id
        GROUP BY s.student_id, s.register_number, s.name, d.dept_code, s.year, att.pct
        ORDER BY average_marks DESC
        LIMIT 10
    """)

    # Department summary
    dept_summaries = query_all("""
        SELECT d.dept_id, d.dept_code, d.dept_name,
               COUNT(DISTINCT s.student_id) AS total_students,
               ROUND(COALESCE(AVG(p.total_marks), 0), 2) AS dept_avg_marks,
               ROUND(COALESCE(AVG(att.pct), 0), 2) AS dept_avg_attendance
        FROM departments d
        LEFT JOIN students s ON d.dept_id = s.dept_id
        LEFT JOIN performances p ON s.student_id = p.student_id
        LEFT JOIN (
            SELECT student_id, (SUM(CASE WHEN status='Present' THEN 1 ELSE 0 END)*100.0/COUNT(*)) AS pct
            FROM attendance GROUP BY student_id
        ) att ON s.student_id = att.student_id
        GROUP BY d.dept_id, d.dept_code, d.dept_name
    """)

    return render_template(
        'reports.html',
        report_type=report_type,
        students=students,
        low_att_records=low_att_records,
        top_rankers=top_rankers,
        dept_summaries=dept_summaries
    )

@reports_bp.route('/reports/student-card/<int:student_id>')
@login_required
def student_card(student_id):
    student = query_one("""
        SELECT s.*, d.dept_name, d.dept_code
        FROM students s
        JOIN departments d ON s.dept_id = d.dept_id
        WHERE s.student_id = %s
    """, (student_id,))

    if not student:
        return "Student not found", 404

    # Performance breakdown
    performances = query_all("""
        SELECT p.*, c.course_code, c.course_name, c.credits, e.exam_name
        FROM performances p
        JOIN courses c ON p.course_id = c.course_id
        JOIN exams e ON p.exam_id = e.exam_id
        WHERE p.student_id = %s
        ORDER BY c.course_code ASC
    """, (student_id,))

    # Attendance breakdown
    att_summary = query_all("""
        SELECT c.course_code, c.course_name,
               COUNT(a.attendance_id) AS total_sessions,
               SUM(CASE WHEN a.status='Present' THEN 1 ELSE 0 END) AS attended,
               COALESCE(ROUND(SUM(CASE WHEN a.status='Present' THEN 1 ELSE 0 END)*100.0/NULLIF(COUNT(a.attendance_id),0), 2), 0.0) AS pct
        FROM courses c
        LEFT JOIN attendance a ON c.course_id = a.course_id AND a.student_id = %s
        WHERE c.dept_id = %s
        GROUP BY c.course_id, c.course_code, c.course_name
    """, (student_id, student['dept_id']))

    # GPA Calculation
    grade_points = {'O': 10, 'A+': 9, 'A': 8, 'B+': 7, 'B': 6, 'C': 5, 'F': 0}
    total_credit_points = 0
    total_credits = 0
    for p in performances:
        credits = p.get('credits', 3)
        g_point = grade_points.get(p.get('grade', 'F'), 0)
        total_credit_points += g_point * credits
        total_credits += credits

    gpa = round(total_credit_points / total_credits, 2) if total_credits > 0 else 0.0

    return render_template(
        'student_card_print.html',
        student=student,
        performances=performances,
        att_summary=att_summary,
        gpa=gpa
    )

@reports_bp.route('/reports/export-csv')
@login_required
def export_csv():
    """Export master student analytics report as downloadable CSV."""
    records = query_all("""
        SELECT s.register_number, s.name AS student_name, d.dept_code, s.year, s.semester, s.section,
               ROUND(COALESCE(att.pct, 0), 2) AS attendance_percentage,
               ROUND(COALESCE(perf.avg_marks, 0), 2) AS average_academic_marks,
               CASE 
                   WHEN COALESCE(att.pct, 0) >= 75 THEN 'Eligible'
                   ELSE 'Detained / Low Attendance'
               END AS attendance_status
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
        ORDER BY s.register_number ASC
    """)

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=[
        'register_number', 'student_name', 'dept_code', 'year', 'semester', 'section',
        'attendance_percentage', 'average_academic_marks', 'attendance_status'
    ])
    writer.writeheader()
    writer.writerows(records)

    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=student_analytics_report.csv"
    response.headers["Content-type"] = "text/csv"
    return response
