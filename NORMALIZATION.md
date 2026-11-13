# Database Normalization Report: Smart Student Attendance and Performance Analytics System

**Department:** Computer Science & Engineering  
**Academic Year:** 2026 - 2027  
**Database Engine:** MySQL 8.0 / InnoDB Engine  

---

## 1. Relational Schema & Entities

The relational database schema is structured into ten distinct relations:

1. $\text{Departments}(\underline{\text{dept\_id}}, \text{dept\_code}, \text{dept\_name}, \text{description}, \text{created\_at})$
2. $\text{Faculty}(\underline{\text{faculty\_id}}, \text{faculty\_code}, \text{name}, \text{email}, \text{phone}, \text{dept\_id}^*, \text{designation}, \text{qualification})$
3. $\text{Students}(\underline{\text{student\_id}}, \text{register\_number}, \text{name}, \text{email}, \text{phone}, \text{dept\_id}^*, \text{year}, \text{semester}, \text{section}, \text{gender}, \text{dob})$
4. $\text{Courses}(\underline{\text{course\_id}}, \text{course\_code}, \text{course\_name}, \text{credits}, \text{dept\_id}^*, \text{semester})$
5. $\text{Classes}(\underline{\text{class\_id}}, \text{course\_id}^*, \text{faculty\_id}^*, \text{academic\_year}, \text{semester}, \text{section}, \text{classroom})$
6. $\text{Attendance}(\underline{\text{attendance\_id}}, \text{student\_id}^*, \text{course\_id}^*, \text{attendance\_date}, \text{status}, \text{remarks})$
7. $\text{Exams}(\underline{\text{exam\_id}}, \text{exam\_name}, \text{exam\_type}, \text{course\_id}^*, \text{max\_marks}, \text{exam\_date})$
8. $\text{Assignments}(\underline{\text{assignment\_id}}, \text{course\_id}^*, \text{title}, \text{max\_marks}, \text{due\_date})$
9. $\text{Performances}(\underline{\text{performance\_id}}, \text{student\_id}^*, \text{course\_id}^*, \text{exam\_id}^*, \text{assignment\_id}^*, \text{internal\_marks}, \text{assignment\_marks}, \text{exam\_marks}, \text{total\_marks}, \text{percentage}, \text{grade}, \text{remarks})$
10. $\text{Admins}(\underline{\text{admin\_id}}, \text{username}, \text{password\_hash}, \text{full\_name}, \text{email}, \text{role})$

*(Underlined attributes denote Primary Keys; asterisks denote Foreign Keys)*

---

## 2. Functional Dependencies (FDs)

- **Departments:**
  - $\text{dept\_id} \rightarrow \text{dept\_code}, \text{dept\_name}, \text{description}$
  - $\text{dept\_code} \rightarrow \text{dept\_id}, \text{dept\_name}$

- **Students:**
  - $\text{student\_id} \rightarrow \text{register\_number}, \text{name}, \text{email}, \text{phone}, \text{dept\_id}, \text{year}, \text{semester}, \text{section}, \text{gender}$
  - $\text{register\_number} \rightarrow \text{student\_id}, \text{name}, \text{email}, \text{dept\_id}$
  - $\text{email} \rightarrow \text{student\_id}, \text{register\_number}$

- **Faculty:**
  - $\text{faculty\_id} \rightarrow \text{faculty\_code}, \text{name}, \text{email}, \text{phone}, \text{dept\_id}, \text{designation}, \text{qualification}$
  - $\text{faculty\_code} \rightarrow \text{faculty\_id}, \text{name}, \text{email}$

- **Courses:**
  - $\text{course\_id} \rightarrow \text{course\_code}, \text{course\_name}, \text{credits}, \text{dept\_id}, \text{semester}$
  - $\text{course\_code} \rightarrow \text{course\_id}, \text{course\_name}$

- **Attendance:**
  - $\text{attendance\_id} \rightarrow \text{student\_id}, \text{course\_id}, \text{attendance\_date}, \text{status}, \text{remarks}$
  - $(\text{student\_id}, \text{course\_id}, \text{attendance\_date}) \rightarrow \text{status}, \text{remarks}$

- **Performances:**
  - $\text{performance\_id} \rightarrow \text{student\_id}, \text{course\_id}, \text{exam\_id}, \text{internal\_marks}, \text{assignment\_marks}, \text{exam\_marks}, \text{total\_marks}, \text{percentage}, \text{grade}$
  - $(\text{student\_id}, \text{course\_id}, \text{exam\_id}) \rightarrow \text{performance\_id}, \text{total\_marks}, \text{grade}$

---

## 3. Step-by-Step Normalization Analysis

### 3.1 First Normal Form (1NF)
**Rule:** An entity is in 1NF if every column contains only atomic (indivisible) values and there are no repeating groups or arrays.

- **Initial State:** If attendance dates and student marks were stored in CSV or delimited strings within a single row (e.g., `attendance_dates = "2026-08-01, 2026-08-02"`), the relation would violate 1NF.
- **Normalization Action:** The schema stores exactly one session per row in `attendance` and exactly one exam score per row in `performances`.
- **Conclusion:** **1NF is fully satisfied.**

### 3.2 Second Normal Form (2NF)
**Rule:** A relation is in 2NF if it is in 1NF and no non-prime attribute is partially dependent on any candidate key (elimination of partial functional dependencies).

- **Initial State:** If a single unnormalized table `Student_Course_Performance` existed with composite key $(\text{student\_id}, \text{course\_id})$, then $\text{student\_name}$ would depend solely on $\text{student\_id}$ (a proper subset of the key), creating a partial dependency.
- **Normalization Action:** Every table has a single-column surrogate Primary Key (`student_id`, `course_id`, `performance_id`).
- All non-key attributes depend on the *entire* primary key.
- **Conclusion:** **2NF is fully satisfied.**

### 3.3 Third Normal Form (3NF)
**Rule:** A relation is in 3NF if it is in 2NF and no non-prime attribute is transitively dependent on the primary key (no $X \rightarrow Y \rightarrow Z$ where neither $X$ nor $Y$ is a superkey).

- **Initial State:** If `students` contained:
  $$\text{student\_id} \rightarrow \text{dept\_id} \rightarrow \text{dept\_name}, \text{dept\_code}$$
  Here, $\text{dept\_name}$ is transitively dependent on $\text{student\_id}$. If department information changes, multiple student rows would need updates, causing update anomalies.
- **Normalization Action:** Department details were decomposed into a separate table `departments`. `students` retains only the foreign key `dept_id`.
- **Conclusion:** **3NF is fully satisfied.**

### 3.4 Boyce-Codd Normal Form (BCNF)
**Rule:** For every functional dependency $X \rightarrow Y$, $X$ must be a superkey.

- In every relation in our design, every determinant is a primary key or unique candidate key (e.g., `register_number`, `faculty_code`, `course_code`).
- There are no overlapping candidate keys with non-trivial dependencies.
- **Conclusion:** **BCNF is fully satisfied.**

### 3.5 Fourth Normal Form (4NF)
**Rule:** A relation is in 4NF if it is in BCNF and contains no non-trivial multi-valued dependencies ($X \twoheadrightarrow Y$).

- A student can have multiple attendance dates and multiple exam marks. If both were stored in the same table, a Cartesian product anomaly would occur ($A \twoheadrightarrow B \text{ and } A \twoheadrightarrow C$).
- In our schema, `attendance` and `performances` are completely independent tables referencing `student_id`.
- **Conclusion:** **4NF is fully satisfied.**

### 3.6 Fifth Normal Form (5NF / PJNF)
**Rule:** The relation cannot be non-loss decomposed into any number of smaller relations with different keys.
- The `classes` relation links `course_id`, `faculty_id`, `academic_year`, `semester`, and `section`. None of these can be omitted without destroying the assignment integrity.
- **Conclusion:** **5NF is fully satisfied.**

---

## 4. Integrity Constraints Summary

| Table | Primary Key | Foreign Key | Unique Constraints | Check Constraints |
|---|---|---|---|---|
| `departments` | `dept_id` | None | `dept_code` | None |
| `faculty` | `faculty_id` | `dept_id` $\rightarrow$ `departments` | `faculty_code`, `email` | None |
| `students` | `student_id` | `dept_id` $\rightarrow$ `departments` | `register_number`, `email` | `year BETWEEN 1 AND 4`, `semester BETWEEN 1 AND 8` |
| `courses` | `course_id` | `dept_id` $\rightarrow$ `departments` | `course_code` | `credits > 0`, `semester BETWEEN 1 AND 8` |
| `classes` | `class_id` | `course_id`, `faculty_id` | `(course, faculty, year, sem, sec)` | `semester BETWEEN 1 AND 8` |
| `attendance` | `attendance_id` | `student_id`, `course_id` | `(student_id, course_id, date)` | `status IN ('Present', 'Absent')` |
| `exams` | `exam_id` | `course_id` | None | `max_marks > 0` |
| `assignments` | `assignment_id` | `course_id` | None | `max_marks > 0` |
| `performances` | `performance_id` | `student_id`, `course_id`, `exam_id` | `(student_id, course_id, exam_id)` | `internal_marks BETWEEN 0 AND 30`, `exam_marks BETWEEN 0 AND 50` |
| `admins` | `admin_id` | None | `username`, `email` | None |

