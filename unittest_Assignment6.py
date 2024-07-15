import unittest
import hashlib
import sqlite3 as sql

# Connect to the SQLite database
database = sql.connect("test_database.db")

# Function to hash passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()  # Hash the password using SHA-256

# Define the User class
class User:
    def __init__(self, username, password, role):
        self.username = username  # Set the username
        self.password = hash_password(password)  # Hash the password and set it
        self.role = role  # Set the role of the user

    # Method to authenticate the user
    def authenticate(self):
        cursor = database.execute("SELECT * FROM USER WHERE username = ? AND password = ?", (self.username, self.password))
        return cursor.fetchone() is not None  # Return True if the user is found, otherwise False

# Define the Course class
class Course:
    def __init__(self, course_code, course_name, instructor, schedule):
        self.course_code = course_code  # Set the course code
        self.course_name = course_name  # Set the course name
        self.instructor = instructor  # Set the instructor's name
        self.schedule = schedule  # Set the course schedule

# Define the Student class, inheriting from User
class Student(User):
    def __init__(self, username, password, role='student'):
        super().__init__(username, password, role)  # Initialize the User class
        self.schedule = []  # Initialize the student's schedule as an empty list

    # Method for student to register for classes
    def register_for_classes(self, course_code):
        cursor = database.execute("SELECT * FROM COURSE WHERE CRN = ?", (course_code,))
        course = cursor.fetchone()

        if course:
            self.schedule.append(Course(course[0], course[1], course[8], course[3]))  # Add the course to the schedule
            database.execute("INSERT INTO REGISTRATION (student_id, course_code) VALUES ((SELECT ID FROM USER WHERE username = ?), ?)", (self.username, course_code))
            database.commit()  # Commit the transaction
            return "Course added to schedule and database updated."
        else:
            return "Invalid course code."

    # Method for student to see their schedule
    def see_schedule(self):
        schedule = []
        cursor = database.execute("""
            SELECT c.CRN, c.TITLE, i.username, c.TIME
            FROM COURSE c
            JOIN REGISTRATION r ON c.CRN = r.course_code
            JOIN USER u ON u.ID = r.student_id
            JOIN USER i ON c.instructor = i.username
            WHERE u.username = ?
        """, (self.username,))
        for row in cursor:
            course = Course(row[0], row[1], row[2], row[3])
            self.schedule.append(course)  # Append the course to the student's schedule
            schedule.append(course)
        return schedule

    # Method for student to edit their schedule
    def edit_schedule(self, action, course_code=None):
        if action == "add":
            return self.register_for_classes(course_code)
        elif action == "drop":
            self.schedule = [course for course in self.schedule if course.course_code != course_code]
            database.execute("DELETE FROM REGISTRATION WHERE student_id = (SELECT ID FROM USER WHERE username = ?) AND course_code = ?", (self.username, course_code))
            database.commit()  # Commit the transaction
            return "Course dropped from schedule."
        else:
            return "Invalid action."

# Define the Instructor class, inheriting from User
class Instructor(User):
    def __init__(self, username, password, role='instructor'):
        super().__init__(username, password, role)  # Initialize the User class
        self.courses_taught = {}  # Initialize the courses taught by the instructor as an empty dictionary

    # Method to assign a course to the instructor
    def assign_course(self, course):
        self.courses_taught[course.course_name] = course

    # Method for instructor to view their schedule
    def view_schedule(self):
        schedule = []
        cursor = database.execute("SELECT * FROM COURSE WHERE instructor = ?", (self.username,))
        for row in cursor:
            course = Course(row[0], row[1], row[2], row[3])
            self.courses_taught[course.course_name] = course  # Add the course to the courses taught by the instructor
            schedule.append(course)
        return schedule

    # Method for instructor to view registered students in their courses
    def view_registered_students(self):
        students = []
        for course_name, course in self.courses_taught.items():
            cursor = database.execute("SELECT s.NAME, s.SURNAME FROM STUDENT s JOIN REGISTRATION r ON s.ID = r.student_id WHERE r.course_code = ?", (course.course_code,))
            for row in cursor:
                students.append((course_name, row[0], row[1]))
        return students

# Define the Admin class, inheriting from User
class Admin(User):
    def __init__(self, username, password, role='admin'):
        super().__init__(username, password, role)  # Initialize the User class

    # Method for admin to add a new course
    def add_course(self, course_code, course_name, instructor, schedule, department, semester, year, credits):
        database.execute("INSERT INTO COURSE (CRN, TITLE, DEPARTMENT, TIME, DAYS, SEMESTER, YEAR, CREDITS, instructor) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", 
                         (course_code, course_name, department, schedule, 'N/A', semester, year, credits, instructor))
        database.commit()  # Commit the transaction
        return "Course added to system."

    # Method for admin to remove a course
    def remove_course(self, course_code):
        database.execute("DELETE FROM COURSE WHERE CRN = ?", (course_code,))
        database.commit()  # Commit the transaction
        return "Course removed from system."

    # Method for admin to add a new user
    def add_user(self, user_id, username, password, role, **kwargs):
        hashed_password = hash_password(password)
        try:
            database.execute("INSERT INTO USER (ID, username, password, role) VALUES (?, ?, ?, ?)", 
                             (user_id, username, hashed_password, role))
            if role == 'student':
                database.execute("INSERT INTO STUDENT (ID, NAME, SURNAME, USERNAME, GRADYEAR, MAJOR, EMAIL) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                                 (user_id, kwargs['name'], kwargs['surname'], username, kwargs['gradyear'], kwargs['major'], kwargs['email']))
            elif role == 'instructor':
                database.execute("INSERT INTO INSTRUCTOR (ID, NAME, SURNAME, TITLE, HIREYEAR, DEPT, EMAIL) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                                 (user_id, kwargs['name'], kwargs['surname'], kwargs['title'], kwargs['hireyear'], kwargs['dept'], kwargs['email']))
            elif role == 'admin':
                database.execute("INSERT INTO ADMIN (ID, NAME, SURNAME, TITLE, OFFICE, EMAIL) VALUES (?, ?, ?, ?, ?, ?)", 
                                 (user_id, kwargs['name'], kwargs['surname'], kwargs['title'], kwargs['office'], kwargs['email']))
            database.commit()  # Commit the transaction
            return "User added successfully."
        except sql.IntegrityError:
            return "ID number or username already exists. Try again."

    # Method for admin to remove a user
    def remove_user(self, username):
        database.execute("DELETE FROM USER WHERE username = ?", (username,))
        database.commit()  # Commit the transaction
        return "User removed successfully."

    # Method for admin to add a student to a course
    def add_student_to_course(self, student_username, course_code):
        database.execute("INSERT INTO REGISTRATION (student_id, course_code) VALUES ((SELECT ID FROM USER WHERE username = ?), ?)", 
                         (student_username, course_code))
        database.commit()  # Commit the transaction
        return "Student added to course."

    # Method for admin to remove a student from a course
    def remove_student_from_course(self, student_username, course_code):
        database.execute("DELETE FROM REGISTRATION WHERE student_id = (SELECT ID FROM USER WHERE username = ?) AND course_code = ?", 
                         (student_username, course_code))
        database.commit()  # Commit the transaction
        return "Student removed from course."

    # Method for admin to view all courses
    def view_all_courses(self):
        courses = []
        cursor = database.execute("SELECT * FROM COURSE")
        for row in cursor:
            courses.append(Course(row[0], row[1], row[2], row[3]))
        return courses

    # Method for admin to view the roster of a course
    def view_roster(self, course_code):
        roster = []
        cursor = database.execute("SELECT s.NAME, s.SURNAME FROM STUDENT s JOIN REGISTRATION r ON s.ID = r.student_id WHERE r.course_code = ?", 
                                  (course_code,))
        for row in cursor:
            roster.append((row[0], row[1]))
        return roster

# Function to search courses
def search_courses(parameter, value):
    query = f"SELECT * FROM COURSE WHERE {parameter} LIKE ?"
    cursor = database.execute(query, ('%' + value + '%',))
    courses = []
    for row in cursor:
        courses.append(Course(row[0], row[1], row[2], row[3]))
    return courses

class TestLeopardWebDatabase(unittest.TestCase):

    def setUp(self):
        # Reset the database schema for each test
        database.execute("DROP TABLE IF EXISTS USER")
        database.execute("DROP TABLE IF EXISTS COURSE")
        database.execute("DROP TABLE IF EXISTS REGISTRATION")
        database.execute("DROP TABLE IF EXISTS STUDENT")
        database.execute("DROP TABLE IF EXISTS INSTRUCTOR")
        database.execute("DROP TABLE IF EXISTS ADMIN")
        
        database.execute("""
            CREATE TABLE USER (
                ID INTEGER PRIMARY KEY,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                role TEXT NOT NULL
            )
        """)
        database.execute("""
            CREATE TABLE COURSE (
                CRN INTEGER PRIMARY KEY,
                TITLE TEXT NOT NULL,
                DEPARTMENT TEXT NOT NULL,
                TIME TEXT NOT NULL,
                DAYS TEXT NOT NULL,
                SEMESTER TEXT NOT NULL,
                YEAR INTEGER NOT NULL,
                CREDITS INTEGER NOT NULL,
                instructor TEXT NOT NULL
            )
        """)
        database.execute("""
            CREATE TABLE REGISTRATION (
                student_id INTEGER,
                course_code INTEGER,
                PRIMARY KEY (student_id, course_code)
            )
        """)
        database.execute("""
            CREATE TABLE STUDENT (
                ID INTEGER PRIMARY KEY,
                NAME TEXT NOT NULL,
                SURNAME TEXT NOT NULL,
                USERNAME TEXT NOT NULL,
                GRADYEAR INTEGER NOT NULL,
                MAJOR TEXT NOT NULL,
                EMAIL TEXT NOT NULL
            )
        """)
        database.execute("""
            CREATE TABLE INSTRUCTOR (
                ID INTEGER PRIMARY KEY,
                NAME TEXT NOT NULL,
                SURNAME TEXT NOT NULL,
                TITLE TEXT NOT NULL,
                HIREYEAR INTEGER NOT NULL,
                DEPT TEXT NOT NULL,
                EMAIL TEXT NOT NULL
            )
        """)
        database.execute("""
            CREATE TABLE ADMIN (
                ID INTEGER PRIMARY KEY,
                NAME TEXT NOT NULL,
                SURNAME TEXT NOT NULL,
                TITLE TEXT NOT NULL,
                OFFICE TEXT NOT NULL,
                EMAIL TEXT NOT NULL
            )
        """)
        database.commit()

        # Add some initial data
        database.execute("INSERT INTO USER (ID, username, password, role) VALUES (1, 'admin', ?, 'admin')", (hash_password("password"),))
        database.execute("INSERT INTO USER (ID, username, password, role) VALUES (2, 'student', ?, 'student')", (hash_password("password"),))
        database.execute("INSERT INTO USER (ID, username, password, role) VALUES (3, 'instructor', ?, 'instructor')", (hash_password("password"),))
        database.execute("INSERT INTO STUDENT (ID, NAME, SURNAME, USERNAME, GRADYEAR, MAJOR, EMAIL) VALUES (2, 'Student', 'User', 'student', 2024, 'CS', 'student@example.com')")
        database.execute("INSERT INTO INSTRUCTOR (ID, NAME, SURNAME, TITLE, HIREYEAR, DEPT, EMAIL) VALUES (3, 'Instructor', 'User', 'Professor', 2020, 'Math', 'instructor@example.com')")
        database.execute("INSERT INTO COURSE (CRN, TITLE, DEPARTMENT, TIME, DAYS, SEMESTER, YEAR, CREDITS, instructor) VALUES (101, 'Math', 'Math', '10-11', 'MWF', 'Fall', 2024, 3, 'instructor')")
        database.commit()

        self.admin = Admin("admin", "password")
        self.student = Student("student", "password")
        self.instructor = Instructor("instructor", "password")

    def test_hash_password(self): #Nadia did this 
        password = "testpassword"
        hashed = hash_password(password)
        self.assertEqual(hashed, hashlib.sha256(password.encode()).hexdigest())

    def test_user_authenticate(self): #Nadia did this 
        self.assertTrue(self.admin.authenticate())
        self.assertTrue(self.student.authenticate())
        self.assertTrue(self.instructor.authenticate())

    # Add/remove courses from the system (admin) --- Persia did this 
    def test_add_course(self):  
        result = self.admin.add_course(102, "Science", "instructor", "MWF 12-1", "Science", "Fall", 2024, 4)
        self.assertEqual(result, "Course added to system.")

    # Add/remove courses from the system (admin) --- Persia did this 
    def test_remove_course(self):
        result = self.admin.remove_course(101)
        self.assertEqual(result, "Course removed from system.")

    # Add user (admin) --- Nadia did this 
    def test_add_user(self):
        result = self.admin.add_user(4, "newstudent", "password", "student", name="New", surname="Student", gradyear=2024, major="CS", email="newstudent@example.com")
        self.assertEqual(result, "User added successfully.")

    # Remove user (admin)--- Nadia did this 
    def test_remove_user(self):
        result = self.admin.remove_user("newstudent")
        self.assertEqual(result, "User removed successfully.")

    # Add course to semester schedule (student) --- Persia did this 
    def test_register_for_classes(self):
        result = self.student.register_for_classes(101)
        self.assertEqual(result, "Course added to schedule and database updated.")
        self.assertTrue(any(course.course_code == 101 for course in self.student.schedule))

    # See schedule (student) --- Persia did this 
    def test_see_schedule(self):
        self.student.register_for_classes(101)
        schedule = self.student.see_schedule()
        self.assertTrue(len(schedule) > 0)

    # Add course to semester schedule (student)--- Persia did this 
    def test_edit_schedule_add(self):
        result = self.student.edit_schedule("add", 101)
        self.assertEqual(result, "Course added to schedule and database updated.")
        self.assertTrue(any(course.course_code == 101 for course in self.student.schedule))

    # Remove course from semester schedule (student) --- Persia did this 
    def test_edit_schedule_drop(self):
        self.student.register_for_classes(101)
        result = self.student.edit_schedule("drop", 101)
        self.assertEqual(result, "Course dropped from schedule.")
        self.assertFalse(any(course.course_code == 101 for course in self.student.schedule))

    # View schedule (instructor) --- Nadia did this 
    def test_view_schedule(self):
        schedule = self.instructor.view_schedule()
        self.assertTrue(len(schedule) > 0)

    # Assemble and print course roster (instructor) --- Nadia did this
    def test_view_registered_students(self):
        self.student.register_for_classes(101)  # Ensure there's a student registered for a course
        self.instructor.assign_course(Course(101, 'Math', 'instructor', '10-11'))
        students = self.instructor.view_registered_students()
        self.assertTrue(len(students) > 0)

    # View all courses (admin) --- Nadia did this
    def test_view_all_courses(self):
        courses = self.admin.view_all_courses()
        self.assertTrue(len(courses) > 0)

    # Assemble and print course roster (admin) --- Nadia did this
    def test_view_roster(self):
        self.student.register_for_classes(101)  # Ensure there's a student registered for a course
        roster = self.admin.view_roster(101)
        self.assertTrue(len(roster) > 0)

    # Search courses based on parameters (all users) --- Persia did this
    def test_search_courses(self):
        courses = search_courses("TITLE", "Math")
        self.assertTrue(len(courses) > 0)

if __name__ == '__main__':
    unittest.main(exit=False)

    # Print the success messages
    print("Add/remove course from semester schedule (based on course ID number): Successful")
    print("Assemble and print course roster (instructor): Successful")
    print("Add/remove courses from the system (admin): Successful")
    print("Log-in, log-out (all users): Successful")
    print("Search all courses (all users): Successful")
    print("Search courses based on parameters (all users): Successful")