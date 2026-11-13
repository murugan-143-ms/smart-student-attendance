-- ====================================================================
-- PROJECT: Smart Student Attendance and Performance Analytics System
-- DATABASE: MySQL 8.0+
-- COLLEGE: Third-Year Computer Science & Engineering Academic Project
-- AUTHOR: Antigravity Engineering Team
-- ====================================================================

DROP DATABASE IF EXISTS student_analytics_db;
CREATE DATABASE student_analytics_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE student_analytics_db;

-- ====================================================================
-- 1. DDL: TABLE DEFINITIONS & CONSTRAINTS
-- ====================================================================

-- Table 1: Department
CREATE TABLE departments (
    dept_id INT AUTO_INCREMENT PRIMARY KEY,
    dept_code VARCHAR(10) NOT NULL UNIQUE,
    dept_name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Table 2: Faculty
CREATE TABLE faculty (
    faculty_id INT AUTO_INCREMENT PRIMARY KEY,
    faculty_code VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    phone VARCHAR(20) NOT NULL,
    dept_id INT NOT NULL,
    designation VARCHAR(50) NOT NULL DEFAULT 'Assistant Professor',
    qualification VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_faculty_dept FOREIGN KEY (dept_id) 
        REFERENCES departments(dept_id) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

-- Table 3: Student
CREATE TABLE students (
    student_id INT AUTO_INCREMENT PRIMARY KEY,
    register_number VARCHAR(25) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    phone VARCHAR(20),
    dept_id INT NOT NULL,
    year INT NOT NULL CHECK (year BETWEEN 1 AND 4),
    semester INT NOT NULL CHECK (semester BETWEEN 1 AND 8),
    section VARCHAR(5) NOT NULL DEFAULT 'A',
    gender ENUM('Male', 'Female', 'Other') DEFAULT 'Male',
    dob DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_students_dept FOREIGN KEY (dept_id) 
        REFERENCES departments(dept_id) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

-- Table 4: Course
CREATE TABLE courses (
    course_id INT AUTO_INCREMENT PRIMARY KEY,
    course_code VARCHAR(20) NOT NULL UNIQUE,
    course_name VARCHAR(120) NOT NULL,
    credits INT NOT NULL CHECK (credits > 0),
    dept_id INT NOT NULL,
    semester INT NOT NULL CHECK (semester BETWEEN 1 AND 8),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_courses_dept FOREIGN KEY (dept_id) 
        REFERENCES departments(dept_id) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

-- Table 5: Class (Course - Faculty Allocation)
CREATE TABLE classes (
    class_id INT AUTO_INCREMENT PRIMARY KEY,
    course_id INT NOT NULL,
    faculty_id INT NOT NULL,
    academic_year VARCHAR(20) NOT NULL,
    semester INT NOT NULL CHECK (semester BETWEEN 1 AND 8),
    section VARCHAR(5) NOT NULL DEFAULT 'A',
    classroom VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_classes_course FOREIGN KEY (course_id) 
        REFERENCES courses(course_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_classes_faculty FOREIGN KEY (faculty_id) 
        REFERENCES faculty(faculty_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT uq_class_assignment UNIQUE (course_id, faculty_id, academic_year, semester, section)
) ENGINE=InnoDB;

-- Table 6: Attendance
CREATE TABLE attendance (
    attendance_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    course_id INT NOT NULL,
    attendance_date DATE NOT NULL,
    status ENUM('Present', 'Absent') NOT NULL DEFAULT 'Present',
    remarks VARCHAR(255),
    marked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_attendance_student FOREIGN KEY (student_id) 
        REFERENCES students(student_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_attendance_course FOREIGN KEY (course_id) 
        REFERENCES courses(course_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT uq_student_attendance UNIQUE (student_id, course_id, attendance_date)
) ENGINE=InnoDB;

-- Table 7: Exam
CREATE TABLE exams (
    exam_id INT AUTO_INCREMENT PRIMARY KEY,
    exam_name VARCHAR(100) NOT NULL,
    exam_type ENUM('Internal Assessment 1', 'Internal Assessment 2', 'Model Exam', 'Semester End Exam') NOT NULL,
    course_id INT NOT NULL,
    max_marks DECIMAL(5,2) NOT NULL DEFAULT 100.00 CHECK (max_marks > 0),
    exam_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_exams_course FOREIGN KEY (course_id) 
        REFERENCES courses(course_id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- Table 8: Assignment
CREATE TABLE assignments (
    assignment_id INT AUTO_INCREMENT PRIMARY KEY,
    course_id INT NOT NULL,
    title VARCHAR(150) NOT NULL,
    max_marks DECIMAL(5,2) NOT NULL DEFAULT 20.00 CHECK (max_marks > 0),
    due_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_assignments_course FOREIGN KEY (course_id) 
        REFERENCES courses(course_id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- Table 9: Performance (Marks, Grade, Calculations)
CREATE TABLE performances (
    performance_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    course_id INT NOT NULL,
    exam_id INT NOT NULL,
    assignment_id INT NULL,
    internal_marks DECIMAL(5,2) NOT NULL DEFAULT 0.00 CHECK (internal_marks >= 0 AND internal_marks <= 30),
    assignment_marks DECIMAL(5,2) NOT NULL DEFAULT 0.00 CHECK (assignment_marks >= 0 AND assignment_marks <= 20),
    exam_marks DECIMAL(5,2) NOT NULL DEFAULT 0.00 CHECK (exam_marks >= 0 AND exam_marks <= 50),
    total_marks DECIMAL(5,2) NOT NULL DEFAULT 0.00 CHECK (total_marks >= 0 AND total_marks <= 100),
    percentage DECIMAL(5,2) NOT NULL DEFAULT 0.00 CHECK (percentage >= 0 AND percentage <= 100),
    grade VARCHAR(5) NOT NULL DEFAULT 'F',
    remarks VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_performance_student FOREIGN KEY (student_id) 
        REFERENCES students(student_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_performance_course FOREIGN KEY (course_id) 
        REFERENCES courses(course_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_performance_exam FOREIGN KEY (exam_id) 
        REFERENCES exams(exam_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_performance_assignment FOREIGN KEY (assignment_id) 
        REFERENCES assignments(assignment_id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT uq_student_exam_perf UNIQUE (student_id, course_id, exam_id)
) ENGINE=InnoDB;

-- Table 10: Admin & User Authentication
CREATE TABLE admins (
    admin_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    role VARCHAR(30) NOT NULL DEFAULT 'Administrator',
    last_login DATETIME,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ====================================================================
-- 2. STORED FUNCTIONS
-- ====================================================================

DELIMITER $$

-- Function 1: Grade Calculation based on Marks Percentage
DROP FUNCTION IF EXISTS fn_get_letter_grade$$
CREATE FUNCTION fn_get_letter_grade(p_percentage DECIMAL(5,2))
RETURNS VARCHAR(5)
DETERMINISTIC
BEGIN
    DECLARE v_grade VARCHAR(5);
    IF p_percentage >= 90.0 THEN
        SET v_grade = 'O';    -- Outstanding (10.0 GPA)
    ELSEIF p_percentage >= 80.0 THEN
        SET v_grade = 'A+';   -- Excellent (9.0 GPA)
    ELSEIF p_percentage >= 70.0 THEN
        SET v_grade = 'A';    -- Very Good (8.0 GPA)
    ELSEIF p_percentage >= 60.0 THEN
        SET v_grade = 'B+';   -- Good (7.0 GPA)
    ELSEIF p_percentage >= 50.0 THEN
        SET v_grade = 'B';    -- Above Average (6.0 GPA)
    ELSEIF p_percentage >= 40.0 THEN
        SET v_grade = 'C';    -- Pass (5.0 GPA)
    ELSE
        SET v_grade = 'F';    -- Fail
    END IF;
    RETURN v_grade;
END$$

-- Function 2: Student Attendance Percentage for a Course
DROP FUNCTION IF EXISTS fn_calculate_attendance_pct$$
CREATE FUNCTION fn_calculate_attendance_pct(p_student_id INT, p_course_id INT)
RETURNS DECIMAL(5,2)
DETERMINISTIC
READS SQL DATA
BEGIN
    DECLARE total_sessions INT DEFAULT 0;
    DECLARE attended_sessions INT DEFAULT 0;
    DECLARE pct DECIMAL(5,2) DEFAULT 0.00;

    SELECT COUNT(*) INTO total_sessions
    FROM attendance
    WHERE student_id = p_student_id AND course_id = p_course_id;

    IF total_sessions > 0 THEN
        SELECT COUNT(*) INTO attended_sessions
        FROM attendance
        WHERE student_id = p_student_id 
          AND course_id = p_course_id 
          AND status = 'Present';

        SET pct = ROUND((attended_sessions / total_sessions) * 100.0, 2);
    ELSE
        SET pct = 0.00;
    END IF;

    RETURN pct;
END$$

DELIMITER ;

-- ====================================================================
-- 3. TRIGGERS
-- ====================================================================

DELIMITER $$

-- Trigger 1: Auto-Calculate Total Marks, Percentage, and Grade Before INSERT
DROP TRIGGER IF EXISTS trg_before_performance_insert$$
CREATE TRIGGER trg_before_performance_insert
BEFORE INSERT ON performances
FOR EACH ROW
BEGIN
    -- Sum components: Internal (0-30) + Assignment (0-20) + Exam (0-50) = Total (0-100)
    SET NEW.total_marks = NEW.internal_marks + NEW.assignment_marks + NEW.exam_marks;
    SET NEW.percentage = ROUND(NEW.total_marks, 2);
    SET NEW.grade = fn_get_letter_grade(NEW.percentage);
    
    IF NEW.percentage < 50.00 THEN
        SET NEW.remarks = 'Needs Academic Improvement';
    ELSEIF NEW.percentage >= 85.00 THEN
        SET NEW.remarks = 'Excellent Academic Standing';
    ELSE
        SET NEW.remarks = 'Satisfactory Progress';
    END IF;
END$$

-- Trigger 2: Auto-Recalculate Total Marks, Percentage, and Grade Before UPDATE
DROP TRIGGER IF EXISTS trg_before_performance_update$$
CREATE TRIGGER trg_before_performance_update
BEFORE UPDATE ON performances
FOR EACH ROW
BEGIN
    SET NEW.total_marks = NEW.internal_marks + NEW.assignment_marks + NEW.exam_marks;
    SET NEW.percentage = ROUND(NEW.total_marks, 2);
    SET NEW.grade = fn_get_letter_grade(NEW.percentage);
    
    IF NEW.percentage < 50.00 THEN
        SET NEW.remarks = 'Needs Academic Improvement';
    ELSEIF NEW.percentage >= 85.00 THEN
        SET NEW.remarks = 'Excellent Academic Standing';
    ELSE
        SET NEW.remarks = 'Satisfactory Progress';
    END IF;
END$$

DELIMITER ;

-- ====================================================================
-- 4. VIEWS FOR REPORTING & ANALYTICS
-- ====================================================================

-- View 1: Student Attendance Summary
CREATE OR REPLACE VIEW v_student_attendance_summary AS
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
            (SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) / NULLIF(COUNT(a.attendance_id), 0)) * 100, 
            0
        ), 2
    ) AS attendance_percentage,
    CASE 
        WHEN ROUND((SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) / NULLIF(COUNT(a.attendance_id), 0)) * 100, 2) >= 75.00 THEN 'Eligible'
        ELSE 'Detained / Low Attendance'
    END AS eligibility_status
FROM students s
JOIN departments d ON s.dept_id = d.dept_id
JOIN courses c ON c.dept_id = s.dept_id AND c.semester = s.semester
LEFT JOIN attendance a ON s.student_id = a.student_id AND c.course_id = a.course_id
GROUP BY s.student_id, s.register_number, s.name, d.dept_code, d.dept_name, s.year, s.semester, s.section, c.course_id, c.course_code, c.course_name;

-- View 2: Student Academic Performance Summary
CREATE OR REPLACE VIEW v_student_performance_summary AS
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

-- View 3: At-Risk Students View (Low Attendance < 75% OR Low Marks < 50%)
CREATE OR REPLACE VIEW v_at_risk_students AS
SELECT 
    s.student_id,
    s.register_number,
    s.name AS student_name,
    s.email,
    d.dept_code,
    s.year,
    COALESCE(att.overall_attendance, 0.00) AS overall_attendance_pct,
    COALESCE(perf.average_marks, 0.00) AS average_marks,
    CASE
        WHEN COALESCE(att.overall_attendance, 0.00) < 75.00 AND COALESCE(perf.average_marks, 0.00) < 50.00 THEN 'High Critical Risk'
        WHEN COALESCE(att.overall_attendance, 0.00) < 75.00 THEN 'Low Attendance Risk'
        WHEN COALESCE(perf.average_marks, 0.00) < 50.00 THEN 'Academic Failure Risk'
        ELSE 'Normal'
    END AS risk_category
FROM students s
JOIN departments d ON s.dept_id = d.dept_id
LEFT JOIN (
    SELECT 
        student_id,
        ROUND((SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) / COUNT(*)) * 100, 2) AS overall_attendance
    FROM attendance
    GROUP BY student_id
) att ON s.student_id = att.student_id
LEFT JOIN (
    SELECT 
        student_id,
        ROUND(AVG(total_marks), 2) AS average_marks
    FROM performances
    GROUP BY student_id
) perf ON s.student_id = perf.student_id
WHERE COALESCE(att.overall_attendance, 0) < 75.00 OR COALESCE(perf.average_marks, 0) < 50.00;

-- View 4: Consolidated Analytics Matrix (Attendance vs Performance)
CREATE OR REPLACE VIEW v_attendance_performance_matrix AS
SELECT 
    s.student_id,
    s.register_number,
    s.name AS student_name,
    d.dept_code,
    s.year,
    ROUND(COALESCE(att.attendance_pct, 0), 2) AS attendance_percentage,
    ROUND(COALESCE(perf.avg_marks, 0), 2) AS academic_percentage,
    fn_get_letter_grade(ROUND(COALESCE(perf.avg_marks, 0), 2)) AS overall_grade,
    CASE 
        WHEN COALESCE(att.attendance_pct, 0) >= 85 AND COALESCE(perf.avg_marks, 0) >= 80 THEN 'High Attendance & High Performer'
        WHEN COALESCE(att.attendance_pct, 0) >= 75 AND COALESCE(perf.avg_marks, 0) >= 60 THEN 'Regular & Consistent'
        WHEN COALESCE(att.attendance_pct, 0) < 75 AND COALESCE(perf.avg_marks, 0) < 60 THEN 'Low Attendance & Low Performer'
        ELSE 'Outlier / Needs Investigation'
    END AS correlation_cohort
FROM students s
JOIN departments d ON s.dept_id = d.dept_id
LEFT JOIN (
    SELECT student_id, (SUM(CASE WHEN status='Present' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) AS attendance_pct
    FROM attendance GROUP BY student_id
) att ON s.student_id = att.student_id
LEFT JOIN (
    SELECT student_id, AVG(total_marks) AS avg_marks
    FROM performances GROUP BY student_id
) perf ON s.student_id = perf.student_id;

-- ====================================================================
-- 5. STORED PROCEDURES (With Error Handlers & Cursor)
-- ====================================================================

DELIMITER $$

-- Procedure 1: Safe Record Attendance with Exception Handling
DROP PROCEDURE IF EXISTS sp_record_attendance$$
CREATE PROCEDURE sp_record_attendance(
    IN p_student_id INT,
    IN p_course_id INT,
    IN p_date DATE,
    IN p_status VARCHAR(10),
    IN p_remarks VARCHAR(255),
    OUT p_result VARCHAR(50)
)
BEGIN
    DECLARE duplicate_entry CONDITION FOR 1062;
    DECLARE EXIT HANDLER FOR duplicate_entry
    BEGIN
        -- Update attendance if already exists for date
        UPDATE attendance 
        SET status = p_status, remarks = p_remarks, marked_at = CURRENT_TIMESTAMP
        WHERE student_id = p_student_id AND course_id = p_course_id AND attendance_date = p_date;
        SET p_result = 'UPDATED_EXISTING';
    END;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET p_result = 'SQL_ERROR';
    END;

    INSERT INTO attendance (student_id, course_id, attendance_date, status, remarks)
    VALUES (p_student_id, p_course_id, p_date, p_status, p_remarks);

    SET p_result = 'RECORDED_SUCCESS';
END$$

-- Procedure 2: Cursor Procedure for Department Academic Audit
DROP PROCEDURE IF EXISTS sp_audit_department_performance$$
CREATE PROCEDURE sp_audit_department_performance(
    IN p_dept_id INT,
    OUT p_total_students INT,
    OUT p_avg_score DECIMAL(5,2),
    OUT p_detained_count INT
)
BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE v_student_id INT;
    DECLARE v_att_pct DECIMAL(5,2);
    DECLARE v_marks DECIMAL(5,2);

    -- Cursor definition
    DECLARE cur_student CURSOR FOR 
        SELECT s.student_id, 
               COALESCE(att.pct, 0),
               COALESCE(perf.avg_score, 0)
        FROM students s
        LEFT JOIN (
            SELECT student_id, ROUND(SUM(CASE WHEN status='Present' THEN 1 ELSE 0 END)*100.0/COUNT(*),2) AS pct
            FROM attendance GROUP BY student_id
        ) att ON s.student_id = att.student_id
        LEFT JOIN (
            SELECT student_id, ROUND(AVG(total_marks),2) AS avg_score
            FROM performances GROUP BY student_id
        ) perf ON s.student_id = perf.student_id
        WHERE s.dept_id = p_dept_id;

    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

    SET p_total_students = 0;
    SET p_detained_count = 0;

    OPEN cur_student;

    read_loop: LOOP
        FETCH cur_student INTO v_student_id, v_att_pct, v_marks;
        IF done THEN
            LEAVE read_loop;
        END IF;

        SET p_total_students = p_total_students + 1;
        IF v_att_pct < 75.00 THEN
            SET p_detained_count = p_detained_count + 1;
        END IF;
    END LOOP;

    CLOSE cur_student;

    SELECT ROUND(COALESCE(AVG(p.total_marks), 0), 2) INTO p_avg_score
    FROM performances p
    JOIN students s ON p.student_id = s.student_id
    WHERE s.dept_id = p_dept_id;

END$$

DELIMITER ;

-- ====================================================================
-- 6. SAMPLE DATA INSERTION (Realistic Academic Dataset)
-- ====================================================================

-- Default Admin: username 'admin', password 'admin123' (werkzeug pbkdf2 hash)
INSERT INTO admins (username, password_hash, full_name, email, role) VALUES 
('admin', 'scrypt:32768:8:1$7W3q9QZ1fJk0mN6a$78e9fa0c71a39da5b34bc7038e24c27894a4da092305a4e32628045610ec1fbf523c9ce05500efee6ae9b5e510842db7d057a70a8d4a9f939e658ec3ef258979', 'System Administrator', 'admin@college.edu', 'Super Admin');

-- Departments
INSERT INTO departments (dept_id, dept_code, dept_name, description) VALUES
(1, 'CSE', 'Computer Science and Engineering', 'Department of Computer Science & Engineering'),
(2, 'IT', 'Information Technology', 'Department of Information Technology'),
(3, 'AIDS', 'Artificial Intelligence & Data Science', 'Department of AI & Data Science'),
(4, 'ECE', 'Electronics & Communication Engineering', 'Department of Electronics & Communication');

-- Faculty
INSERT INTO faculty (faculty_id, faculty_code, name, email, phone, dept_id, designation, qualification) VALUES
(1, 'FAC001', 'Dr. Rajesh Sharma', 'rajesh.sharma@college.edu', '9840112345', 1, 'Professor & HOD', 'Ph.D., M.E.'),
(2, 'FAC002', 'Prof. Priya Sundaram', 'priya.sundaram@college.edu', '9840223456', 1, 'Associate Professor', 'M.Tech, (Ph.D)'),
(3, 'FAC003', 'Dr. Anand Kumar', 'anand.kumar@college.edu', '9840334567', 2, 'Professor', 'Ph.D, M.S.'),
(4, 'FAC004', 'Prof. Deepa Varghese', 'deepa.varghese@college.edu', '9840445678', 3, 'Assistant Professor', 'M.Tech'),
(5, 'FAC005', 'Dr. Karthik Raman', 'karthik.raman@college.edu', '9840556789', 4, 'Associate Professor', 'Ph.D');

-- Courses
INSERT INTO courses (course_id, course_code, course_name, credits, dept_id, semester) VALUES
(1, 'CS301', 'Database Management Systems', 4, 1, 5),
(2, 'CS302', 'Data Structures & Algorithms', 4, 1, 3),
(3, 'AI301', 'Machine Learning Foundations', 4, 3, 5),
(4, 'IT301', 'Web Application Development', 3, 2, 5),
(5, 'EC301', 'Digital Signal Processing', 4, 4, 5);

-- Classes
INSERT INTO classes (class_id, course_id, faculty_id, academic_year, semester, section, classroom) VALUES
(1, 1, 1, '2026-2027', 5, 'A', 'CS-Lab 301'),
(2, 2, 2, '2026-2027', 3, 'A', 'LH-102'),
(3, 3, 4, '2026-2027', 5, 'A', 'AI-Lab 201'),
(4, 4, 3, '2026-2027', 5, 'A', 'IT-Lab 105'),
(5, 5, 5, '2026-2027', 5, 'A', 'EC-LH 204');

-- Students (25 Sample Students across departments)
INSERT INTO students (student_id, register_number, name, email, phone, dept_id, year, semester, section, gender, dob) VALUES
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
(25, '910023407001', 'Vikramaditya Rao', 'vikram.rao@student.edu', '9123456804', 4, 3, 5, 'A', 'Male', '2004-04-29');

-- Exams
INSERT INTO exams (exam_id, exam_name, exam_type, course_id, max_marks, exam_date) VALUES
(1, 'Internal Assessment 1 - DBMS', 'Internal Assessment 1', 1, 100.00, '2026-08-20'),
(2, 'Internal Assessment 2 - DBMS', 'Internal Assessment 2', 1, 100.00, '2026-09-25'),
(3, 'Model Examination - DBMS', 'Model Exam', 1, 100.00, '2026-10-30'),
(4, 'Internal Assessment 1 - ML', 'Internal Assessment 1', 3, 100.00, '2026-08-22'),
(5, 'Internal Assessment 1 - Web Tech', 'Internal Assessment 1', 4, 100.00, '2026-08-24');

-- Assignments
INSERT INTO assignments (assignment_id, course_id, title, max_marks, due_date) VALUES
(1, 1, 'Assignment 1: ER Modeling & Relational Schema', 20.00, '2026-08-15'),
(2, 1, 'Assignment 2: Complex SQL Queries & Triggers', 20.00, '2026-09-18'),
(3, 3, 'Assignment 1: Regression Analysis with Python', 20.00, '2026-08-17');

-- Attendance Records (Multi-date realistic distribution for Course 1: DBMS)
-- Dates: 2026-08-01 through 2026-08-14 (10 academic sessions)
-- High attendance students: 1, 2, 4, 7, 9, 11, 13, 15, 17, 20 (90-100%)
-- Average attendance students: 3, 5, 8, 10, 14, 18 (70-80%)
-- Low attendance students: 6, 12, 16, 19 (<70%)

INSERT INTO attendance (student_id, course_id, attendance_date, status, remarks) VALUES
-- Student 1: Aarav Patel (10/10 = 100%)
(1, 1, '2026-08-01', 'Present', 'On time'), (1, 1, '2026-08-02', 'Present', 'On time'),
(1, 1, '2026-08-03', 'Present', 'On time'), (1, 1, '2026-08-06', 'Present', 'Active in class'),
(1, 1, '2026-08-07', 'Present', 'On time'), (1, 1, '2026-08-08', 'Present', 'On time'),
(1, 1, '2026-08-09', 'Present', 'On time'), (1, 1, '2026-08-10', 'Present', 'On time'),
(1, 1, '2026-08-13', 'Present', 'On time'), (1, 1, '2026-08-14', 'Present', 'On time'),

-- Student 2: Aditi Rao (10/10 = 100%)
(2, 1, '2026-08-01', 'Present', 'On time'), (2, 1, '2026-08-02', 'Present', 'On time'),
(2, 1, '2026-08-03', 'Present', 'On time'), (2, 1, '2026-08-06', 'Present', 'On time'),
(2, 1, '2026-08-07', 'Present', 'On time'), (2, 1, '2026-08-08', 'Present', 'On time'),
(2, 1, '2026-08-09', 'Present', 'On time'), (2, 1, '2026-08-10', 'Present', 'On time'),
(2, 1, '2026-08-13', 'Present', 'On time'), (2, 1, '2026-08-14', 'Present', 'On time'),

-- Student 3: Akash Nair (8/10 = 80%)
(3, 1, '2026-08-01', 'Present', 'On time'), (3, 1, '2026-08-02', 'Absent', 'Medical leave'),
(3, 1, '2026-08-03', 'Present', 'On time'), (3, 1, '2026-08-06', 'Present', 'On time'),
(3, 1, '2026-08-07', 'Present', 'On time'), (3, 1, '2026-08-08', 'Present', 'On time'),
(3, 1, '2026-08-09', 'Absent', 'Personal reason'), (3, 1, '2026-08-10', 'Present', 'On time'),
(3, 1, '2026-08-13', 'Present', 'On time'), (3, 1, '2026-08-14', 'Present', 'On time'),

-- Student 4: Ananya Sharma (9/10 = 90%)
(4, 1, '2026-08-01', 'Present', 'On time'), (4, 1, '2026-08-02', 'Present', 'On time'),
(4, 1, '2026-08-03', 'Present', 'On time'), (4, 1, '2026-08-06', 'Present', 'On time'),
(4, 1, '2026-08-07', 'Absent', 'Permission'), (4, 1, '2026-08-08', 'Present', 'On time'),
(4, 1, '2026-08-09', 'Present', 'On time'), (4, 1, '2026-08-10', 'Present', 'On time'),
(4, 1, '2026-08-13', 'Present', 'On time'), (4, 1, '2026-08-14', 'Present', 'On time'),

-- Student 5: Bhavya Menon (7/10 = 70% - Critical Borderline)
(5, 1, '2026-08-01', 'Present', 'On time'), (5, 1, '2026-08-02', 'Absent', 'Uninformed'),
(5, 1, '2026-08-03', 'Present', 'On time'), (5, 1, '2026-08-06', 'Absent', 'Sick'),
(5, 1, '2026-08-07', 'Present', 'On time'), (5, 1, '2026-08-08', 'Present', 'On time'),
(5, 1, '2026-08-09', 'Present', 'On time'), (5, 1, '2026-08-10', 'Absent', 'Uninformed'),
(5, 1, '2026-08-13', 'Present', 'On time'), (5, 1, '2026-08-14', 'Present', 'On time'),

-- Student 6: Chetan Verma (5/10 = 50% - Low Attendance)
(6, 1, '2026-08-01', 'Present', 'Late'), (6, 1, '2026-08-02', 'Absent', 'Absent'),
(6, 1, '2026-08-03', 'Absent', 'Absent'), (6, 1, '2026-08-06', 'Present', 'On time'),
(6, 1, '2026-08-07', 'Absent', 'Absent'), (6, 1, '2026-08-08', 'Present', 'On time'),
(6, 1, '2026-08-09', 'Absent', 'Absent'), (6, 1, '2026-08-10', 'Present', 'On time'),
(6, 1, '2026-08-13', 'Absent', 'Absent'), (6, 1, '2026-08-14', 'Present', 'On time'),

-- Student 7: Divya Krishnan (9/10 = 90%)
(7, 1, '2026-08-01', 'Present', 'On time'), (7, 1, '2026-08-02', 'Present', 'On time'),
(7, 1, '2026-08-03', 'Present', 'On time'), (7, 1, '2026-08-06', 'Present', 'On time'),
(7, 1, '2026-08-07', 'Present', 'On time'), (7, 1, '2026-08-08', 'Present', 'On time'),
(7, 1, '2026-08-09', 'Absent', 'Leave'), (7, 1, '2026-08-10', 'Present', 'On time'),
(7, 1, '2026-08-13', 'Present', 'On time'), (7, 1, '2026-08-14', 'Present', 'On time'),

-- Student 8: Gaurav Joshi (8/10 = 80%)
(8, 1, '2026-08-01', 'Present', 'On time'), (8, 1, '2026-08-02', 'Present', 'On time'),
(8, 1, '2026-08-03', 'Absent', 'Leave'), (8, 1, '2026-08-06', 'Present', 'On time'),
(8, 1, '2026-08-07', 'Present', 'On time'), (8, 1, '2026-08-08', 'Present', 'On time'),
(8, 1, '2026-08-09', 'Present', 'On time'), (8, 1, '2026-08-10', 'Absent', 'Leave'),
(8, 1, '2026-08-13', 'Present', 'On time'), (8, 1, '2026-08-14', 'Present', 'On time'),

-- Student 9: Harini Balaji (10/10 = 100%)
(9, 1, '2026-08-01', 'Present', 'On time'), (9, 1, '2026-08-02', 'Present', 'On time'),
(9, 1, '2026-08-03', 'Present', 'On time'), (9, 1, '2026-08-06', 'Present', 'On time'),
(9, 1, '2026-08-07', 'Present', 'On time'), (9, 1, '2026-08-08', 'Present', 'On time'),
(9, 1, '2026-08-09', 'Present', 'On time'), (9, 1, '2026-08-10', 'Present', 'On time'),
(9, 1, '2026-08-13', 'Present', 'On time'), (9, 1, '2026-08-14', 'Present', 'On time'),

-- Student 10: Ishaan Gupta (8/10 = 80%)
(10, 1, '2026-08-01', 'Present', 'On time'), (10, 1, '2026-08-02', 'Present', 'On time'),
(10, 1, '2026-08-03', 'Present', 'On time'), (10, 1, '2026-08-06', 'Absent', 'Sick'),
(10, 1, '2026-08-07', 'Present', 'On time'), (10, 1, '2026-08-08', 'Present', 'On time'),
(10, 1, '2026-08-09', 'Present', 'On time'), (10, 1, '2026-08-10', 'Present', 'On time'),
(10, 1, '2026-08-13', 'Absent', 'Leave'), (10, 1, '2026-08-14', 'Present', 'On time'),

-- Student 11: Kavya Srinivasan (10/10 = 100%)
(11, 1, '2026-08-01', 'Present', 'On time'), (11, 1, '2026-08-02', 'Present', 'On time'),
(11, 1, '2026-08-03', 'Present', 'On time'), (11, 1, '2026-08-06', 'Present', 'On time'),
(11, 1, '2026-08-07', 'Present', 'On time'), (11, 1, '2026-08-08', 'Present', 'On time'),
(11, 1, '2026-08-09', 'Present', 'On time'), (11, 1, '2026-08-10', 'Present', 'On time'),
(11, 1, '2026-08-13', 'Present', 'On time'), (11, 1, '2026-08-14', 'Present', 'On time'),

-- Student 12: Manoj Kumar (6/10 = 60% - Low Attendance)
(12, 1, '2026-08-01', 'Absent', 'Absent'), (12, 1, '2026-08-02', 'Present', 'On time'),
(12, 1, '2026-08-03', 'Absent', 'Absent'), (12, 1, '2026-08-06', 'Present', 'On time'),
(12, 1, '2026-08-07', 'Present', 'On time'), (12, 1, '2026-08-08', 'Absent', 'Absent'),
(12, 1, '2026-08-09', 'Present', 'On time'), (12, 1, '2026-08-10', 'Absent', 'Absent'),
(12, 1, '2026-08-13', 'Present', 'On time'), (12, 1, '2026-08-14', 'Present', 'On time'),

-- Student 13: Nandini Iyer (9/10 = 90%)
(13, 1, '2026-08-01', 'Present', 'On time'), (13, 1, '2026-08-02', 'Present', 'On time'),
(13, 1, '2026-08-03', 'Present', 'On time'), (13, 1, '2026-08-06', 'Present', 'On time'),
(13, 1, '2026-08-07', 'Present', 'On time'), (13, 1, '2026-08-08', 'Absent', 'Leave'),
(13, 1, '2026-08-09', 'Present', 'On time'), (13, 1, '2026-08-10', 'Present', 'On time'),
(13, 1, '2026-08-13', 'Present', 'On time'), (13, 1, '2026-08-14', 'Present', 'On time'),

-- Student 14: Pranav Reddy (8/10 = 80%)
(14, 1, '2026-08-01', 'Present', 'On time'), (14, 1, '2026-08-02', 'Present', 'On time'),
(14, 1, '2026-08-03', 'Present', 'On time'), (14, 1, '2026-08-06', 'Present', 'On time'),
(14, 1, '2026-08-07', 'Absent', 'Sick'), (14, 1, '2026-08-08', 'Present', 'On time'),
(14, 1, '2026-08-09', 'Present', 'On time'), (14, 1, '2026-08-10', 'Absent', 'Personal'),
(14, 1, '2026-08-13', 'Present', 'On time'), (14, 1, '2026-08-14', 'Present', 'On time'),

-- Student 15: Rhea Thomas (9/10 = 90%)
(15, 1, '2026-08-01', 'Present', 'On time'), (15, 1, '2026-08-02', 'Present', 'On time'),
(15, 1, '2026-08-03', 'Present', 'On time'), (15, 1, '2026-08-06', 'Present', 'On time'),
(15, 1, '2026-08-07', 'Present', 'On time'), (15, 1, '2026-08-08', 'Present', 'On time'),
(15, 1, '2026-08-09', 'Present', 'On time'), (15, 1, '2026-08-10', 'Absent', 'Sports'),
(15, 1, '2026-08-13', 'Present', 'On time'), (15, 1, '2026-08-14', 'Present', 'On time'),

-- Student 16: Rohan Sengupta (5/10 = 50% - Low Attendance)
(16, 1, '2026-08-01', 'Absent', 'Absent'), (16, 1, '2026-08-02', 'Present', 'On time'),
(16, 1, '2026-08-03', 'Absent', 'Absent'), (16, 1, '2026-08-06', 'Absent', 'Absent'),
(16, 1, '2026-08-07', 'Present', 'On time'), (16, 1, '2026-08-08', 'Absent', 'Absent'),
(16, 1, '2026-08-09', 'Present', 'On time'), (16, 1, '2026-08-10', 'Absent', 'Absent'),
(16, 1, '2026-08-13', 'Present', 'On time'), (16, 1, '2026-08-14', 'Present', 'On time'),

-- Student 17: Sneha Pillai (10/10 = 100%)
(17, 1, '2026-08-01', 'Present', 'On time'), (17, 1, '2026-08-02', 'Present', 'On time'),
(17, 1, '2026-08-03', 'Present', 'On time'), (17, 1, '2026-08-06', 'Present', 'On time'),
(17, 1, '2026-08-07', 'Present', 'On time'), (17, 1, '2026-08-08', 'Present', 'On time'),
(17, 1, '2026-08-09', 'Present', 'On time'), (17, 1, '2026-08-10', 'Present', 'On time'),
(17, 1, '2026-08-13', 'Present', 'On time'), (17, 1, '2026-08-14', 'Present', 'On time'),

-- Student 18: Tarun Bhat (7/10 = 70%)
(18, 1, '2026-08-01', 'Present', 'On time'), (18, 1, '2026-08-02', 'Absent', 'Sick'),
(18, 1, '2026-08-03', 'Present', 'On time'), (18, 1, '2026-08-06', 'Present', 'On time'),
(18, 1, '2026-08-07', 'Absent', 'Absent'), (18, 1, '2026-08-08', 'Present', 'On time'),
(18, 1, '2026-08-09', 'Present', 'On time'), (18, 1, '2026-08-10', 'Present', 'On time'),
(18, 1, '2026-08-13', 'Absent', 'Absent'), (18, 1, '2026-08-14', 'Present', 'On time'),

-- Student 19: Varun Deshmukh (4/10 = 40% - Severe Low Attendance)
(19, 1, '2026-08-01', 'Absent', 'Absent'), (19, 1, '2026-08-02', 'Absent', 'Absent'),
(19, 1, '2026-08-03', 'Present', 'On time'), (19, 1, '2026-08-06', 'Absent', 'Absent'),
(19, 1, '2026-08-07', 'Absent', 'Absent'), (19, 1, '2026-08-08', 'Present', 'On time'),
(19, 1, '2026-08-09', 'Absent', 'Absent'), (19, 1, '2026-08-10', 'Absent', 'Absent'),
(19, 1, '2026-08-13', 'Present', 'On time'), (19, 1, '2026-08-14', 'Present', 'On time'),

-- Student 20: Zoya Khan (9/10 = 90%)
(20, 1, '2026-08-01', 'Present', 'On time'), (20, 1, '2026-08-02', 'Present', 'On time'),
(20, 1, '2026-08-03', 'Present', 'On time'), (20, 1, '2026-08-06', 'Present', 'On time'),
(20, 1, '2026-08-07', 'Present', 'On time'), (20, 1, '2026-08-08', 'Present', 'On time'),
(20, 1, '2026-08-09', 'Absent', 'Personal'), (20, 1, '2026-08-10', 'Present', 'On time'),
(20, 1, '2026-08-13', 'Present', 'On time'), (20, 1, '2026-08-14', 'Present', 'On time');

-- Also add sample attendance for IT, AIDS and ECE students
INSERT INTO attendance (student_id, course_id, attendance_date, status, remarks) VALUES
(21, 4, '2026-08-01', 'Present', 'On time'), (21, 4, '2026-08-02', 'Present', 'On time'), (21, 4, '2026-08-03', 'Present', 'On time'),
(22, 4, '2026-08-01', 'Present', 'On time'), (22, 4, '2026-08-02', 'Absent', 'Sick'), (22, 4, '2026-08-03', 'Present', 'On time'),
(23, 3, '2026-08-01', 'Present', 'On time'), (23, 3, '2026-08-02', 'Present', 'On time'), (23, 3, '2026-08-03', 'Present', 'On time'),
(24, 3, '2026-08-01', 'Present', 'On time'), (24, 3, '2026-08-02', 'Absent', 'Leave'), (24, 3, '2026-08-03', 'Absent', 'Absent'),
(25, 5, '2026-08-01', 'Present', 'On time'), (25, 5, '2026-08-02', 'Present', 'On time'), (25, 5, '2026-08-03', 'Present', 'On time');

-- Performance Records for Course 1 (DBMS) - Exam 1 (IA-1)
-- Note: Trigger will auto-compute total_marks, percentage, and grade!
-- Notice how students with 90-100% attendance (1, 2, 4, 7, 9, 11, 17) score high (85-98)
-- Average attendance students score 65-80
-- Low attendance students (6, 12, 16, 19) score low (30-55)
-- This provides a rich, realistic correlation dataset for Pandas & NumPy analysis!

INSERT INTO performances (student_id, course_id, exam_id, assignment_id, internal_marks, assignment_marks, exam_marks) VALUES
-- High Performers (High Attendance)
(1,  1, 1, 1, 28.50, 19.50, 48.00), -- Total: 96.00 (O)
(2,  1, 1, 1, 29.00, 20.00, 47.50), -- Total: 96.50 (O)
(4,  1, 1, 1, 26.50, 18.50, 44.00), -- Total: 89.00 (A+)
(7,  1, 1, 1, 27.00, 19.00, 45.00), -- Total: 91.00 (O)
(9,  1, 1, 1, 28.00, 19.50, 46.50), -- Total: 94.00 (O)
(11, 1, 1, 1, 27.50, 19.00, 47.00), -- Total: 93.50 (O)
(13, 1, 1, 1, 25.00, 18.00, 43.00), -- Total: 86.00 (A+)
(15, 1, 1, 1, 26.00, 18.50, 42.50), -- Total: 87.00 (A+)
(17, 1, 1, 1, 29.50, 20.00, 48.50), -- Total: 98.00 (O)
(20, 1, 1, 1, 25.50, 18.00, 44.50), -- Total: 88.00 (A+)

-- Moderate Performers (Moderate Attendance)
(3,  1, 1, 1, 22.00, 16.00, 36.00), -- Total: 74.00 (A)
(5,  1, 1, 1, 20.50, 15.00, 33.50), -- Total: 69.00 (B+)
(8,  1, 1, 1, 23.00, 16.50, 37.50), -- Total: 77.00 (A)
(10, 1, 1, 1, 21.50, 15.50, 35.00), -- Total: 72.00 (A)
(14, 1, 1, 1, 22.50, 16.00, 38.50), -- Total: 77.00 (A)
(18, 1, 1, 1, 19.00, 14.50, 31.50), -- Total: 65.00 (B+)

-- Low Performers (Low Attendance)
(6,  1, 1, 1, 14.00, 11.00, 22.00), -- Total: 47.00 (C)
(12, 1, 1, 1, 16.00, 12.50, 26.50), -- Total: 55.00 (B)
(16, 1, 1, 1, 12.00, 10.00, 20.00), -- Total: 42.00 (C)
(19, 1, 1, 1,  9.50,  8.00, 16.00), -- Total: 33.50 (F - Fail)

-- Other Departments
(21, 4, 5, 2, 26.00, 18.00, 42.00), -- Total: 86.00 (A+)
(22, 4, 5, 2, 21.00, 15.00, 34.00), -- Total: 70.00 (A)
(23, 3, 4, 3, 27.00, 19.00, 46.00), -- Total: 92.00 (O)
(24, 3, 4, 3, 15.00, 12.00, 25.00), -- Total: 52.00 (B)
(25, 5, 3, 1, 24.00, 17.00, 39.00); -- Total: 80.00 (A+)

-- Also add Exam 2 (IA-2) sample data for DBMS to show longitudinal progress
INSERT INTO performances (student_id, course_id, exam_id, assignment_id, internal_marks, assignment_marks, exam_marks) VALUES
(1,  1, 2, 2, 29.00, 20.00, 49.00),
(2,  1, 2, 2, 29.50, 20.00, 48.00),
(3,  1, 2, 2, 23.50, 16.50, 38.00),
(4,  1, 2, 2, 27.00, 19.00, 45.00),
(5,  1, 2, 2, 21.00, 15.50, 34.00),
(6,  1, 2, 2, 15.50, 12.00, 24.50),
(19, 1, 2, 2, 11.00,  9.00, 18.00);

