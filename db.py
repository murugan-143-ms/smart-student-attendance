import os
import re
import sqlite3
import pymysql
from pymysql.cursors import DictCursor
from config import Config

_active_backend = None
_backend_info = {}

def get_mysql_connection(custom_config=None):
    """Attempt connection to MySQL server."""
    host = custom_config.get('host') if custom_config else Config.DB_HOST
    port = custom_config.get('port') if custom_config else Config.DB_PORT
    user = custom_config.get('user') if custom_config else Config.DB_USER
    password = custom_config.get('password') if custom_config else Config.DB_PASSWORD
    db_name = custom_config.get('database') if custom_config else Config.DB_NAME

    return pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=db_name,
        cursorclass=DictCursor,
        autocommit=True,
        charset='utf8mb4'
    )

def test_mysql_credentials(host, port, user, password, database=None):
    """Test MySQL connection without crashing."""
    try:
        conn = pymysql.connect(
            host=host,
            port=int(port),
            user=user,
            password=password,
            database=database if database else None,
            connect_timeout=3
        )
        conn.close()
        return True, "Successfully connected to MySQL Server!"
    except Exception as e:
        return False, str(e)

def init_sqlite_mirror():
    """Initialize SQLite database with identical schema and sample data."""
    conn = sqlite3.connect(Config.SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Create Tables
    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS departments (
        dept_id INTEGER PRIMARY KEY AUTOINCREMENT,
        dept_code TEXT NOT NULL UNIQUE,
        dept_name TEXT NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS faculty (
        faculty_id INTEGER PRIMARY KEY AUTOINCREMENT,
        faculty_code TEXT NOT NULL UNIQUE,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        phone TEXT NOT NULL,
        dept_id INTEGER NOT NULL,
        designation TEXT NOT NULL DEFAULT 'Assistant Professor',
        qualification TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (dept_id) REFERENCES departments(dept_id) ON DELETE RESTRICT
    );

    CREATE TABLE IF NOT EXISTS students (
        student_id INTEGER PRIMARY KEY AUTOINCREMENT,
        register_number TEXT NOT NULL UNIQUE,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        phone TEXT,
        dept_id INTEGER NOT NULL,
        year INTEGER NOT NULL CHECK (year BETWEEN 1 AND 4),
        semester INTEGER NOT NULL CHECK (semester BETWEEN 1 AND 8),
        section TEXT NOT NULL DEFAULT 'A',
        gender TEXT DEFAULT 'Male',
        dob DATE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (dept_id) REFERENCES departments(dept_id) ON DELETE RESTRICT
    );

    CREATE TABLE IF NOT EXISTS courses (
        course_id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_code TEXT NOT NULL UNIQUE,
        course_name TEXT NOT NULL,
        credits INTEGER NOT NULL CHECK (credits > 0),
        dept_id INTEGER NOT NULL,
        semester INTEGER NOT NULL CHECK (semester BETWEEN 1 AND 8),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (dept_id) REFERENCES departments(dept_id) ON DELETE RESTRICT
    );

    CREATE TABLE IF NOT EXISTS classes (
        class_id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_id INTEGER NOT NULL,
        faculty_id INTEGER NOT NULL,
        academic_year TEXT NOT NULL,
        semester INTEGER NOT NULL,
        section TEXT NOT NULL DEFAULT 'A',
        classroom TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE,
        FOREIGN KEY (faculty_id) REFERENCES faculty(faculty_id) ON DELETE RESTRICT,
        UNIQUE (course_id, faculty_id, academic_year, semester, section)
    );

    CREATE TABLE IF NOT EXISTS attendance (
        attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        course_id INTEGER NOT NULL,
        attendance_date DATE NOT NULL,
        status TEXT NOT NULL DEFAULT 'Present',
        remarks TEXT,
        marked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
        FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE,
        UNIQUE (student_id, course_id, attendance_date)
    );

    CREATE TABLE IF NOT EXISTS exams (
        exam_id INTEGER PRIMARY KEY AUTOINCREMENT,
        exam_name TEXT NOT NULL,
        exam_type TEXT NOT NULL,
        course_id INTEGER NOT NULL,
        max_marks REAL NOT NULL DEFAULT 100.00,
        exam_date DATE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS assignments (
        assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        max_marks REAL NOT NULL DEFAULT 20.00,
        due_date DATE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS performances (
        performance_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        course_id INTEGER NOT NULL,
        exam_id INTEGER NOT NULL,
        assignment_id INTEGER,
        internal_marks REAL NOT NULL DEFAULT 0.00,
        assignment_marks REAL NOT NULL DEFAULT 0.00,
        exam_marks REAL NOT NULL DEFAULT 0.00,
        total_marks REAL NOT NULL DEFAULT 0.00,
        percentage REAL NOT NULL DEFAULT 0.00,
        grade TEXT NOT NULL DEFAULT 'F',
        remarks TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
        FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE,
        FOREIGN KEY (exam_id) REFERENCES exams(exam_id) ON DELETE CASCADE,
        FOREIGN KEY (assignment_id) REFERENCES assignments(assignment_id) ON DELETE SET NULL,
        UNIQUE (student_id, course_id, exam_id)
    );

    CREATE TABLE IF NOT EXISTS admins (
        admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        role TEXT NOT NULL DEFAULT 'Administrator',
        last_login DATETIME,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Views
    CREATE VIEW IF NOT EXISTS v_student_attendance_summary AS
    SELECT 
        s.student_id,
        s.register_number,
        s.name AS student_name,
        d.dept_code,
        d.dept_name,
        s.year,
        s.semester,
        s.section,
        c.course_id,
        c.course_code,
        c.course_name,
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
    JOIN courses c ON c.dept_id = s.dept_id AND c.semester = s.semester
    LEFT JOIN attendance a ON s.student_id = a.student_id AND c.course_id = a.course_id
    GROUP BY s.student_id, s.register_number, s.name, d.dept_code, d.dept_name, s.year, s.semester, s.section, c.course_id, c.course_code, c.course_name;

    CREATE VIEW IF NOT EXISTS v_student_performance_summary AS
    SELECT 
        p.performance_id,
        s.student_id,
        s.register_number,
        s.name AS student_name,
        d.dept_code,
        s.year,
        s.semester,
        c.course_code,
        c.course_name,
        e.exam_name,
        e.exam_type,
        p.internal_marks,
        p.assignment_marks,
        p.exam_marks,
        p.total_marks,
        p.percentage,
        p.grade,
        p.remarks
    FROM performances p
    JOIN students s ON p.student_id = s.student_id
    JOIN departments d ON s.dept_id = d.dept_id
    JOIN courses c ON p.course_id = c.course_id
    JOIN exams e ON p.exam_id = e.exam_id;
    """)

    # Check if admin exists; if not, seed initial data
    cursor.execute("SELECT COUNT(*) FROM admins")
    if cursor.fetchone()[0] == 0:
        seed_sqlite_sample_data(cursor)

    conn.commit()
    conn.close()

def seed_sqlite_sample_data(cursor):
    """Seed comprehensive sample data into SQLite."""
    # Admin (password: admin123)
    cursor.execute("""
        INSERT INTO admins (username, password_hash, full_name, email, role) 
        VALUES ('admin', 'scrypt:32768:8:1$7W3q9QZ1fJk0mN6a$78e9fa0c71a39da5b34bc7038e24c27894a4da092305a4e32628045610ec1fbf523c9ce05500efee6ae9b5e510842db7d057a70a8d4a9f939e658ec3ef258979', 'System Administrator', 'admin@college.edu', 'Super Admin')
    """)

    # Departments
    departments = [
        (1, 'CSE', 'Computer Science and Engineering', 'Department of Computer Science & Engineering'),
        (2, 'IT', 'Information Technology', 'Department of Information Technology'),
        (3, 'AIDS', 'Artificial Intelligence & Data Science', 'Department of AI & Data Science'),
        (4, 'ECE', 'Electronics & Communication Engineering', 'Department of Electronics & Communication')
    ]
    cursor.executemany("INSERT INTO departments VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)", departments)

    # Faculty
    faculty = [
        (1, 'FAC001', 'Dr. Rajesh Sharma', 'rajesh.sharma@college.edu', '9840112345', 1, 'Professor & HOD', 'Ph.D., M.E.'),
        (2, 'FAC002', 'Prof. Priya Sundaram', 'priya.sundaram@college.edu', '9840223456', 1, 'Associate Professor', 'M.Tech, (Ph.D)'),
        (3, 'FAC003', 'Dr. Anand Kumar', 'anand.kumar@college.edu', '9840334567', 2, 'Professor', 'Ph.D, M.S.'),
        (4, 'FAC004', 'Prof. Deepa Varghese', 'deepa.varghese@college.edu', '9840445678', 3, 'Assistant Professor', 'M.Tech'),
        (5, 'FAC005', 'Dr. Karthik Raman', 'karthik.raman@college.edu', '9840556789', 4, 'Associate Professor', 'Ph.D')
    ]
    cursor.executemany("INSERT INTO faculty VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)", faculty)

    # Courses
    courses = [
        (1, 'CS301', 'Database Management Systems', 4, 1, 5),
        (2, 'CS302', 'Data Structures & Algorithms', 4, 1, 3),
        (3, 'AI301', 'Machine Learning Foundations', 4, 3, 5),
        (4, 'IT301', 'Web Application Development', 3, 2, 5),
        (5, 'EC301', 'Digital Signal Processing', 4, 4, 5)
    ]
    cursor.executemany("INSERT INTO courses VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)", courses)

    # Classes
    classes = [
        (1, 1, 1, '2026-2027', 5, 'A', 'CS-Lab 301'),
        (2, 2, 2, '2026-2027', 3, 'A', 'LH-102'),
        (3, 3, 4, '2026-2027', 5, 'A', 'AI-Lab 201'),
        (4, 4, 3, '2026-2027', 5, 'A', 'IT-Lab 105'),
        (5, 5, 5, '2026-2027', 5, 'A', 'EC-LH 204')
    ]
    cursor.executemany("INSERT INTO classes VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)", classes)

    # Students
    students = [
        (1, '910023104001', 'Aarav Patel', 'aarav.patel@student.edu', '9123456780', 1, 3, 5, 'A', 'Male', '2004-05-12'),
        (2, '910023104002', 'Aditi Rao', 'aditi.rao@student.edu', '9123456781', 1, 3, 5, 'A', 'Female', '2004-08-22'),
        (3, '910023104003', 'Akash Nair', 'akash.nair@student.edu', '9123456782', 1, 3, 5, 'A', 'Male', '2003-11-04'),
        (4, '910023104004', 'Ananya Sharma', 'ananya.sharma@student.edu', '9123456783', 1, 3, 5, 'A', 'Female', '2004-01-19'),
        (5, '910023104005', 'Bhavya Menon', 'bhavya.menon@student.edu', '9123456784', 1, 3, 5, 'A', 'Female', '2004-07-30'),
        (6, '910023104006', 'Chetan Verma', 'chetan.verma@student.edu', '9123456785', 1, 3, 5, 'A', 'Male', '2003-09-14'),
        (7, '910023104007', 'Divya Krishnan', 'divya.krishnan@student.edu', '9123456786', 1, 3, 5, 'A', 'Female', '2004-03-25'),
        (8, '910023104008', 'Gaurav Joshi', 'gaurav.joshi@student.edu', '9123456787', 1, 3, 5, 'A', 'Male', '2004-06-18'),
        (9, '910023104009', 'Harini Balaji', 'harini.balaji@student.edu', '9123456788', 1, 3, 5, 'A', 'Female', '2004-12-05'),
        (10, '910023104010', 'Ishaan Gupta', 'ishaan.gupta@student.edu', '9123456789', 1, 3, 5, 'A', 'Male', '2004-04-09'),
        (11, '910023104011', 'Kavya Srinivasan', 'kavya.s@student.edu', '9123456790', 1, 3, 5, 'A', 'Female', '2004-02-14'),
        (12, '910023104012', 'Manoj Kumar', 'manoj.kumar@student.edu', '9123456791', 1, 3, 5, 'A', 'Male', '2003-10-27'),
        (13, '910023104013', 'Nandini Iyer', 'nandini.iyer@student.edu', '9123456792', 1, 3, 5, 'A', 'Female', '2004-09-08'),
        (14, '910023104014', 'Pranav Reddy', 'pranav.reddy@student.edu', '9123456793', 1, 3, 5, 'A', 'Male', '2004-05-03'),
        (15, '910023104015', 'Rhea Thomas', 'rhea.thomas@student.edu', '9123456794', 1, 3, 5, 'A', 'Female', '2004-10-11'),
        (16, '910023104016', 'Rohan Sengupta', 'rohan.s@student.edu', '9123456795', 1, 3, 5, 'A', 'Male', '2003-12-21'),
        (17, '910023104017', 'Sneha Pillai', 'sneha.pillai@student.edu', '9123456796', 1, 3, 5, 'A', 'Female', '2004-06-01'),
        (18, '910023104018', 'Tarun Bhat', 'tarun.bhat@student.edu', '9123456797', 1, 3, 5, 'A', 'Male', '2004-08-15'),
        (19, '910023104019', 'Varun Deshmukh', 'varun.d@student.edu', '9123456798', 1, 3, 5, 'A', 'Male', '2003-04-17'),
        (20, '910023104020', 'Zoya Khan', 'zoya.khan@student.edu', '9123456799', 1, 3, 5, 'A', 'Female', '2004-07-07'),
        (21, '910023205001', 'Arjun Nambiar', 'arjun.n@student.edu', '9123456800', 2, 3, 5, 'A', 'Male', '2004-03-12'),
        (22, '910023205002', 'Meera Venkatesh', 'meera.v@student.edu', '9123456801', 2, 3, 5, 'A', 'Female', '2004-09-28'),
        (23, '910023306001', 'Karthika Devi', 'karthika.d@student.edu', '9123456802', 3, 3, 5, 'A', 'Female', '2004-01-05'),
        (24, '910023306002', 'Siddharth Roy', 'siddharth.roy@student.edu', '9123456803', 3, 3, 5, 'A', 'Male', '2003-11-19'),
        (25, '910023407001', 'Vikramaditya Rao', 'vikram.rao@student.edu', '9123456804', 4, 3, 5, 'A', 'Male', '2004-04-29')
    ]
    cursor.executemany("INSERT INTO students VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)", students)

    # Exams
    exams = [
        (1, 'Internal Assessment 1 - DBMS', 'Internal Assessment 1', 1, 100.00, '2026-08-20'),
        (2, 'Internal Assessment 2 - DBMS', 'Internal Assessment 2', 1, 100.00, '2026-09-25'),
        (3, 'Model Examination - DBMS', 'Model Exam', 1, 100.00, '2026-10-30'),
        (4, 'Internal Assessment 1 - ML', 'Internal Assessment 1', 3, 100.00, '2026-08-22'),
        (5, 'Internal Assessment 1 - Web Tech', 'Internal Assessment 1', 4, 100.00, '2026-08-24')
    ]
    cursor.executemany("INSERT INTO exams VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)", exams)

    # Assignments
    assignments = [
        (1, 1, 'Assignment 1: ER Modeling & Relational Schema', 20.00, '2026-08-15'),
        (2, 1, 'Assignment 2: Complex SQL Queries & Triggers', 20.00, '2026-09-18'),
        (3, 3, 'Assignment 1: Regression Analysis with Python', 20.00, '2026-08-17')
    ]
    cursor.executemany("INSERT INTO assignments VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)", assignments)

    # Attendance records
    dates = ['2026-08-01', '2026-08-02', '2026-08-03', '2026-08-06', '2026-08-07', 
             '2026-08-08', '2026-08-09', '2026-08-10', '2026-08-13', '2026-08-14']
    
    # Presences map: student_id -> list of indices present (0 to 9)
    attendance_patterns = {
        1: [0,1,2,3,4,5,6,7,8,9], # 100%
        2: [0,1,2,3,4,5,6,7,8,9], # 100%
        3: [0,2,3,4,5,7,8,9],     # 80%
        4: [0,1,2,3,5,6,7,8,9],   # 90%
        5: [0,2,4,5,6,8,9],       # 70%
        6: [0,3,5,7,9],           # 50%
        7: [0,1,2,3,4,5,7,8,9],   # 90%
        8: [0,1,3,4,5,6,8,9],     # 80%
        9: [0,1,2,3,4,5,6,7,8,9], # 100%
        10: [0,1,2,4,5,6,7,9],    # 80%
        11: [0,1,2,3,4,5,6,7,8,9],# 100%
        12: [1,3,4,6,8,9],        # 60%
        13: [0,1,2,3,4,6,7,8,9],  # 90%
        14: [0,1,2,3,5,6,8,9],    # 80%
        15: [0,1,2,3,4,5,6,8,9],  # 90%
        16: [1,4,6,8,9],          # 50%
        17: [0,1,2,3,4,5,6,7,8,9],# 100%
        18: [0,2,3,5,6,7,9],      # 70%
        19: [2,5,8,9],            # 40%
        20: [0,1,2,3,4,5,7,8,9],  # 90%
    }
    
    att_rows = []
    for s_id, p_indices in attendance_patterns.items():
        for idx, d in enumerate(dates):
            status = 'Present' if idx in p_indices else 'Absent'
            remarks = 'On time' if status == 'Present' else 'Absent'
            att_rows.append((s_id, 1, d, status, remarks))

    # Add other depts
    att_rows.extend([
        (21, 4, '2026-08-01', 'Present', 'On time'), (21, 4, '2026-08-02', 'Present', 'On time'), (21, 4, '2026-08-03', 'Present', 'On time'),
        (22, 4, '2026-08-01', 'Present', 'On time'), (22, 4, '2026-08-02', 'Absent', 'Sick'), (22, 4, '2026-08-03', 'Present', 'On time'),
        (23, 3, '2026-08-01', 'Present', 'On time'), (23, 3, '2026-08-02', 'Present', 'On time'), (23, 3, '2026-08-03', 'Present', 'On time'),
        (24, 3, '2026-08-01', 'Present', 'On time'), (24, 3, '2026-08-02', 'Absent', 'Leave'), (24, 3, '2026-08-03', 'Absent', 'Absent'),
        (25, 5, '2026-08-01', 'Present', 'On time'), (25, 5, '2026-08-02', 'Present', 'On time'), (25, 5, '2026-08-03', 'Present', 'On time')
    ])

    cursor.executemany("INSERT INTO attendance (student_id, course_id, attendance_date, status, remarks) VALUES (?, ?, ?, ?, ?)", att_rows)

    # Helper function for grade
    def calc_grade(p):
        if p >= 90: return 'O'
        if p >= 80: return 'A+'
        if p >= 70: return 'A'
        if p >= 60: return 'B+'
        if p >= 50: return 'B'
        if p >= 40: return 'C'
        return 'F'

    # Performance rows: (student_id, course_id, exam_id, assignment_id, internal, assign, exam)
    perf_raw = [
        (1,  1, 1, 1, 28.5, 19.5, 48.0),
        (2,  1, 1, 1, 29.0, 20.0, 47.5),
        (3,  1, 1, 1, 22.0, 16.0, 36.0),
        (4,  1, 1, 1, 26.5, 18.5, 44.0),
        (5,  1, 1, 1, 20.5, 15.0, 33.5),
        (6,  1, 1, 1, 14.0, 11.0, 22.0),
        (7,  1, 1, 1, 27.0, 19.0, 45.0),
        (8,  1, 1, 1, 23.0, 16.5, 37.5),
        (9,  1, 1, 1, 28.0, 19.5, 46.5),
        (10, 1, 1, 1, 21.5, 15.5, 35.0),
        (11, 1, 1, 1, 27.5, 19.0, 47.0),
        (12, 1, 1, 1, 16.0, 12.5, 26.5),
        (13, 1, 1, 1, 25.0, 18.0, 43.0),
        (14, 1, 1, 1, 22.5, 16.0, 38.5),
        (15, 1, 1, 1, 26.0, 18.5, 42.5),
        (16, 1, 1, 1, 12.0, 10.0, 20.0),
        (17, 1, 1, 1, 29.5, 20.0, 48.5),
        (18, 1, 1, 1, 19.0, 14.5, 31.5),
        (19, 1, 1, 1,  9.5,  8.0, 16.0),
        (20, 1, 1, 1, 25.5, 18.0, 44.5),
        (21, 4, 5, 2, 26.0, 18.0, 42.0),
        (22, 4, 5, 2, 21.0, 15.0, 34.0),
        (23, 3, 4, 3, 27.0, 19.0, 46.0),
        (24, 3, 4, 3, 15.0, 12.0, 25.0),
        (25, 5, 3, 1, 24.0, 17.0, 39.0),
        # Exam 2 entries
        (1,  1, 2, 2, 29.0, 20.0, 49.0),
        (2,  1, 2, 2, 29.5, 20.0, 48.0),
        (3,  1, 2, 2, 23.5, 16.5, 38.0),
        (4,  1, 2, 2, 27.0, 19.0, 45.0),
        (5,  1, 2, 2, 21.0, 15.5, 34.0),
        (6,  1, 2, 2, 15.5, 12.0, 24.5),
        (19, 1, 2, 2, 11.0,  9.0, 18.0)
    ]

    perf_rows = []
    for s_id, c_id, e_id, a_id, i_m, a_m, e_m in perf_raw:
        tot = round(i_m + a_m + e_m, 2)
        pct = tot
        grd = calc_grade(pct)
        remarks = 'Excellent Academic Standing' if pct >= 85 else ('Needs Academic Improvement' if pct < 50 else 'Satisfactory Progress')
        perf_rows.append((s_id, c_id, e_id, a_id, i_m, a_m, e_m, tot, pct, grd, remarks))

    cursor.executemany("""
        INSERT INTO performances (student_id, course_id, exam_id, assignment_id, internal_marks, assignment_marks, exam_marks, total_marks, percentage, grade, remarks)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, perf_rows)

def check_backend_availability():
    """Detect if MySQL or SQLite should be the active database backend."""
    global _active_backend, _backend_info

    if Config.DB_MODE == 'MYSQL':
        try:
            conn = get_mysql_connection()
            conn.close()
            _active_backend = 'MYSQL'
            _backend_info = {
                'type': 'MySQL 8.0 Server',
                'host': f"{Config.DB_HOST}:{Config.DB_PORT}",
                'database': Config.DB_NAME,
                'status': 'Connected'
            }
            return
        except Exception as e:
            _backend_info = {'type': 'MySQL (Failed)', 'error': str(e)}
            raise e

    if Config.DB_MODE in ('AUTO', 'SQLITE'):
        # In AUTO mode, try MySQL first
        try:
            conn = get_mysql_connection()
            conn.close()
            _active_backend = 'MYSQL'
            _backend_info = {
                'type': 'MySQL 8.0 Server',
                'host': f"{Config.DB_HOST}:{Config.DB_PORT}",
                'database': Config.DB_NAME,
                'status': 'Active'
            }
            return
        except Exception as ex:
            # Fallback to SQLite mirror
            init_sqlite_mirror()
            _active_backend = 'SQLITE'
            _backend_info = {
                'type': 'SQLite3 (High-Fidelity Mirror / Standalone Engine)',
                'host': 'Local File Engine',
                'database': str(Config.SQLITE_PATH.name),
                'status': 'Active (Ready for Demo)',
                'mysql_note': f"MySQL Server status: {str(ex)}"
            }

def get_connection():
    """Get active database connection."""
    global _active_backend
    if _active_backend is None:
        check_backend_availability()

    if _active_backend == 'MYSQL':
        return get_mysql_connection()
    else:
        conn = sqlite3.connect(Config.SQLITE_PATH)
        conn.row_factory = sqlite3.Row
        return conn

def get_active_info():
    """Return backend status info dictionary."""
    global _backend_info
    if _active_backend is None:
        check_backend_availability()
    return _backend_info

def query_all(sql, params=None):
    """Execute query and fetch all rows as a list of dicts."""
    global _active_backend
    if _active_backend is None:
        check_backend_availability()

    params = params or ()
    conn = get_connection()
    try:
        if _active_backend == 'MYSQL':
            with conn.cursor() as cursor:
                cursor.execute(sql, params)
                return cursor.fetchall()
        else:
            # SQLite marker translation: %s -> ?
            translated_sql = re.sub(r'%s', '?', sql)
            cursor = conn.cursor()
            cursor.execute(translated_sql, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    finally:
        conn.close()

def query_one(sql, params=None):
    """Execute query and fetch a single row as a dict."""
    global _active_backend
    if _active_backend is None:
        check_backend_availability()

    params = params or ()
    conn = get_connection()
    try:
        if _active_backend == 'MYSQL':
            with conn.cursor() as cursor:
                cursor.execute(sql, params)
                return cursor.fetchone()
        else:
            translated_sql = re.sub(r'%s', '?', sql)
            cursor = conn.cursor()
            cursor.execute(translated_sql, params)
            row = cursor.fetchone()
            return dict(row) if row else None
    finally:
        conn.close()

def execute(sql, params=None):
    """Execute INSERT/UPDATE/DELETE query and return lastrowid / affected rows."""
    global _active_backend
    if _active_backend is None:
        check_backend_availability()

    params = params or ()
    conn = get_connection()
    try:
        if _active_backend == 'MYSQL':
            with conn.cursor() as cursor:
                cursor.execute(sql, params)
                last_id = cursor.lastrowid
                rowcount = cursor.rowcount
                return last_id if last_id else rowcount
        else:
            translated_sql = re.sub(r'%s', '?', sql)
            cursor = conn.cursor()
            cursor.execute(translated_sql, params)
            conn.commit()
            last_id = cursor.lastrowid
            rowcount = cursor.rowcount
            return last_id if last_id else rowcount
    finally:
        conn.close()

