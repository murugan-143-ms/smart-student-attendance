"""
Analytics Engine for Smart Student Attendance and Performance Analytics System
Utilizes Pandas and NumPy for descriptive, correlational, and predictive analytics.
"""

import numpy as np
import pandas as pd
from db import query_all

def get_analytics_dataset():
    """
    Extract consolidated student attendance and performance data from DB
    into Pandas DataFrames for statistical computation.
    """
    # 1. Fetch Students with Departments
    students_data = query_all("""
        SELECT s.student_id, s.register_number, s.name AS student_name,
               s.dept_id, d.dept_code, d.dept_name, s.year, s.semester, s.section, s.gender
        FROM students s
        JOIN departments d ON s.dept_id = d.dept_id
    """)
    df_students = pd.DataFrame(students_data)
    if df_students.empty:
        return None

    # 2. Fetch Attendance Records
    attendance_data = query_all("""
        SELECT a.student_id, a.course_id, a.attendance_date, a.status
        FROM attendance a
    """)
    df_att = pd.DataFrame(attendance_data)

    # 3. Fetch Performance Records
    perf_data = query_all("""
        SELECT p.student_id, p.course_id, p.exam_id, e.exam_name, e.exam_type,
               p.internal_marks, p.assignment_marks, p.exam_marks,
               p.total_marks, p.percentage, p.grade
        FROM performances p
        JOIN exams e ON p.exam_id = e.exam_id
    """)
    df_perf = pd.DataFrame(perf_data)

    # Attendance calculation per student
    if not df_att.empty:
        att_summary = df_att.groupby('student_id').agg(
            total_classes=('status', 'count'),
            present_classes=('status', lambda x: (x == 'Present').sum()),
            absent_classes=('status', lambda x: (x == 'Absent').sum())
        ).reset_index()
        att_summary['attendance_pct'] = (att_summary['present_classes'] / att_summary['total_classes'] * 100.0).round(2)
    else:
        att_summary = pd.DataFrame(columns=['student_id', 'total_classes', 'present_classes', 'absent_classes', 'attendance_pct'])

    # Performance calculation per student
    if not df_perf.empty:
        perf_summary = df_perf.groupby('student_id').agg(
            exam_count=('total_marks', 'count'),
            avg_marks=('total_marks', 'mean'),
            max_marks=('total_marks', 'max'),
            min_marks=('total_marks', 'min'),
            avg_internal=('internal_marks', 'mean'),
            avg_assignment=('assignment_marks', 'mean'),
            avg_exam=('exam_marks', 'mean')
        ).reset_index()
        perf_summary['avg_marks'] = perf_summary['avg_marks'].round(2)
    else:
        perf_summary = pd.DataFrame(columns=['student_id', 'exam_count', 'avg_marks', 'max_marks', 'min_marks'])

    # Merge everything into a master DataFrame
    master = df_students.merge(att_summary, on='student_id', how='left')
    master = master.merge(perf_summary, on='student_id', how='left')

    # Fill NA values
    master['attendance_pct'] = master['attendance_pct'].fillna(0.0)
    master['avg_marks'] = master['avg_marks'].fillna(0.0)
    master['total_classes'] = master['total_classes'].fillna(0).astype(int)
    master['present_classes'] = master['present_classes'].fillna(0).astype(int)
    master['absent_classes'] = master['absent_classes'].fillna(0).astype(int)

    return {
        'master': master,
        'attendance_raw': df_att,
        'perf_raw': df_perf,
        'students_raw': df_students
    }

def compute_overall_kpis():
    """Calculate core statistics for the admin dashboard."""
    data = get_analytics_dataset()
    if not data or data['master'].empty:
        return {
            'total_students': 0,
            'total_faculty': 0,
            'avg_attendance': 0.0,
            'avg_marks': 0.0,
            'low_attendance_count': 0,
            'top_performers_count': 0,
            'at_risk_count': 0
        }

    master = data['master']
    faculty_count = query_all("SELECT COUNT(*) AS cnt FROM faculty")[0]['cnt']

    total_students = len(master)
    avg_att = float(np.round(master['attendance_pct'].mean(), 2)) if total_students > 0 else 0.0
    avg_marks = float(np.round(master['avg_marks'].mean(), 2)) if total_students > 0 else 0.0

    low_att_count = int((master['attendance_pct'] < 75.0).sum())
    top_perf_count = int((master['avg_marks'] >= 85.0).sum())
    at_risk_count = int(((master['attendance_pct'] < 75.0) | (master['avg_marks'] < 50.0)).sum())

    return {
        'total_students': total_students,
        'total_faculty': faculty_count,
        'avg_attendance': avg_att,
        'avg_marks': avg_marks,
        'low_attendance_count': low_att_count,
        'top_performers_count': top_perf_count,
        'at_risk_count': at_risk_count
    }

def compute_correlation_and_regression():
    """
    Calculate Pearson Correlation and Linear Regression model
    between Attendance Percentage (X) and Exam Marks (Y) using NumPy.
    """
    data = get_analytics_dataset()
    if not data or data['master'].empty:
        return {
            'correlation': 0.0,
            'r_squared': 0.0,
            'slope': 0.0,
            'intercept': 0.0,
            'scatter_points': [],
            'regression_line': []
        }

    master = data['master']
    # Filter students that have both attendance and marks recorded
    valid = master[(master['total_classes'] > 0) & (master['avg_marks'] > 0)].copy()

    if len(valid) < 2:
        return {
            'correlation': 0.0,
            'r_squared': 0.0,
            'slope': 0.0,
            'intercept': 0.0,
            'scatter_points': [],
            'regression_line': []
        }

    x = valid['attendance_pct'].to_numpy(dtype=float)
    y = valid['avg_marks'].to_numpy(dtype=float)

    # 1. Pearson Correlation Coefficient (r)
    corr_matrix = np.corrcoef(x, y)
    r = float(np.round(corr_matrix[0, 1], 4)) if not np.isnan(corr_matrix[0, 1]) else 0.0
    r_squared = float(np.round(r ** 2, 4))

    # 2. Linear Regression (y = mx + c) using NumPy polyfit (degree 1)
    try:
        slope, intercept = np.polyfit(x, y, 1)
        slope = float(np.round(slope, 4))
        intercept = float(np.round(intercept, 4))
    except Exception:
        slope, intercept = 0.0, 0.0

    # 3. Generate Scatter plot data for Chart.js
    scatter_points = []
    for _, row in valid.iterrows():
        scatter_points.append({
            'x': float(row['attendance_pct']),
            'y': float(row['avg_marks']),
            'name': row['student_name'],
            'reg_no': row['register_number'],
            'dept': row['dept_code']
        })

    # 4. Generate line points from min_x to max_x
    min_x = max(0.0, float(np.min(x)) - 5.0)
    max_x = min(100.0, float(np.max(x)) + 5.0)
    line_points = [
        {'x': round(min_x, 1), 'y': round(slope * min_x + intercept, 2)},
        {'x': round(max_x, 1), 'y': round(slope * max_x + intercept, 2)}
    ]

    return {
        'correlation': r,
        'r_squared': r_squared,
        'slope': slope,
        'intercept': intercept,
        'scatter_points': scatter_points,
        'regression_line': line_points,
        'interpretation': interpret_correlation(r)
    }

def interpret_correlation(r):
    """Generate textual interpretation of Pearson correlation."""
    if r >= 0.8:
        return "Very Strong Positive Correlation: Attendance has an exceptionally high impact on examination scores. Students attending >85% of classes consistently secure distinction/O grades."
    elif r >= 0.6:
        return "Strong Positive Correlation: Solid relationship between high attendance and academic excellence."
    elif r >= 0.4:
        return "Moderate Positive Correlation: Attendance positively affects grades, with moderate variance based on prior subject aptitude."
    elif r >= 0:
        return "Weak or Negligible Positive Correlation."
    else:
        return "Negative Correlation (Anomaly detected in dataset)."

def get_quadrant_analysis():
    """
    Classify students into 4 distinct quadrants:
    Q1: Star Performers (Attendance >= 75%, Marks >= 75%)
    Q2: Struggling Diligent (Attendance >= 75%, Marks < 50%)
    Q3: Critical Risk (Attendance < 75%, Marks < 50%)
    Q4: Fast Learners (Attendance < 75%, Marks >= 75%)
    """
    data = get_analytics_dataset()
    if not data or data['master'].empty:
        return {'q1': [], 'q2': [], 'q3': [], 'q4': [], 'summary': {}}

    master = data['master']
    
    q1 = master[(master['attendance_pct'] >= 75.0) & (master['avg_marks'] >= 75.0)].to_dict('records')
    q2 = master[(master['attendance_pct'] >= 75.0) & (master['avg_marks'] < 50.0)].to_dict('records')
    q3 = master[(master['attendance_pct'] < 75.0) & (master['avg_marks'] < 50.0)].to_dict('records')
    q4 = master[(master['attendance_pct'] < 75.0) & (master['avg_marks'] >= 75.0)].to_dict('records')

    return {
        'q1': q1,
        'q2': q2,
        'q3': q3,
        'q4': q4,
        'summary': {
            'q1_count': len(q1),
            'q2_count': len(q2),
            'q3_count': len(q3),
            'q4_count': len(q4)
        }
    }

def get_department_comparison():
    """Department-wise attendance and marks comparison for bar charts."""
    data = get_analytics_dataset()
    if not data or data['master'].empty:
        return {'labels': [], 'attendance': [], 'marks': []}

    master = data['master']
    dept_grp = master.groupby('dept_code').agg(
        avg_att=('attendance_pct', 'mean'),
        avg_marks=('avg_marks', 'mean'),
        student_count=('student_id', 'count')
    ).reset_index()

    return {
        'labels': dept_grp['dept_code'].tolist(),
        'attendance': [round(x, 2) for x in dept_grp['avg_att'].tolist()],
        'marks': [round(x, 2) for x in dept_grp['avg_marks'].tolist()],
        'counts': dept_grp['student_count'].tolist()
    }

def get_grade_distribution():
    """Calculate grade distribution for Pie / Doughnut Chart."""
    perf_rows = query_all("SELECT grade, COUNT(*) AS count FROM performances GROUP BY grade ORDER BY count DESC")
    all_grades = ['O', 'A+', 'A', 'B+', 'B', 'C', 'F']
    counts_map = {row['grade']: row['count'] for row in perf_rows}
    
    labels = []
    data = []
    for g in all_grades:
        if g in counts_map or len(labels) < 6:
            labels.append(f"Grade {g}")
            data.append(counts_map.get(g, 0))

    return {
        'labels': labels,
        'data': data
    }

def generate_academic_insights():
    """Generate rule-based diagnostic insights powered by Pandas metrics."""
    data = get_analytics_dataset()
    if not data or data['master'].empty:
        return []

    master = data['master']
    insights = []

    # 1. Attendance risk alert
    low_att = master[master['attendance_pct'] < 75.0]
    if len(low_att) > 0:
        names = ", ".join(low_att['student_name'].head(3).tolist())
        more_str = f" and {len(low_att) - 3} others" if len(low_att) > 3 else ""
        insights.append({
            'type': 'warning',
            'title': 'Low Attendance Alert (< 75% Cut-off)',
            'desc': f"{len(low_att)} student(s) ({names}{more_str}) are below the mandatory 75% college attendance threshold, risking exam detention."
        })

    # 2. Critical combined risk alert
    critical = master[(master['attendance_pct'] < 75.0) & (master['avg_marks'] < 50.0)]
    if len(critical) > 0:
        insights.append({
            'type': 'danger',
            'title': 'Urgent Academic Intervention Required',
            'desc': f"{len(critical)} student(s) exhibit both poor attendance (<75%) and failing marks (<50%). Immediate parent-teacher counseling is advised."
        })

    # 3. Star performers
    stars = master[(master['attendance_pct'] >= 90.0) & (master['avg_marks'] >= 85.0)]
    if len(stars) > 0:
        insights.append({
            'type': 'success',
            'title': 'High Academic Standing Cohort',
            'desc': f"{len(stars)} students maintained >=90% attendance and secured distinction marks (>85%), validating regular class participation benefits."
        })

    # 4. Statistical Summary
    stats = compute_correlation_and_regression()
    insights.append({
        'type': 'info',
        'title': f"Statistical Correlation Metric (Pearson r = {stats['correlation']})",
        'desc': f"R² Value = {stats['r_squared']}. Approximately {round(stats['r_squared']*100, 1)}% of mark variations can be explained by class attendance consistency."
    })

    return insights

