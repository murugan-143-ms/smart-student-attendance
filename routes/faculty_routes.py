from flask import Blueprint, render_template, request, redirect, url_for, flash
from routes.auth_routes import login_required
from db import query_all, query_one, execute

faculty_bp = Blueprint('faculty', __name__)

@faculty_bp.route('/faculty')
@login_required
def index():
    faculty_list = query_all("""
        SELECT f.faculty_id, f.faculty_code, f.name, f.email, f.phone,
               f.designation, f.qualification,
               d.dept_id, d.dept_name, d.dept_code,
               COUNT(cl.class_id) AS allocated_classes
        FROM faculty f
        JOIN departments d ON f.dept_id = d.dept_id
        LEFT JOIN classes cl ON f.faculty_id = cl.faculty_id
        GROUP BY f.faculty_id, f.faculty_code, f.name, f.email, f.phone,
                 f.designation, f.qualification, d.dept_id, d.dept_name, d.dept_code
        ORDER BY f.faculty_id ASC
    """)

    departments = query_all("SELECT * FROM departments ORDER BY dept_name ASC")
    courses = query_all("SELECT c.*, d.dept_code FROM courses c JOIN departments d ON c.dept_id = d.dept_id ORDER BY c.course_name ASC")
    classes = query_all("""
        SELECT cl.*, c.course_code, c.course_name, f.name AS faculty_name
        FROM classes cl
        JOIN courses c ON cl.course_id = c.course_id
        JOIN faculty f ON cl.faculty_id = f.faculty_id
        ORDER BY cl.academic_year DESC, c.course_code ASC
    """)

    return render_template(
        'faculty.html',
        faculty_list=faculty_list,
        departments=departments,
        courses=courses,
        classes=classes
    )

@faculty_bp.route('/faculty/add', methods=['POST'])
@login_required
def add():
    code = request.form.get('faculty_code', '').strip()
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    phone = request.form.get('phone', '').strip()
    dept_id = request.form.get('dept_id')
    designation = request.form.get('designation', '').strip()
    qualification = request.form.get('qualification', '').strip()

    if not code or not name or not email or not dept_id or not qualification:
        flash('Please fill in all mandatory faculty fields.', 'danger')
        return redirect(url_for('faculty.index'))

    existing = query_one(
        "SELECT * FROM faculty WHERE faculty_code = %s OR email = %s",
        (code, email)
    )
    if existing:
        flash(f'Faculty Code "{code}" or Email "{email}" already registered.', 'danger')
        return redirect(url_for('faculty.index'))

    try:
        execute("""
            INSERT INTO faculty (faculty_code, name, email, phone, dept_id, designation, qualification)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (code, name, email, phone, dept_id, designation, qualification))
        flash(f'Faculty "{name}" successfully added to registry!', 'success')
    except Exception as e:
        flash(f'Database error: {str(e)}', 'danger')

    return redirect(url_for('faculty.index'))

@faculty_bp.route('/faculty/edit/<int:faculty_id>', methods=['POST'])
@login_required
def edit(faculty_id):
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    phone = request.form.get('phone', '').strip()
    dept_id = request.form.get('dept_id')
    designation = request.form.get('designation', '').strip()
    qualification = request.form.get('qualification', '').strip()

    try:
        execute("""
            UPDATE faculty
            SET name = %s, email = %s, phone = %s, dept_id = %s,
                designation = %s, qualification = %s
            WHERE faculty_id = %s
        """, (name, email, phone, dept_id, designation, qualification, faculty_id))
        flash(f'Faculty member "{name}" updated successfully.', 'success')
    except Exception as e:
        flash(f'Update failed: {str(e)}', 'danger')

    return redirect(url_for('faculty.index'))

@faculty_bp.route('/faculty/delete/<int:faculty_id>', methods=['POST'])
@login_required
def delete(faculty_id):
    try:
        execute("DELETE FROM faculty WHERE faculty_id = %s", (faculty_id,))
        flash('Faculty member removed from records.', 'info')
    except Exception as e:
        flash(f'Cannot delete faculty member: {str(e)}', 'danger')

    return redirect(url_for('faculty.index'))

@faculty_bp.route('/faculty/assign', methods=['POST'])
@login_required
def assign_course():
    faculty_id = request.form.get('faculty_id')
    course_id = request.form.get('course_id')
    academic_year = request.form.get('academic_year', '2026-2027')
    semester = request.form.get('semester', 5)
    section = request.form.get('section', 'A')
    classroom = request.form.get('classroom', 'LH-101')

    if not faculty_id or not course_id:
        flash('Please select both faculty member and course.', 'danger')
        return redirect(url_for('faculty.index'))

    try:
        execute("""
            INSERT INTO classes (course_id, faculty_id, academic_year, semester, section, classroom)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (course_id, faculty_id, academic_year, semester, section, classroom))
        flash('Course successfully assigned to faculty!', 'success')
    except Exception as e:
        flash(f'Assignment failed (Duplicate or error): {str(e)}', 'danger')

    return redirect(url_for('faculty.index'))

