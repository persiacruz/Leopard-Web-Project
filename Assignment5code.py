import sqlite3 as sql  # Import the sqlite3 library and alias it as sql
import hashlib  # Import the hashlib library for hashing passwords

# Connect to the SQLite database
database = sql.connect("LeopardWebDatabase.db")

#Nadia completed this part
# Function to hash passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()  # Hash the password using SHA-256

#Nadia completed this part
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

    # Method to print user information
    def print_info(self):
        print(f"Username: {self.username}, Role: {self.role}")

#Persia completed this part
# Define the Course class
class Course:
    def __init__(self, course_code, course_name, instructor, schedule):
        self.course_code = course_code  # Set the course code
        self.course_name = course_name  # Set the course name
        self.instructor = instructor  # Set the instructor's name
        self.schedule = schedule  # Set the course schedule

    # Method to print course information
    def print_info(self):
        print("Course Code:", self.course_code)
        print("Course Name:", self.course_name)
        print("Instructor:", self.instructor)
        print("Schedule:", self.schedule)

#Nadia completed this part
# Define the Student class, inheriting from User
class Student(User):
    def __init__(self, username, password, role='student'):
        super().__init__(username, password, role)  # Initialize the User class
        self.schedule = []  # Initialize the student's schedule as an empty list

    # Method for student to register for classes
    def register_for_classes(self):
        print("Registering for classes...")
        print("Available Classes:")
        cursor = database.execute("SELECT * FROM COURSE")  # Query all courses
        for row in cursor:
            print(f"Course Code: {row[0]}, Course Name: {row[1]}, Instructor: {row[8]}, Schedule: {row[3]}")

        course_code = int(input("Enter the course code you want to register for: "))
        cursor = database.execute("SELECT * FROM COURSE WHERE CRN = ?", (course_code,))
        course = cursor.fetchone()

        if course:
            self.schedule.append(Course(course[0], course[1], course[8], course[3]))  # Add the course to the schedule
            database.execute("INSERT INTO REGISTRATION (student_id, course_code) VALUES ((SELECT ID FROM USER WHERE username = ?), ?)", (self.username, course_code))
            database.commit()  # Commit the transaction
            print("Course added to schedule and database updated.")
        else:
            print("Invalid course code.")

    # Method for student to see their schedule
    def see_schedule(self):
        print("Viewing schedule...")
        cursor = database.execute("""
            SELECT c.CRN, c.TITLE, i.NAME, c.TIME
            FROM COURSE c
            JOIN REGISTRATION r ON c.CRN = r.course_code
            JOIN USER u ON u.ID = r.student_id
            JOIN INSTRUCTOR i ON c.instructor_id = i.ID
            WHERE u.username = ?
        """, (self.username,))
        for row in cursor:
            course = Course(row[0], row[1], row[2], row[3])
            self.schedule.append(course)  # Append the course to the student's schedule
            course.print_info()

    # Method for student to edit their schedule
    def edit_schedule(self):
        print("Editing schedule...")
        self.see_schedule()
        action = input("Enter 'add' to add a course or 'drop' to drop a course: ").lower()
        if action == "add":
            self.register_for_classes()
        elif action == "drop":
            course_code = int(input("Enter the course code to drop: "))
            self.schedule = [course for course in self.schedule if course.course_code != course_code]
            database.execute("DELETE FROM REGISTRATION WHERE student_id = (SELECT ID FROM USER WHERE username = ?) AND course_code = ?", (self.username, course_code))
            database.commit()  # Commit the transaction
            print("Course dropped from schedule.")
        else:
            print("Invalid action.")
#Persia completed this part    
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
        print("Viewing schedule...")
        cursor = database.execute("SELECT * FROM COURSE WHERE instructor = ?", (self.username,))
        for row in cursor:
            course = Course(row[0], row[1], row[2], row[3])
            self.courses_taught[course.course_name] = course  # Add the course to the courses taught by the instructor
            course.print_info()

    # Method for instructor to view registered students in their courses
    def view_registered_students(self):
        print("Viewing registered students...")
        for course_name, course in self.courses_taught.items():
            print(f"Course: {course_name}")
            cursor = database.execute("SELECT s.NAME, s.SURNAME FROM STUDENT s JOIN REGISTRATION r ON s.ID = r.student_id WHERE r.course_code = ?", (course.course_code,))
            print("Students:")
            for row in cursor:
                print(f"{row[0]} {row[1]}")

#Nadia completed this part
# Define the Admin class, inheriting from User
class Admin(User):
    def __init__(self, username, password, role='admin'):
        super().__init__(username, password, role)  # Initialize the User class

    # Method for admin to add a new course
    def add_course(self):
        course_code = int(input("Enter course code: "))
        course_name = input("Enter course name: ")
        instructor = input("Enter instructor username: ")
        schedule = input("Enter schedule: ")
        department = input("Enter department: ")
        semester = input("Enter semester: ")
        year = int(input("Enter year: "))
        credits = int(input("Enter credits: "))
        
        database.execute("INSERT INTO COURSE (CRN, TITLE, DEPARTMENT, TIME, DAYS, SEMESTER, YEAR, CREDITS, instructor) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", 
                         (course_code, course_name, department, schedule, 'N/A', semester, year, credits, instructor))
        database.commit()  # Commit the transaction
        print("Course added to system.")

    # Method for admin to remove a course
    def remove_course(self):
        course_code = int(input("Enter course code to remove: "))
        database.execute("DELETE FROM COURSE WHERE CRN = ?", (course_code,))
        database.commit()  # Commit the transaction
        print("Course removed from system.")

    # Method for admin to add a new user
    def add_user(self):
        user_id = int(input("Enter new ID number: "))
        username = input("Enter new username: ")
        password = input("Create a password: ")
        role = input("Enter role (student, instructor, admin): ").lower()
        hashed_password = hash_password(password)
        try:
            database.execute("INSERT INTO USER (ID, username, password, role) VALUES (?, ?, ?, ?)", 
                             (user_id, username, hashed_password, role))
            if role == 'student':
                name = input("Enter student's first name: ")
                surname = input("Enter student's last name: ")
                gradyear = input("Enter student's graduation year: ")
                major = input("Enter student's major: ")
                email = input("Enter student's email: ")
                database.execute("INSERT INTO STUDENT (ID, NAME, SURNAME, USERNAME, GRADYEAR, MAJOR, EMAIL) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                                 (user_id, name, surname, username, gradyear, major, email))
            elif role == 'instructor':
                name = input("Enter instructor's first name: ")
                surname = input("Enter instructor's last name: ")
                title = input("Enter instructor's title: ")
                hireyear = int(input("Enter instructor's hire year: "))
                dept = input("Enter instructor's department: ")
                email = input("Enter instructor's email: ")
                database.execute("INSERT INTO INSTRUCTOR (ID, NAME, SURNAME, TITLE, HIREYEAR, DEPT, EMAIL) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                                 (user_id, name, surname, title, hireyear, dept, email))
            elif role == 'admin':
                name = input("Enter admin's first name: ")
                surname = input("Enter admin's last name: ")
                title = input("Enter admin's title: ")
                office = input("Enter admin's office: ")
                email = input("Enter admin's email: ")
                database.execute("INSERT INTO ADMIN (ID, NAME, SURNAME, TITLE, OFFICE, EMAIL) VALUES (?, ?, ?, ?, ?, ?)", 
                                 (user_id, name, surname, title, office, email))
            database.commit()  # Commit the transaction
            print("User added successfully.")
        except sql.IntegrityError:
            print("ID number or username already exists. Try again.")

    # Method for admin to remove a user
    def remove_user(self):
        username = input("Enter username to remove: ")
        database.execute("DELETE FROM USER WHERE username = ?", (username,))
        database.commit()  # Commit the transaction
        print("User removed successfully.")

    # Method for admin to add a student to a course
    def add_student_to_course(self):
        student_username = input("Enter student username: ")
        course_code = int(input("Enter course code: "))
        database.execute("INSERT INTO REGISTRATION (student_id, course_code) VALUES ((SELECT ID FROM USER WHERE username = ?), ?)", 
                         (student_username, course_code))
        database.commit()  # Commit the transaction
        print("Student added to course.")

    # Method for admin to remove a student from a course
    def remove_student_from_course(self):
        student_username = input("Enter student username: ")
        course_code = int(input("Enter course code: "))
        database.execute("DELETE FROM REGISTRATION WHERE student_id = (SELECT ID FROM USER WHERE username = ?) AND course_code = ?", 
                         (student_username, course_code))
        database.commit()  # Commit the transaction
        print("Student removed from course.")

    # Method for admin to view all courses
    def view_all_courses(self):
        print("Viewing all courses...")
        cursor = database.execute("SELECT * FROM COURSE")
        for row in cursor:
            print(f"Course Code: {row[0]}, Course Name: {row[1]}, Instructor: {row[2]}, Schedule: {row[3]}")

    # Method for admin to view the roster of a course
    def view_roster(self):
        course_code = int(input("Enter course code: "))
        cursor = database.execute("SELECT s.NAME, s.SURNAME FROM STUDENT s JOIN REGISTRATION r ON s.ID = r.student_id WHERE r.course_code = ?", 
                                  (course_code,))
        print(f"Roster for Course Code {course_code}:")
        for row in cursor:
            print(f"{row[0]} {row[1]}")

#Persia completed this part
# Function to display the main menu
def main_menu():
    while True:
        print("\nMain Menu:")
        print("1. Login")
        print("2. Register")
        print("3. Exit")
        choice = input("Enter your choice (1-3): ")

        if choice == "1":
            role = input("Enter role (student, instructor, admin): ").lower()
            username = input("Enter username: ")
            password = input("Enter password: ")

            if role == "student":
                user = Student(username, password)
            elif role == "instructor":
                user = Instructor(username, password)
            elif role == "admin":
                user = Admin(username, password)
            else:
                print("Invalid role. Try again.")
                continue

            if user.authenticate():
                print(f"Login successful. Welcome, {username}!")
                if role == "student":
                    student_menu(user)
                elif role == "instructor":
                    instructor_menu(user)
                elif role == "admin":
                    admin_menu(user)
            else:
                print("Login failed. Invalid credentials.")
        elif choice == "2":
            role = input("Enter role (student, instructor, admin): ").lower()
            username = input("Enter new username: ")
            password = input("Create a password: ")

            hashed_password = hash_password(password)
            try:
                database.execute("INSERT INTO USER (username, password, role) VALUES (?, ?, ?)", (username, hashed_password, role))
                if role == 'student':
                    name = input("Enter student's first name: ")
                    surname = input("Enter student's last name: ")
                    gradyear = input("Enter student's graduation year: ")
                    major = input("Enter student's major: ")
                    email = input("Enter student's email: ")
                    database.execute("INSERT INTO STUDENT (NAME, SURNAME, USERNAME, GRADYEAR, MAJOR, EMAIL) VALUES (?, ?, ?, ?, ?, ?)", 
                                     (name, surname, username, gradyear, major, email))
                database.commit()  # Commit the transaction
                print("Registration successful.")
            except sql.IntegrityError:
                print("Username already exists. Try again.")
        elif choice == "3":
            print("Exiting...")
            database.close()  # Close the database connection
            break
        else:
            print("Invalid choice. Please try again.")

#Persia completed this part
# Function to display the student menu
def student_menu(user):
    while True:
        print("\nStudent Menu:")
        print("1. Register for classes")
        print("2. See schedule")
        print("3. Edit schedule")
        print("4. Logout")
        choice = input("Enter your choice (1-4): ")

        if choice == "1":
            user.register_for_classes()
        elif choice == "2":
            user.see_schedule()
        elif choice == "3":
            user.edit_schedule()
        elif choice == "4":
            break
        else:
            print("Invalid choice. Please try again.")

#Nadia completed this part
# Function to display the instructor menu
def instructor_menu(user):
    while True:
        print("\nInstructor Menu:")
        print("1. View schedule")
        print("2. View registered students")
        print("3. Search courses")
        print("4. Logout")
        choice = input("Enter your choice (1-4): ")

        if choice == "1":
            user.view_schedule()
        elif choice == "2":
            user.view_registered_students()
        elif choice == "3":
            search_courses()
        elif choice == "4":
            break
        else:
            print("Invalid choice. Please try again.")

#Nadia completed this part
# Function to display the admin menu
def admin_menu(user):
    while True:
        print("\nAdmin Menu:")
        print("1. Add course")
        print("2. Remove course")
        print("3. Add user")
        print("4. Remove user")
        print("5. Add student to course")
        print("6. Remove student from course")
        print("7. View all courses")
        print("8. View roster")
        print("9. Search courses")
        print("10. Logout")
        choice = input("Enter your choice (1-10): ")

        if choice == "1":
            user.add_course()
        elif choice == "2":
            user.remove_course()
        elif choice == "3":
            user.add_user()
        elif choice == "4":
            user.remove_user()
        elif choice == "5":
            user.add_student_to_course()
        elif choice == "6":
            user.remove_student_from_course()
        elif choice == "7":
            user.view_all_courses()
        elif choice == "8":
            user.view_roster()
        elif choice == "9":
            search_courses()
        elif choice == "10":
            break
        else:
            print("Invalid choice. Please try again.")
            
#Persia completed this part
# Function to search courses
def search_courses():
    parameter = input("Enter search parameter (course code, name, instructor, schedule): ").lower()
    value = input("Enter value to search: ")
    query = f"SELECT * FROM COURSE WHERE {parameter} LIKE ?"
    cursor = database.execute(query, ('%' + value + '%',))
    for row in cursor:
        print(f"Course Code: {row[0]}, Course Name: {row[1]}, Instructor: {row[2]}, Schedule: {row[3]}")

# Start the application
main_menu()





