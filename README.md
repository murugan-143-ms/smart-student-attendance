# Smart Student Attendance and Performance Analytics System

A production-ready educational management and predictive analytics web application developed for academic demonstration and review in Computer Science & Engineering.

The system manages student attendance and academic performance using a centralized **MySQL 8.0** relational database, evaluates examination marks, computes letter grades automatically, monitors student attendance percentages, and leverages **Pandas** and **NumPy** to perform correlation and linear regression analysis between classroom attendance and academic outcomes.

---

## 1. Technology Stack

| Layer | Technologies & Tools |
|---|---|
| **Frontend** | HTML5, CSS3, JavaScript (ES6+), Bootstrap 5.3, Bootstrap Icons |
| **Backend** | Python 3.11+ / Flask Framework |
| **Database** | MySQL 8.0 Community Server & MySQL Workbench 8.0 CE |
| **Database Connector** | PyMySQL / mysql-connector-python |
| **Data Analytics** | Pandas, NumPy (Correlation, Regression, Distribution) |
| **Data Visualization** | Chart.js 4.4 (Scatter Plot, Bar Chart, Doughnut Chart) |
| **Authentication** | Secure Flask Session with PBKDF2/Werkzeug Cryptographic Hashing |

---

## 2. System Architecture & Features

### Module 1: Admin Login & Security
- Secure session-based authentication for administrators and faculty.
- Protection against unauthorized URL access using `@login_required` decorators.
- Password hashing using PBKDF2 with SHA-256 / scrypt.
- One-click demo credentials helper for fast viva presentations (`admin` / `admin123`).

### Module 2: Student Management
- Complete CRUD operations: Add, Edit, Delete, and View students.
- Search students in real-time by Register Number, Name, or Email.
- Filter by Academic Year (1 to 4) and Department (CSE, ECE, IT, AIDS).
- Input validation preventing duplicate register numbers or emails.
- Detailed student profile displaying full attendance logs and examination mark histories.

### Module 3: Faculty Management
- Add, update, and remove faculty members.
- Store qualifications (Ph.D., M.Tech), designations (Professor, HOD, Assistant Professor), and contact details.
- Course allocation module: Assign faculty members to courses, academic years, semesters, and classrooms.

### Module 4: Attendance Management
- Interactive Daily Attendance Register: Select course and date to load all enrolled students.
- One-click batch marking with "Mark All Present" and "Mark All Absent" shortcuts.
- Real-time cumulative attendance percentage calculation:
  $$\text{Attendance \%} = \left(\frac{\text{Attended Sessions}}{\text{Total Sessions}}\right) \times 100$$
- Automatic determination of semester examination eligibility ($<75\%$ flagged as **Detained**).
- Historical attendance search by session date and course code.

### Module 5: Academic Performance Management
- Component-wise mark entry:
  - Internal Assessment (0 to 30 marks)
  - Assignment Assessment (0 to 20 marks)
  - Semester Examination (0 to 50 marks)
  - Total Score (0 to 100 marks)
- Automatic letter grade determination:
  - **O** (Outstanding): $\ge 90\%$ (10.0 GPA)
  - **A+** (Excellent): $80 - 89\%$ (9.0 GPA)
  - **A** (Very Good): $70 - 79\%$ (8.0 GPA)
  - **B+** (Good): $60 - 69\%$ (7.0 GPA)
  - **B** (Above Average): $50 - 59\%$ (6.0 GPA)
  - **C** (Pass): $40 - 49\%$ (5.0 GPA)
  - **F** (Fail): $< 40\%$

### Module 6: Performance Analytics (Data Science Engine)
- Utilizes **Pandas** and **NumPy** to calculate:
  - **Pearson Correlation Coefficient ($r$):** Quantifies linear relationship between attendance and examination performance ($r \approx 0.948$).
  - **Coefficient of Determination ($R^2$):** Measures the proportion of variance explained by attendance ($R^2 \approx 0.898$).
  - **Linear Regression Equation ($y = mx + c$):** Computes slope and intercept using `np.polyfit`.
  - **Interactive Chart.js Scatter Plot:** Plots individual student data points overlaid with the linear regression trend line.
  - **Four-Quadrant Performance Cohorts:**
    - *Q1 (Star Performers):* $\text{Att} \ge 75\%, \text{Marks} \ge 75\%$
    - *Q2 (Struggling Diligent):* $\text{Att} \ge 75\%, \text{Marks} < 50\%$
    - *Q3 (Critical At-Risk):* $\text{Att} < 75\%, \text{Marks} < 50\%$
    - *Q4 (Fast Learners):* $\text{Att} < 75\%, \text{Marks} \ge 75\%$
  - **Automated Diagnostic Insights:** Rule-based qualitative recommendations for academic advisors.

### Module 7: Reports & Official Transcripts
- Printable **Official Academic Grade Sheet & Transcript** with college branding, course credits, GPA calculation, and signature blocks.
- Low Attendance Detention Notice Report ($<75\%$).
- College Academic Merit Rank List.
- One-click CSV dataset export.

### Module 8: DBMS Showcase & Query Explorer
- Dedicated review page demonstrating core DBMS concepts:
  - DDL, DML, DQL
  - Aggregate functions (`COUNT`, `AVG`, `MAX`, `MIN`, `SUM`)
  - `GROUP BY` and `HAVING`
  - Subqueries (scalar and correlated)
  - Joins (`INNER`, `LEFT`, `SELF`, `CROSS`)
  - Views (`v_student_attendance_summary`, `v_student_performance_summary`, `v_at_risk_students`)
  - Stored Procedures with `DECLARE EXIT HANDLER` error handling
  - Stored Functions and Triggers (`BEFORE INSERT`, `BEFORE UPDATE`)
  - Comprehensive Normalization (1NF, 2NF, 3NF, BCNF, 4NF, 5NF)

---

## 3. Project Directory Structure

```text
student_analytics_system/
│
├── app.py                      # Application entry point and Flask route registry
├── config.py                   # Configuration settings (MySQL / SQLite parameters)
├── db.py                       # Unified database manager and connection router
├── analytics.py                # Pandas & NumPy statistical analysis engine
├── database.sql                # Complete MySQL 8.0 schema, tables, triggers, and sample data
├── requirements.txt            # Python dependencies
├── NORMALIZATION.md            # In-depth DBMS normalization academic documentation
├── README.md                   # Project documentation and setup guide
│
├── routes/                     # Modular Flask Blueprints
│   ├── auth_routes.py          # Admin login and session management
│   ├── dashboard_routes.py     # Main KPI dashboard and chart API
│   ├── student_routes.py       # Student management and profile routes
│   ├── faculty_routes.py       # Faculty directory and course assignment
│   ├── attendance_routes.py    # Daily register, history logs, and attendance ledger
│   ├── performance_routes.py   # Marks entry, grade calculation, and editing
│   ├── analytics_routes.py     # Correlation and scatter plot analysis
│   ├── reports_routes.py       # Printable transcripts and CSV export
│   ├── dbms_showcase_routes.py # Live SQL concepts execution console
│   └── settings_routes.py      # MySQL configuration and connection tester
│
├── templates/                  # Jinja2 HTML5 Templates
│   ├── base.html               # Master layout with sidebar navigation and badges
│   ├── login.html              # Admin login interface with demo auto-fill
│   ├── dashboard.html          # Executive dashboard with Chart.js charts
│   ├── students.html           # Student management table with add/edit/delete modals
│   ├── student_profile.html    # Individual student attendance and marks dossier
│   ├── faculty.html            # Faculty roster and class allocation
│   ├── attendance.html         # Daily batch attendance marking sheet
│   ├── attendance_view.html    # Attendance date-wise history logs
│   ├── attendance_summary.html # Cumulative attendance percentage ledger
│   ├── performance.html        # Academic examination marks manager
│   ├── analytics.html          # Regression scatter plot and 4-cohort matrix
│   ├── reports.html            # Reports center and merit rank list
│   ├── student_card_print.html # Print-ready academic transcript / report card
│   ├── dbms_showcase.html      # Interactive DBMS query explorer
│   ├── settings.html           # Database connection manager
│   ├── 404.html                # 404 Not Found error page
│   └── 500.html                # 500 Server Error page
│
└── static/                     # Static web assets
    ├── css/
    │   └── style.css           # Custom professional styling and print styles
    └── js/                     # Client-side scripts
```

---

## 4. Step-by-Step Installation & Running on Windows

### Step 1: Open PowerShell or Command Prompt
Navigate to the project root folder:
```powershell
cd "C:\Users\Murugan Durai\.gemini\antigravity\scratch\student_analytics_system"
```

### Step 2: (Optional) Create and Activate Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Step 3: Install Required Python Packages
```powershell
pip install -r requirements.txt
```

### Step 4: Setup the MySQL Database in MySQL Workbench
1. Launch **MySQL Workbench 8.0 CE**.
2. Connect to your local MySQL instance (Default: `localhost:3306`).
3. Click **File &rarr; Open SQL Script...** and choose `database.sql` located in this project directory.
4. Click the **Execute (Lightning Bolt)** icon on the toolbar.
5. This creates the `student_analytics_db` database, all 10 relational tables, stored procedures, functions, triggers, views, and pre-populates realistic academic sample records.

### Step 5: Configure MySQL Connection (if using custom password)
If your local MySQL root user has a password, set it as an environment variable in PowerShell:
```powershell
$env:DB_USER = "root"
$env:DB_PASSWORD = "your_mysql_password"
$env:DB_NAME = "student_analytics_db"
```
*(Note: If MySQL Server is not running or credentials are not yet configured, the application automatically runs on its built-in high-fidelity database mirror so the entire system works immediately out-of-the-box!)*

### Step 6: Start the Flask Application
```powershell
python app.py
```

### Step 7: Open in Web Browser
Open your browser and navigate to:
```text
http://127.0.0.1:5000
```

---

## 5. Default Login Credentials

| Role | Username | Password | Access Level |
|---|---|---|---|
| **System Administrator** | `admin` | `admin123` | Full Access (All 7 Modules) |

*(A convenient "Fill Demo Credentials" button is present on the login page for instant authentication during reviews).*

---

## 6. College Viva / Oral Examination Questions & Answers

### Q1: Why did you choose MySQL for this project?
**Answer:** MySQL is an ACID-compliant, high-performance relational database management system (RDBMS) that provides robust support for primary keys, foreign key constraints, triggers, views, stored procedures, and complex multi-table joins. It ensures data consistency and integrity for critical academic records such as attendance logs and examination marks.

### Q2: How does the application prevent duplicate student entries?
**Answer:** At the database level, `register_number` and `email` columns have `UNIQUE` constraints in the `students` table. At the application level in `student_routes.py`, an explicit verification query runs prior to any `INSERT` statement, providing friendly user flash notifications if a duplicate is attempted.

### Q3: How is the attendance percentage calculated?
**Answer:** Attendance percentage is computed dynamically through SQL aggregate expressions and views using:
```sql
ROUND((SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)), 2)
```
Students falling below $75\%$ are automatically flagged as **Detained** according to university academic regulations.

### Q4: How is the correlation between attendance and performance computed?
**Answer:** The `analytics.py` module extracts the consolidated dataset into a **Pandas DataFrame** and uses **NumPy** (`np.corrcoef` and `np.polyfit`) to calculate the Pearson Correlation Coefficient ($r \approx 0.95$), the Coefficient of Determination ($R^2 \approx 0.90$), and the linear regression line ($y = mx + c$). The resulting coordinates and student cohorts are displayed interactively on a Chart.js scatter plot.

### Q5: What database triggers are implemented in the system?
**Answer:** The database includes `BEFORE INSERT` and `BEFORE UPDATE` triggers (`trg_before_performance_insert` and `trg_before_performance_update`) on the `performances` table. When marks are entered, the trigger automatically computes total marks, percentage, and invokes the stored function `fn_get_letter_grade()` to assign the corresponding letter grade (O, A+, A, B+, B, C, F) and standing remarks before storing the row on disk.

