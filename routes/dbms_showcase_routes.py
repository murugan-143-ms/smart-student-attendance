import re
from flask import Blueprint, render_template, request, jsonify
from routes.auth_routes import login_required
import db
from db import query_all, get_active_info, get_connection

dbms_bp = Blueprint('dbms', __name__)

SQL_CONCEPTS = [

    # =========================================================
    # TABLE STRUCTURE: SHOW TABLES
    # =========================================================
    {
        'id': 'show_tables',
        'category': 'Table Structure',
        'title': 'SHOW TABLES — All 10 Database Tables',
        'description': 'Lists every relational table in the student_analytics_db schema. The system uses 10 normalized tables: departments, faculty, students, courses, classes, attendance, exams, assignments, performances, admins.',
        'sql': """-- ==============================================
-- SHOW ALL TABLES IN student_analytics_db
-- ==============================================
-- This command lists all tables in the
-- currently selected MySQL database schema.
-- Our schema has 10 normalized relational tables
-- designed in 3NF (Third Normal Form).
SHOW TABLES;"""
    },

    # =========================================================
    # TABLE STRUCTURE: DESCRIBE STUDENTS
    # =========================================================
    {
        'id': 'describe_students',
        'category': 'Table Structure',
        'title': 'DESCRIBE — Students Table Schema',
        'description': 'Shows the column definitions, data types, keys, and constraints of the students table.',
        'sql': """-- ==============================================
-- DESCRIBE students TABLE
-- ==============================================
-- DESCRIBE shows each column's:
--   Field      -> Column name
--   Type       -> Data type (INT, VARCHAR, DATE...)
--   Null       -> Whether NULL values are allowed
--   Key        -> PRI (Primary), MUL (Foreign), UNI (Unique)
--   Default    -> Default value
--   Extra      -> AUTO_INCREMENT etc.
DESCRIBE students;"""
    },

    # =========================================================
    # TABLE STRUCTURE: DESCRIBE ATTENDANCE
    # =========================================================
    {
        'id': 'describe_attendance',
        'category': 'Table Structure',
        'title': 'DESCRIBE — Attendance Table Schema',
        'description': 'Displays the column-level structure of the attendance table, including foreign key references to students and courses.',
        'sql': """-- ==============================================
-- DESCRIBE attendance TABLE
-- ==============================================
-- The attendance table links:
--   student_id  -> FK → students(student_id)
--   course_id   -> FK → courses(course_id)
--   UNIQUE(student_id, course_id, attendance_date)
--     ensures one record per student per course per day.
DESCRIBE attendance;"""
    },

    # =========================================================
    # DQL: BASIC SELECT
    # =========================================================
    {
        'id': 'dql_select',
        'category': 'DQL (Data Query Language)',
        'title': 'Multi-Table SELECT with Arithmetic Aliases',
        'description': 'Extracts consolidated student profiles with calculated attendance metrics and performance summaries.',
        'sql': """-- ==============================================
-- DQL: SELECT with JOIN and Column Aliases
-- ==============================================
-- SELECT   : Chooses specific columns to display
-- AS       : Renames output columns with aliases
-- FROM     : Specifies the primary (base) table
-- JOIN     : Merges departments using the FK dept_id
-- ORDER BY : Sorts result by register_number ascending
-- LIMIT    : Returns only the first 5 rows
SELECT 
    s.register_number,          -- Unique roll number
    s.name        AS student_name,
    d.dept_code   AS department,
    s.year        AS academic_year,
    s.semester
FROM   students s                          -- Base table
JOIN   departments d ON s.dept_id = d.dept_id  -- FK join
ORDER  BY s.register_number ASC
LIMIT  5;"""
    },

    # =========================================================
    # JOINS: INNER JOIN (3 tables)
    # =========================================================
    {
        'id': 'inner_join',
        'category': 'Joins',
        'title': 'INNER JOIN — Student + Department + Performance',
        'description': 'Returns only rows that have matching records in all three joined tables (students, departments, performances).',
        'sql': """-- ==============================================
-- INNER JOIN: 3-Table Merge
-- ==============================================
-- INNER JOIN returns ONLY rows where the join
-- condition is TRUE in both tables.
-- Rows with no matching records are excluded.
--
-- TABLE CHAIN:
--   students  ──(dept_id)──► departments
--   students  ──(student_id)──► performances
SELECT
    s.register_number,
    s.name           AS student_name,
    d.dept_name      AS department,       -- from departments
    p.total_marks,                        -- from performances
    p.grade
FROM      students    s
INNER JOIN departments d  ON s.dept_id    = d.dept_id
INNER JOIN performances p ON s.student_id = p.student_id
ORDER BY  p.total_marks DESC
LIMIT 8;"""
    },

    # =========================================================
    # JOINS: LEFT JOIN
    # =========================================================
    {
        'id': 'left_join',
        'category': 'Joins',
        'title': 'LEFT OUTER JOIN — All Students + Attendance Count',
        'description': 'Returns every student row even if no attendance has been recorded yet. Missing attendance appears as 0.',
        'sql': """-- ==============================================
-- LEFT OUTER JOIN
-- ==============================================
-- LEFT JOIN returns ALL rows from the LEFT table
-- (students), and the matched rows from the RIGHT
-- table (attendance). If no match → NULL (or 0 here).
--
-- Use Case: Find students with zero attendance records.
--
--   students  ──LEFT JOIN──► attendance
SELECT
    s.register_number,
    s.name,
    d.dept_code,
    -- COALESCE replaces NULL with 0 when no attendance
    COALESCE(COUNT(a.attendance_id), 0) AS sessions_recorded
FROM      students    s
JOIN      departments d  ON s.dept_id    = d.dept_id
LEFT JOIN attendance  a  ON s.student_id = a.student_id
GROUP BY  s.student_id, s.register_number, s.name, d.dept_code
ORDER BY  sessions_recorded ASC
LIMIT 8;"""
    },

    # =========================================================
    # JOINS: SELF JOIN
    # =========================================================
    {
        'id': 'self_join',
        'category': 'Joins',
        'title': 'SELF JOIN — Classmates in Same Dept & Year',
        'description': 'Joins the students table with itself to find pairs of students sharing the same department and academic year.',
        'sql': """-- ==============================================
-- SELF JOIN
-- ==============================================
-- A SELF JOIN joins a table to ITSELF using two
-- different aliases (s1 and s2).
-- Useful for comparing rows within the same table.
--
-- Condition: same dept, same year, different student
--   s1.student_id < s2.student_id  → avoids duplicates
SELECT
    s1.name  AS student_a,
    s2.name  AS student_b,
    s1.year  AS shared_year,
    s1.dept_id
FROM students s1
INNER JOIN students s2
    ON  s1.dept_id    = s2.dept_id      -- same department
    AND s1.year       = s2.year         -- same academic year
    AND s1.student_id < s2.student_id   -- prevent (A,B)+(B,A)
LIMIT 6;"""
    },

    # =========================================================
    # JOINS: CROSS JOIN
    # =========================================================
    {
        'id': 'cross_join',
        'category': 'Joins',
        'title': 'CROSS JOIN — Cartesian Product (Course × Exam)',
        'description': 'Generates every possible combination of courses and exam types — the full Cartesian product.',
        'sql': """-- ==============================================
-- CROSS JOIN (Cartesian Product)
-- ==============================================
-- CROSS JOIN combines EVERY row of table A with
-- EVERY row of table B.
-- If A has 5 rows and B has 2 → result = 10 rows.
--
-- Use Case: Generate a course-exam schedule matrix.
SELECT
    c.course_code,
    c.course_name,
    e.exam_type
FROM courses c
CROSS JOIN (
    SELECT DISTINCT exam_type   -- Pick unique exam types
    FROM   exams
    LIMIT  2
) e
ORDER BY c.course_code
LIMIT 8;"""
    },

    # =========================================================
    # VIEWS: VIEW DEFINITION
    # =========================================================
    {
        'id': 'view_definition',
        'category': 'Views',
        'title': 'VIEW Definition — v_student_attendance_summary',
        'description': 'Shows the CREATE VIEW SQL that defines the attendance summary view. A VIEW is a saved SELECT query that acts as a virtual table.',
        'sql': """-- ==============================================
-- WHAT IS A VIEW?
-- ==============================================
-- A VIEW is a virtual table defined by a SELECT query.
-- It does NOT store data physically.
-- Every time you SELECT from a view, MySQL runs
-- the underlying query live against the base tables.
--
-- Benefits:
--   • Simplifies complex multi-table queries
--   • Provides security (hide sensitive columns)
--   • Reusable logic across multiple queries
--
-- Our VIEW: v_student_attendance_summary
--   Joins: students + departments + courses + attendance
--   Computes: attendance_percentage, eligibility_status
SHOW CREATE VIEW v_student_attendance_summary;"""
    },

    # =========================================================
    # VIEWS: QUERY A VIEW
    # =========================================================
    {
        'id': 'view_demo',
        'category': 'Views',
        'title': 'SELECT from VIEW — Performance Summary',
        'description': 'Queries the pre-built view v_student_performance_summary which wraps a 4-table JOIN into a single virtual table.',
        'sql': """-- ==============================================
-- QUERYING A VIEW (Virtual Table)
-- ==============================================
-- v_student_performance_summary is a VIEW that
-- internally joins:
--   performances  ──► students
--   students      ──► departments
--   performances  ──► courses
--   performances  ──► exams
--
-- You query it exactly like a real table:
SELECT
    register_number,
    student_name,
    dept_code        AS dept,
    course_name,
    total_marks,
    grade,
    remarks
FROM v_student_performance_summary
ORDER BY total_marks DESC
LIMIT 8;"""
    },

    # =========================================================
    # VIEWS: ATTENDANCE VIEW
    # =========================================================
    {
        'id': 'view_attendance',
        'category': 'Views',
        'title': 'SELECT from VIEW — Attendance Summary',
        'description': 'Reads from the v_student_attendance_summary view which calculates live attendance percentage and eligibility for each student per course.',
        'sql': """-- ==============================================
-- VIEW: v_student_attendance_summary
-- ==============================================
-- This VIEW pre-computes for each student:
--   total_classes       → COUNT(attendance records)
--   present_count       → SUM where status='Present'
--   attendance_percentage → (present/total)*100
--   eligibility_status  → 'Eligible' or 'Detained'
--
-- Based on University rule: < 75% → Detained
SELECT
    register_number,
    student_name,
    dept_code,
    course_code,
    total_classes,
    present_count,
    attendance_percentage,
    eligibility_status
FROM v_student_attendance_summary
ORDER BY attendance_percentage ASC
LIMIT 10;"""
    },

    # =========================================================
    # AGGREGATES & GROUP BY
    # =========================================================
    {
        'id': 'aggregates_groupby',
        'category': 'Aggregate Functions & GROUP BY',
        'title': 'GROUP BY with COUNT, AVG, MIN, MAX',
        'description': 'Calculates department-level performance metrics using SQL aggregate functions and GROUP BY.',
        'sql': """-- ==============================================
-- AGGREGATE FUNCTIONS + GROUP BY
-- ==============================================
-- Aggregate functions operate on a SET of rows:
--   COUNT() → number of rows
--   AVG()   → arithmetic mean
--   MAX()   → highest value
--   MIN()   → lowest value
--   SUM()   → total sum
--
-- GROUP BY partitions rows into groups (by dept_code)
-- before the aggregate functions are applied.
SELECT
    d.dept_code,
    COUNT(DISTINCT s.student_id)      AS total_students,
    ROUND(AVG(p.total_marks), 2)      AS avg_marks,
    ROUND(MAX(p.total_marks), 2)      AS highest_marks,
    ROUND(MIN(p.total_marks), 2)      AS lowest_marks,
    ROUND(SUM(p.total_marks), 2)      AS total_marks_sum
FROM departments d
JOIN students    s ON d.dept_id    = s.dept_id
JOIN performances p ON s.student_id = p.student_id
GROUP BY d.dept_code
ORDER BY avg_marks DESC;"""
    },

    # =========================================================
    # HAVING CLAUSE
    # =========================================================
    {
        'id': 'having_clause',
        'category': 'HAVING Clause',
        'title': 'HAVING — Detained Students (Attendance < 75%)',
        'description': 'Filters grouped attendance results to identify students detained due to low attendance.',
        'sql': """-- ==============================================
-- HAVING CLAUSE
-- ==============================================
-- WHERE  filters individual rows BEFORE grouping.
-- HAVING filters aggregated groups AFTER grouping.
--
-- Rule: Use HAVING when filtering on aggregate values
--       like COUNT(), AVG(), SUM()...
--
-- Use Case: Flag students with attendance_pct < 75%
SELECT
    s.register_number,
    s.name,
    COUNT(a.attendance_id)                                AS total_sessions,
    SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) AS present_count,
    -- Computed attendance percentage per student
    ROUND(
        (SUM(CASE WHEN a.status='Present' THEN 1 ELSE 0 END) * 100.0
        / COUNT(a.attendance_id)), 2
    )                                                      AS attendance_pct
FROM students   s
JOIN attendance a ON s.student_id = a.student_id
GROUP BY s.student_id, s.register_number, s.name
HAVING attendance_pct < 75.00    -- ← HAVING filters groups
ORDER BY attendance_pct ASC;"""
    },

    # =========================================================
    # SUBQUERY
    # =========================================================
    {
        'id': 'subquery_scalar',
        'category': 'Subqueries',
        'title': 'Subquery in WHERE — Students Above Class Average',
        'description': 'Uses a scalar subquery to compare each student\'s marks against the dynamically computed class average.',
        'sql': """-- ==============================================
-- SUBQUERY (Scalar Subquery in WHERE)
-- ==============================================
-- A SUBQUERY is a SELECT query nested inside another.
-- A SCALAR subquery returns exactly one value (one row,
-- one column) used for comparison.
--
-- Here the inner query computes the average mark,
-- and the outer query finds all students above it.
--
--   Inner: SELECT AVG(total_marks) FROM performances
--          → returns a single number (e.g. 72.3)
--   Outer: WHERE p.total_marks > 72.3
SELECT
    s.register_number,
    s.name,
    p.total_marks,
    p.grade,
    -- Show how much above average each student is
    ROUND(p.total_marks - (SELECT AVG(total_marks) FROM performances), 2)
        AS marks_above_avg
FROM performances p
JOIN students s ON p.student_id = s.student_id
WHERE p.total_marks > (
    SELECT AVG(total_marks)   -- ← Scalar Subquery
    FROM   performances
)
ORDER BY p.total_marks DESC
LIMIT 8;"""
    }
]

@dbms_bp.route('/dbms-showcase')
@login_required
def index():
    db_info = get_active_info()
    return render_template(
        'dbms_showcase.html',
        concepts=SQL_CONCEPTS,
        db_info=db_info
    )

@dbms_bp.route('/api/dbms/execute', methods=['POST'])
@login_required
def execute_query():
    concept_id = request.json.get('concept_id')
    concept = next((c for c in SQL_CONCEPTS if c['id'] == concept_id), None)
    if not concept:
        return jsonify({'error': 'Concept not found'}), 404

    try:
        raw_sql = concept['sql']
        # Strip SQL single-line comments (-- ...) to get executable statement
        clean_lines = [ln for ln in raw_sql.splitlines() if not ln.strip().startswith('--')]
        executable_sql = '\n'.join(clean_lines).strip().rstrip(';')

        # Detect meta/DDL statements that bypass the ORM helper
        first_word = executable_sql.split()[0].upper() if executable_sql.split() else ''

        if first_word in ('SHOW', 'DESCRIBE', 'DESC', 'EXPLAIN'):
            conn = get_connection()
            try:
                if db._active_backend == 'MYSQL':
                    with conn.cursor() as cursor:
                        cursor.execute(executable_sql)
                        results = cursor.fetchall()
                else:
                    cursor = conn.cursor()
                    cursor.execute(executable_sql)
                    rows = cursor.fetchall()
                    results = [dict(r) for r in rows]
            finally:
                conn.close()
        else:
            results = query_all(executable_sql)

        return jsonify({
            'success': True,
            'title': concept['title'],
            'sql': concept['sql'],
            'results': results,
            'row_count': len(results)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
