from flask import Blueprint, render_template, jsonify
from routes.auth_routes import login_required
from db import query_all, get_active_info
import analytics

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    kpis = analytics.compute_overall_kpis()
    insights = analytics.generate_academic_insights()
    db_info = get_active_info()

    # Low attendance students (<75%)
    low_att_students = query_all("""
        SELECT s.student_id, s.register_number, s.name, d.dept_code, s.year, s.section,
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
        WHERE COALESCE(att.pct, 0) < 75.0
        ORDER BY attendance_percentage ASC
        LIMIT 6
    """)

    # Top performing students (>=85%)
    top_students = query_all("""
        SELECT s.student_id, s.register_number, s.name, d.dept_code, s.year,
               ROUND(COALESCE(att.pct, 0), 2) AS attendance_percentage,
               ROUND(COALESCE(perf.avg_marks, 0), 2) AS avg_marks,
               COUNT(p.performance_id) AS exams_taken
        FROM students s
        JOIN departments d ON s.dept_id = d.dept_id
        LEFT JOIN (
            SELECT student_id, (SUM(CASE WHEN status='Present' THEN 1 ELSE 0 END)*100.0/COUNT(*)) AS pct
            FROM attendance GROUP BY student_id
        ) att ON s.student_id = att.student_id
        JOIN performances p ON s.student_id = p.student_id
        LEFT JOIN (
            SELECT student_id, AVG(total_marks) AS avg_marks
            FROM performances GROUP BY student_id
        ) perf ON s.student_id = perf.student_id
        GROUP BY s.student_id, s.register_number, s.name, d.dept_code, s.year, att.pct, perf.avg_marks
        HAVING avg_marks >= 85.0
        ORDER BY avg_marks DESC
        LIMIT 6
    """)

    # Recent attendance dates
    recent_dates = query_all("""
        SELECT attendance_date, COUNT(*) AS total_marked,
               SUM(CASE WHEN status='Present' THEN 1 ELSE 0 END) AS present_count,
               SUM(CASE WHEN status='Absent' THEN 1 ELSE 0 END) AS absent_count
        FROM attendance
        GROUP BY attendance_date
        ORDER BY attendance_date DESC
        LIMIT 5
    """)

    return render_template(
        'dashboard.html',
        kpis=kpis,
        insights=insights,
        low_att_students=low_att_students,
        top_students=top_students,
        recent_dates=recent_dates,
        db_info=db_info
    )

@dashboard_bp.route('/api/dashboard/charts')
@login_required
def charts_api():
    dept_comp = analytics.get_department_comparison()
    grade_dist = analytics.get_grade_distribution()
    return jsonify({
        'departments': dept_comp,
        'grades': grade_dist
    })

