import sqlite3 as sql
import hashlib
import tkinter as tk
from tkinter import messagebox, simpledialog

# Connect to the SQLite database
database = sql.connect("LeopardWebDatabase.db")

# Function to hash passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Define the User class
class User:
    def __init__(self, username, password, role):
        self.username = username
        self.password = hash_password(password)
        self.role = role

    def authenticate(self):
        cursor = database.execute("SELECT * FROM USER WHERE username = ? AND password = ?", (self.username, self.password))
        return cursor.fetchone() is not None

# Define the Course class
class Course:
    def __init__(self, course_code, course_name, instructor, schedule):
        self.course_code = course_code
        self.course_name = course_name
        self.instructor = instructor
        self.schedule = schedule

# Define the Student class, inheriting from User
class Student(User):
    def __init__(self, username, password, role='student'):
        super().__init__(username, password, role)
        self.schedule = []

    def register_for_classes(self):
        courses = []
        cursor = database.execute("SELECT CRN, TITLE, DEPARTMENT, TIME, DAYS, SEMESTER, YEAR, CREDITS FROM COURSE")
        for row in cursor:
            courses.append(f"{row[0]}: {row[1]}, {row[2]}, {row[3]}, {row[4]}, {row[5]}, {row[6]}, {row[7]} credits")
        return courses

    def add_course_to_schedule(self, course_code):
        cursor = database.execute("SELECT * FROM COURSE WHERE CRN = ?", (course_code,))
        course = cursor.fetchone()
        if course:
            self.schedule.append(Course(course[0], course[1], course[8], course[3]))
            database.execute("INSERT INTO REGISTRATION (student_id, course_code) VALUES ((SELECT ID FROM USER WHERE username = ?), ?)", (self.username, course_code))
            database.commit()
            return "Course added to schedule and database updated."
        else:
            return "Invalid course code."

    def see_schedule(self):
        self.schedule.clear()
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
            self.schedule.append(course)
        return self.schedule

    def edit_schedule(self, action, course_code):
        if action == "add":
            return self.add_course_to_schedule(course_code)
        elif action == "drop":
            self.schedule = [course for course in self.schedule if course.course_code != course_code]
            database.execute("DELETE FROM REGISTRATION WHERE student_id = (SELECT ID FROM USER WHERE username = ?) AND course_code = ?", (self.username, course_code))
            database.commit()
            return "Course dropped from schedule."
        else:
            return "Invalid action."

# Define the Instructor class, inheriting from User
class Instructor(User):
    def __init__(self, username, password, role='instructor'):
        super().__init__(username, password, role)
        self.courses_taught = {}

    def assign_course(self, course):
        self.courses_taught[course.course_name] = course

    def view_schedule(self):
        self.courses_taught.clear()
        cursor = database.execute("SELECT * FROM COURSE WHERE instructor = ?", (self.username,))
        for row in cursor:
            course = Course(row[0], row[1], row[2], row[3])
            self.courses_taught[course.course_name] = course
        return self.courses_taught

    def view_registered_students(self):
        students = {}
        for course_name, course in self.courses_taught.items():
            students[course_name] = []
            cursor = database.execute("SELECT s.NAME, s.SURNAME FROM STUDENT s JOIN REGISTRATION r ON s.ID = r.student_id WHERE r.course_code = ?", (course.course_code,))
            for row in cursor:
                students[course_name].append(f"{row[0]} {row[1]}")
        return students

# Define the Admin class, inheriting from User
class Admin(User):
    def __init__(self, username, password, role='admin'):
        super().__init__(username, password, role)

    def add_course(self, course_code, course_name, instructor, schedule, department, semester, year, credits):
        database.execute("INSERT INTO COURSE (CRN, TITLE, DEPARTMENT, TIME, DAYS, SEMESTER, YEAR, CREDITS, instructor_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, (SELECT ID FROM INSTRUCTOR WHERE EMAIL = ?))", 
                         (course_code, course_name, department, schedule, 'N/A', semester, year, credits, instructor))
        database.commit()
        return "Course added to system."

    def remove_course(self, course_code):
        database.execute("DELETE FROM COURSE WHERE CRN = ?", (course_code,))
        database.commit()
        return "Course removed from system."

    def add_user(self, user_id, username, password, role, name, surname, gradyear='', major='', email='', title='', hireyear=0, dept='', office=''):
        hashed_password = hash_password(password)
        try:
            database.execute("INSERT INTO USER (ID, username, password, role) VALUES (?, ?, ?, ?)", (user_id, username, hashed_password, role))
            if role == 'student':
                database.execute("INSERT INTO STUDENT (ID, NAME, SURNAME, USERNAME, GRADYEAR, MAJOR, EMAIL) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                                 (user_id, name, surname, username, gradyear, major, email))
            elif role == 'instructor':
                database.execute("INSERT INTO INSTRUCTOR (ID, NAME, SURNAME, TITLE, HIREYEAR, DEPT, EMAIL) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                                 (user_id, name, surname, title, hireyear, dept, email))
            elif role == 'admin':
                database.execute("INSERT INTO ADMIN (ID, NAME, SURNAME, TITLE, OFFICE, EMAIL) VALUES (?, ?, ?, ?, ?, ?)", 
                                 (user_id, name, surname, title, office, email))
            database.commit()
            return "User added successfully."
        except sql.IntegrityError:
            return "ID number or username already exists. Try again."

    def remove_user(self, username):
        database.execute("DELETE FROM USER WHERE username = ?", (username,))
        database.commit()
        return "User removed successfully."

    def add_student_to_course(self, student_username, course_code):
        database.execute("INSERT INTO REGISTRATION (student_id, course_code) VALUES ((SELECT ID FROM USER WHERE username = ?), ?)", (student_username, course_code))
        database.commit()
        return "Student added to course."

    def remove_student_from_course(self, student_username, course_code):
        database.execute("DELETE FROM REGISTRATION WHERE student_id = (SELECT ID FROM USER WHERE username = ?) AND course_code = ?", (student_username, course_code))
        database.commit()
        return "Student removed from course."

    def view_all_courses(self):
        courses = []
        cursor = database.execute("SELECT CRN, TITLE, DEPARTMENT, TIME, DAYS, SEMESTER, YEAR, CREDITS FROM COURSE")
        for row in cursor:
            courses.append(f"{row[0]}: {row[1]}, {row[2]}, {row[3]}, {row[4]}, {row[5]}, {row[6]}, {row[7]} credits")
        return courses

    def view_roster(self, course_code):
        roster = []
        cursor = database.execute("SELECT s.NAME, s.SURNAME FROM STUDENT s JOIN REGISTRATION r ON s.ID = r.student_id WHERE r.course_code = ?", (course_code,))
        for row in cursor:
            roster.append(f"{row[0]} {row[1]}")
        return roster

# GUI Implementation
class RegistrationSystemApp:
    def __init__(self, root):
        self.root = root
        self.root.title("College Registration System")

        # Main menu
        self.main_menu()

    def main_menu(self):
        self.clear_screen()
        tk.Label(self.root, text="Main Menu", font=("Helvetica", 16)).pack(pady=10)
        tk.Button(self.root, text="Login", command=self.login_screen).pack(pady=5)
        tk.Button(self.root, text="Register", command=self.register_screen).pack(pady=5)
        tk.Button(self.root, text="Exit", command=self.root.quit).pack(pady=5)

    def clear_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def login_screen(self):
        self.clear_screen()
        tk.Label(self.root, text="Login", font=("Helvetica", 16)).pack(pady=10)

        role_label = tk.Label(self.root, text="Role:")
        role_label.pack(pady=5)
        self.role_entry = tk.Entry(self.root)
        self.role_entry.pack(pady=5)

        username_label = tk.Label(self.root, text="Username:")
        username_label.pack(pady=5)
        self.username_entry = tk.Entry(self.root)
        self.username_entry.pack(pady=5)

        password_label = tk.Label(self.root, text="Password:")
        password_label.pack(pady=5)
        self.password_entry = tk.Entry(self.root, show="*")
        self.password_entry.pack(pady=5)

        tk.Button(self.root, text="Login", command=self.login).pack(pady=5)
        tk.Button(self.root, text="Back", command=self.main_menu).pack(pady=5)

    def register_screen(self):
        self.clear_screen()
        tk.Label(self.root, text="Register", font=("Helvetica", 16)).pack(pady=10)

        role_label = tk.Label(self.root, text="Role:")
        role_label.pack(pady=5)
        self.role_entry = tk.Entry(self.root)
        self.role_entry.pack(pady=5)

        username_label = tk.Label(self.root, text="Username:")
        username_label.pack(pady=5)
        self.username_entry = tk.Entry(self.root)
        self.username_entry.pack(pady=5)

        password_label = tk.Label(self.root, text="Password:")
        password_label.pack(pady=5)
        self.password_entry = tk.Entry(self.root, show="*")
        self.password_entry.pack(pady=5)

        tk.Button(self.root, text="Register", command=self.register).pack(pady=5)
        tk.Button(self.root, text="Back", command=self.main_menu).pack(pady=5)

    def login(self):
        role = self.role_entry.get().lower()
        username = self.username_entry.get()
        password = self.password_entry.get()

        if role == "student":
            user = Student(username, password)
        elif role == "instructor":
            user = Instructor(username, password)
        elif role == "admin":
            user = Admin(username, password)
        else:
            messagebox.showerror("Error", "Invalid role. Try again.")
            return

        if user.authenticate():
            messagebox.showinfo("Success", f"Login successful. Welcome, {username}!")
            self.user = user
            if role == "student":
                self.student_menu()
            elif role == "instructor":
                self.instructor_menu()
            elif role == "admin":
                self.admin_menu()
        else:
            messagebox.showerror("Error", "Login failed. Invalid credentials.")
      
    def register(self):
        role = self.role_entry.get().lower()
        username = self.username_entry.get()
        password = self.password_entry.get()

        hashed_password = hash_password(password)
        try:
            database.execute("INSERT INTO USER (username, password, role) VALUES (?, ?, ?)", (username, hashed_password, role))
            if role == 'student':
                name = simpledialog.askstring("Input", "Enter student's first name:")
                surname = simpledialog.askstring("Input", "Enter student's last name:")
                gradyear = simpledialog.askstring("Input", "Enter student's graduation year:")
                major = simpledialog.askstring("Input", "Enter student's major:")
                email = simpledialog.askstring("Input", "Enter student's email:")
                database.execute("INSERT INTO STUDENT (NAME, SURNAME, USERNAME, GRADYEAR, MAJOR, EMAIL) VALUES (?, ?, ?, ?, ?, ?)", 
                                (name, surname, username, gradyear, major, email))
            elif role == 'instructor':
                name = simpledialog.askstring("Input", "Enter instructor's first name:")
                surname = simpledialog.askstring("Input", "Enter instructor's last name:")
                title = simpledialog.askstring("Input", "Enter instructor's title:")
                hireyear = simpledialog.askinteger("Input", "Enter instructor's hire year:")
                dept = simpledialog.askstring("Input", "Enter instructor's department:")
                email = simpledialog.askstring("Input", "Enter instructor's email:")
                database.execute("INSERT INTO INSTRUCTOR (NAME, SURNAME, USERNAME, TITLE, HIREYEAR, DEPT, EMAIL) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                                (name, surname, username, title, hireyear, dept, email))
            elif role == 'admin':
                name = simpledialog.askstring("Input", "Enter admin's first name:")
                surname = simpledialog.askstring("Input", "Enter admin's last name:")
                title = simpledialog.askstring("Input", "Enter admin's title:")
                office = simpledialog.askstring("Input", "Enter admin's office:")
                email = simpledialog.askstring("Input", "Enter admin's email:")
                database.execute("INSERT INTO ADMIN (NAME, SURNAME, TITLE, OFFICE, EMAIL) VALUES (?, ?, ?, ?, ?)", 
                                (name, surname, title, office, email))
            database.commit()
            messagebox.showinfo("Success", "Registration successful.")
            self.main_menu()
        except sql.IntegrityError:
            messagebox.showerror("Error", "Username already exists. Try again.")

    # def register(self):
    #     role = self.role_entry.get().lower()
    #     username = self.username_entry.get()
    #     password = self.password_entry.get()

    #     hashed_password = hash_password(password)
    #     try:
    #         database.execute("INSERT INTO USER (username, password, role) VALUES (?, ?, ?)", (username, hashed_password, role))
    #         name = simpledialog.askstring("Input", "Enter first name:")
    #         surname = simpledialog.askstring("Input", "Enter last name:")
    #         if role == 'student':
    #             gradyear = simpledialog.askstring("Input", "Enter graduation year:")
    #             major = simpledialog.askstring("Input", "Enter major:")
    #             email = simpledialog.askstring("Input", "Enter email:")
    #             database.execute("INSERT INTO STUDENT (NAME, SURNAME, USERNAME, GRADYEAR, MAJOR, EMAIL) VALUES (?, ?, ?, ?, ?, ?)", 
    #                              (name, surname, username, gradyear, major, email))
    #         elif role == 'instructor':
    #             title = simpledialog.askstring("Input", "Enter title:")
    #             hireyear = simpledialog.askinteger("Input", "Enter hire year:")
    #             dept = simpledialog.askstring("Input", "Enter department:")
    #             email = simpledialog.askstring("Input", "Enter email:")
    #             database.execute("INSERT INTO INSTRUCTOR (NAME, SURNAME, USERNAME, TITLE, HIREYEAR, DEPT, EMAIL) VALUES (?, ?, ?, ?, ?, ?, ?)", 
    #                              (name, surname, username, title, hireyear, dept, email))
    #         elif role == 'admin':
    #             title = simpledialog.askstring("Input", "Enter title:")
    #             office = simpledialog.askstring("Input", "Enter office:")
    #             email = simpledialog.askstring("Input", "Enter email:")
    #             database.execute("INSERT INTO ADMIN (NAME, SURNAME, USERNAME, TITLE, OFFICE, EMAIL) VALUES (?, ?, ?, ?, ?, ?)", 
    #                              (name, surname, username, title, office, email))
    #         database.commit()
    #         messagebox.showinfo("Success", "Registration successful.")
    #         self.main_menu()
    #     except sql.IntegrityError:
    #         messagebox.showerror("Error", "Username already exists. Try again.")

    def student_menu(self):
        self.clear_screen()
        tk.Label(self.root, text="Student Menu", font=("Helvetica", 16)).pack(pady=10)
        tk.Button(self.root, text="Register for classes", command=self.register_for_classes).pack(pady=5)
        tk.Button(self.root, text="See schedule", command=self.see_schedule).pack(pady=5)
        tk.Button(self.root, text="Edit schedule", command=self.edit_schedule).pack(pady=5)
        tk.Button(self.root, text="Logout", command=self.main_menu).pack(pady=5)

    def register_for_classes(self):
        courses = self.user.register_for_classes()
        course_list = "\n".join(courses)
        course_code = simpledialog.askinteger("Input", f"Available Classes:\n{course_list}\nEnter the course code you want to register for:")
        if course_code:
            result = self.user.add_course_to_schedule(course_code)
            messagebox.showinfo("Result", result)

    def see_schedule(self):
        schedule = self.user.see_schedule()
        schedule_list = "\n".join([f"{course.course_code}: {course.course_name} - {course.instructor} - {course.schedule}" for course in schedule])
        messagebox.showinfo("Schedule", f"Your Schedule:\n{schedule_list}")

    def edit_schedule(self):
        action = simpledialog.askstring("Input", "Enter 'add' to add a course or 'drop' to drop a course:").lower()
        if action in ["add", "drop"]:
            course_code = simpledialog.askinteger("Input", "Enter the course code:")
            if course_code:
                result = self.user.edit_schedule(action, course_code)
                messagebox.showinfo("Result", result)
        else:
            messagebox.showerror("Error", "Invalid action.")

    def instructor_menu(self):
        self.clear_screen()
        tk.Label(self.root, text="Instructor Menu", font=("Helvetica", 16)).pack(pady=10)
        tk.Button(self.root, text="View schedule", command=self.view_schedule).pack(pady=5)
        tk.Button(self.root, text="View registered students", command=self.view_registered_students).pack(pady=5)
        tk.Button(self.root, text="Logout", command=self.main_menu).pack(pady=5)

    def view_schedule(self):
        courses = self.user.view_schedule()
        course_list = "\n".join([f"{course.course_code}: {course.course_name} - {course.instructor} - {course.schedule}" for course in courses.values()])
        messagebox.showinfo("Schedule", f"Your Schedule:\n{course_list}")

    def view_registered_students(self):
        students = self.user.view_registered_students()
        for course_name, student_list in students.items():
            student_names = "\n".join(student_list)
            messagebox.showinfo("Registered Students", f"Course: {course_name}\nStudents:\n{student_names}")

    def admin_menu(self):
        self.clear_screen()
        tk.Label(self.root, text="Admin Menu", font=("Helvetica", 16)).pack(pady=10)
        tk.Button(self.root, text="Add course", command=self.add_course).pack(pady=5)
        tk.Button(self.root, text="Remove course", command=self.remove_course).pack(pady=5)
        tk.Button(self.root, text="Add user", command=self.add_user).pack(pady=5)
        tk.Button(self.root, text="Remove user", command=self.remove_user).pack(pady=5)
        tk.Button(self.root, text="Add student to course", command=self.add_student_to_course).pack(pady=5)
        tk.Button(self.root, text="Remove student from course", command=self.remove_student_from_course).pack(pady=5)
        tk.Button(self.root, text="View all courses", command=self.view_all_courses).pack(pady=5)
        tk.Button(self.root, text="View roster", command=self.view_roster).pack(pady=5)
        tk.Button(self.root, text="Logout", command=self.main_menu).pack(pady=5)

    def add_course(self):
        course_code = simpledialog.askinteger("Input", "Enter course code:")
        course_name = simpledialog.askstring("Input", "Enter course name:")
        instructor = simpledialog.askstring("Input", "Enter instructor username:")
        schedule = simpledialog.askstring("Input", "Enter schedule:")
        department = simpledialog.askstring("Input", "Enter department:")
        semester = simpledialog.askstring("Input", "Enter semester:")
        year = simpledialog.askinteger("Input", "Enter year:")
        credits = simpledialog.askinteger("Input", "Enter credits:")
        result = self.user.add_course(course_code, course_name, instructor, schedule, department, semester, year, credits)
        messagebox.showinfo("Result", result)

    def remove_course(self):
        course_code = simpledialog.askinteger("Input", "Enter course code to remove:")
        if course_code:
            result = self.user.remove_course(course_code)
            messagebox.showinfo("Result", result)

    def add_user(self):
        user_id = simpledialog.askinteger("Input", "Enter new ID number:")
        username = simpledialog.askstring("Input", "Enter new username:")
        password = simpledialog.askstring("Input", "Create a password:")
        role = simpledialog.askstring("Input", "Enter role (student, instructor, admin):").lower()
        name = simpledialog.askstring("Input", "Enter first name:")
        surname = simpledialog.askstring("Input", "Enter last name:")
        gradyear = major = email = title = hireyear = dept = office = ''
        if role == 'student':
            gradyear = simpledialog.askstring("Input", "Enter graduation year:")
            major = simpledialog.askstring("Input", "Enter major:")
            email = simpledialog.askstring("Input", "Enter email:")
        elif role == 'instructor':
            title = simpledialog.askstring("Input", "Enter title:")
            hireyear = simpledialog.askinteger("Input", "Enter hire year:")
            dept = simpledialog.askstring("Input", "Enter department:")
            email = simpledialog.askstring("Input", "Enter email:")
        elif role == 'admin':
            title = simpledialog.askstring("Input", "Enter title:")
            office = simpledialog.askstring("Input", "Enter office:")
            email = simpledialog.askstring("Input", "Enter email:")
        result = self.user.add_user(user_id, username, password, role, name, surname, gradyear, major, email, title, hireyear, dept, office)
        messagebox.showinfo("Result", result)

    def remove_user(self):
        username = simpledialog.askstring("Input", "Enter username to remove:")
        if username:
            result = self.user.remove_user(username)
            messagebox.showinfo("Result", result)

    def add_student_to_course(self):
        student_username = simpledialog.askstring("Input", "Enter student username:")
        course_code = simpledialog.askinteger("Input", "Enter course code:")
        if student_username and course_code:
            result = self.user.add_student_to_course(student_username, course_code)
            messagebox.showinfo("Result", result)

    def remove_student_from_course(self):
        student_username = simpledialog.askstring("Input", "Enter student username:")
        course_code = simpledialog.askinteger("Input", "Enter course code:")
        if student_username and course_code:
            result = self.user.remove_student_from_course(student_username, course_code)
            messagebox.showinfo("Result", result)

    def view_all_courses(self):
        courses = self.user.view_all_courses()
        course_list = "\n".join(courses)
        messagebox.showinfo("Courses", f"All Courses:\n{course_list}")

    def view_roster(self):
        course_code = simpledialog.askinteger("Input", "Enter course code:")
        if course_code:
            roster = self.user.view_roster(course_code)
            roster_list = "\n".join(roster)
            messagebox.showinfo("Roster", f"Roster for Course Code {course_code}:\n{roster_list}")

if __name__ == "__main__":
    root = tk.Tk()
    app = RegistrationSystemApp(root)
    root.mainloop()

#Works but doesnt add users to correct database table
#doesnt prompt instructors or admin the correct questions when they register

# import sqlite3 as sql
# import hashlib
# import tkinter as tk
# from tkinter import messagebox, simpledialog

# # Connect to the SQLite database
# database = sql.connect("LeopardWebDatabase.db")

# # Function to hash passwords
# def hash_password(password):
#     return hashlib.sha256(password.encode()).hexdigest()

# # Define the User class
# class User:
#     def __init__(self, username, password, role):
#         self.username = username
#         self.password = hash_password(password)
#         self.role = role

#     def authenticate(self):
#         cursor = database.execute("SELECT * FROM USER WHERE username = ? AND password = ?", (self.username, self.password))
#         return cursor.fetchone() is not None

# # Define the Course class
# class Course:
#     def __init__(self, course_code, course_name, instructor, schedule):
#         self.course_code = course_code
#         self.course_name = course_name
#         self.instructor = instructor
#         self.schedule = schedule

# # Define the Student class, inheriting from User
# class Student(User):
#     def __init__(self, username, password, role='student'):
#         super().__init__(username, password, role)
#         self.schedule = []

#     def register_for_classes(self):
#         courses = []
#         cursor = database.execute("SELECT CRN, TITLE, DEPARTMENT, TIME, DAYS, SEMESTER, YEAR, CREDITS FROM COURSE")
#         for row in cursor:
#             courses.append(f"{row[0]}: {row[1]}, {row[2]}, {row[3]}, {row[4]}, {row[5]}, {row[6]}, {row[7]} credits")
#         return courses

#     def add_course_to_schedule(self, course_code):
#         cursor = database.execute("SELECT * FROM COURSE WHERE CRN = ?", (course_code,))
#         course = cursor.fetchone()
#         if course:
#             self.schedule.append(Course(course[0], course[1], course[8], course[3]))
#             database.execute("INSERT INTO REGISTRATION (student_id, course_code) VALUES ((SELECT ID FROM USER WHERE username = ?), ?)", (self.username, course_code))
#             database.commit()
#             return "Course added to schedule and database updated."
#         else:
#             return "Invalid course code."

#     def see_schedule(self):
#         self.schedule.clear()
#         cursor = database.execute("""
#             SELECT c.CRN, c.TITLE, i.NAME, c.TIME
#             FROM COURSE c
#             JOIN REGISTRATION r ON c.CRN = r.course_code
#             JOIN USER u ON u.ID = r.student_id
#             JOIN INSTRUCTOR i ON c.instructor_id = i.ID
#             WHERE u.username = ?
#         """, (self.username,))
#         for row in cursor:
#             course = Course(row[0], row[1], row[2], row[3])
#             self.schedule.append(course)
#         return self.schedule

#     def edit_schedule(self, action, course_code):
#         if action == "add":
#             return self.add_course_to_schedule(course_code)
#         elif action == "drop":
#             self.schedule = [course for course in self.schedule if course.course_code != course_code]
#             database.execute("DELETE FROM REGISTRATION WHERE student_id = (SELECT ID FROM USER WHERE username = ?) AND course_code = ?", (self.username, course_code))
#             database.commit()
#             return "Course dropped from schedule."
#         else:
#             return "Invalid action."

# # Define the Instructor class, inheriting from User
# class Instructor(User):
#     def __init__(self, username, password, role='instructor'):
#         super().__init__(username, password, role)
#         self.courses_taught = {}

#     def assign_course(self, course):
#         self.courses_taught[course.course_name] = course

#     def view_schedule(self):
#         self.courses_taught.clear()
#         cursor = database.execute("SELECT * FROM COURSE WHERE instructor = ?", (self.username,))
#         for row in cursor:
#             course = Course(row[0], row[1], row[2], row[3])
#             self.courses_taught[course.course_name] = course
#         return self.courses_taught

#     def view_registered_students(self):
#         students = {}
#         for course_name, course in self.courses_taught.items():
#             students[course_name] = []
#             cursor = database.execute("SELECT s.NAME, s.SURNAME FROM STUDENT s JOIN REGISTRATION r ON s.ID = r.student_id WHERE r.course_code = ?", (course.course_code,))
#             for row in cursor:
#                 students[course_name].append(f"{row[0]} {row[1]}")
#         return students

# # Define the Admin class, inheriting from User
# class Admin(User):
#     def __init__(self, username, password, role='admin'):
#         super().__init__(username, password, role)

#     def add_course(self, course_code, course_name, instructor, schedule, department, semester, year, credits):
#         database.execute("INSERT INTO COURSE (CRN, TITLE, DEPARTMENT, TIME, DAYS, SEMESTER, YEAR, CREDITS, instructor_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, (SELECT ID FROM INSTRUCTOR WHERE EMAIL = ?))", 
#                          (course_code, course_name, department, schedule, 'N/A', semester, year, credits, instructor))
#         database.commit()
#         return "Course added to system."

#     def remove_course(self, course_code):
#         database.execute("DELETE FROM COURSE WHERE CRN = ?", (course_code,))
#         database.commit()
#         return "Course removed from system."

#     def add_user(self, user_id, username, password, role, name, surname, gradyear='', major='', email='', title='', hireyear=0, dept='', office=''):
#         hashed_password = hash_password(password)
#         try:
#             database.execute("INSERT INTO USER (ID, username, password, role) VALUES (?, ?, ?, ?)", (user_id, username, hashed_password, role))
#             if role == 'student':
#                 database.execute("INSERT INTO STUDENT (ID, NAME, SURNAME, USERNAME, GRADYEAR, MAJOR, EMAIL) VALUES (?, ?, ?, ?, ?, ?, ?)", 
#                                  (user_id, name, surname, username, gradyear, major, email))
#             elif role == 'instructor':
#                 database.execute("INSERT INTO INSTRUCTOR (ID, NAME, SURNAME, TITLE, HIREYEAR, DEPT, EMAIL) VALUES (?, ?, ?, ?, ?, ?, ?)", 
#                                  (user_id, name, surname, title, hireyear, dept, email))
#             elif role == 'admin':
#                 database.execute("INSERT INTO ADMIN (ID, NAME, SURNAME, TITLE, OFFICE, EMAIL) VALUES (?, ?, ?, ?, ?, ?)", 
#                                  (user_id, name, surname, title, office, email))
#             database.commit()
#             return "User added successfully."
#         except sql.IntegrityError:
#             return "ID number or username already exists. Try again."

#     def remove_user(self, username):
#         database.execute("DELETE FROM USER WHERE username = ?", (username,))
#         database.commit()
#         return "User removed successfully."

#     def add_student_to_course(self, student_username, course_code):
#         database.execute("INSERT INTO REGISTRATION (student_id, course_code) VALUES ((SELECT ID FROM USER WHERE username = ?), ?)", (student_username, course_code))
#         database.commit()
#         return "Student added to course."

#     def remove_student_from_course(self, student_username, course_code):
#         database.execute("DELETE FROM REGISTRATION WHERE student_id = (SELECT ID FROM USER WHERE username = ?) AND course_code = ?", (student_username, course_code))
#         database.commit()
#         return "Student removed from course."

#     def view_all_courses(self):
#         courses = []
#         cursor = database.execute("SELECT CRN, TITLE, DEPARTMENT, TIME, DAYS, SEMESTER, YEAR, CREDITS FROM COURSE")
#         for row in cursor:
#             courses.append(f"{row[0]}: {row[1]}, {row[2]}, {row[3]}, {row[4]}, {row[5]}, {row[6]}, {row[7]} credits")
#         return courses

#     def view_roster(self, course_code):
#         roster = []
#         cursor = database.execute("SELECT s.NAME, s.SURNAME FROM STUDENT s JOIN REGISTRATION r ON s.ID = r.student_id WHERE r.course_code = ?", (course_code,))
#         for row in cursor:
#             roster.append(f"{row[0]} {row[1]}")
#         return roster

# # GUI Implementation
# class RegistrationSystemApp:
#     def __init__(self, root):
#         self.root = root
#         self.root.title("College Registration System")

#         # Main menu
#         self.main_menu()

#     def main_menu(self):
#         self.clear_screen()
#         tk.Label(self.root, text="Main Menu", font=("Helvetica", 16)).pack(pady=10)
#         tk.Button(self.root, text="Login", command=self.login_screen).pack(pady=5)
#         tk.Button(self.root, text="Register", command=self.register_screen).pack(pady=5)
#         tk.Button(self.root, text="Exit", command=self.root.quit).pack(pady=5)

#     def clear_screen(self):
#         for widget in self.root.winfo_children():
#             widget.destroy()

#     def login_screen(self):
#         self.clear_screen()
#         tk.Label(self.root, text="Login", font=("Helvetica", 16)).pack(pady=10)

#         role_label = tk.Label(self.root, text="Role:")
#         role_label.pack(pady=5)
#         self.role_entry = tk.Entry(self.root)
#         self.role_entry.pack(pady=5)

#         username_label = tk.Label(self.root, text="Username:")
#         username_label.pack(pady=5)
#         self.username_entry = tk.Entry(self.root)
#         self.username_entry.pack(pady=5)

#         password_label = tk.Label(self.root, text="Password:")
#         password_label.pack(pady=5)
#         self.password_entry = tk.Entry(self.root, show="*")
#         self.password_entry.pack(pady=5)

#         tk.Button(self.root, text="Login", command=self.login).pack(pady=5)
#         tk.Button(self.root, text="Back", command=self.main_menu).pack(pady=5)

#     def register_screen(self):
#         self.clear_screen()
#         tk.Label(self.root, text="Register", font=("Helvetica", 16)).pack(pady=10)

#         role_label = tk.Label(self.root, text="Role:")
#         role_label.pack(pady=5)
#         self.role_entry = tk.Entry(self.root)
#         self.role_entry.pack(pady=5)

#         username_label = tk.Label(self.root, text="Username:")
#         username_label.pack(pady=5)
#         self.username_entry = tk.Entry(self.root)
#         self.username_entry.pack(pady=5)

#         password_label = tk.Label(self.root, text="Password:")
#         password_label.pack(pady=5)
#         self.password_entry = tk.Entry(self.root, show="*")
#         self.password_entry.pack(pady=5)

#         tk.Button(self.root, text="Register", command=self.register).pack(pady=5)
#         tk.Button(self.root, text="Back", command=self.main_menu).pack(pady=5)

#     def login(self):
#         role = self.role_entry.get().lower()
#         username = self.username_entry.get()
#         password = self.password_entry.get()

#         if role == "student":
#             user = Student(username, password)
#         elif role == "instructor":
#             user = Instructor(username, password)
#         elif role == "admin":
#             user = Admin(username, password)
#         else:
#             messagebox.showerror("Error", "Invalid role. Try again.")
#             return

#         if user.authenticate():
#             messagebox.showinfo("Success", f"Login successful. Welcome, {username}!")
#             self.user = user
#             if role == "student":
#                 self.student_menu()
#             elif role == "instructor":
#                 self.instructor_menu()
#             elif role == "admin":
#                 self.admin_menu()
#         else:
#             messagebox.showerror("Error", "Login failed. Invalid credentials.")

#     def register(self):
#         role = self.role_entry.get().lower()
#         username = self.username_entry.get()
#         password = self.password_entry.get()

#         hashed_password = hash_password(password)
#         try:
#             database.execute("INSERT INTO USER (username, password, role) VALUES (?, ?, ?)", (username, hashed_password, role))
#             if role == 'student':
#                 name = simpledialog.askstring("Input", "Enter student's first name:")
#                 surname = simpledialog.askstring("Input", "Enter student's last name:")
#                 gradyear = simpledialog.askstring("Input", "Enter student's graduation year:")
#                 major = simpledialog.askstring("Input", "Enter student's major:")
#                 email = simpledialog.askstring("Input", "Enter student's email:")
#                 database.execute("INSERT INTO STUDENT (NAME, SURNAME, USERNAME, GRADYEAR, MAJOR, EMAIL) VALUES (?, ?, ?, ?, ?, ?)", 
#                                  (name, surname, username, gradyear, major, email))
#             database.commit()
#             messagebox.showinfo("Success", "Registration successful.")
#             self.main_menu()
#         except sql.IntegrityError:
#             messagebox.showerror("Error", "Username already exists. Try again.")

#     def student_menu(self):
#         self.clear_screen()
#         tk.Label(self.root, text="Student Menu", font=("Helvetica", 16)).pack(pady=10)
#         tk.Button(self.root, text="Register for classes", command=self.register_for_classes).pack(pady=5)
#         tk.Button(self.root, text="See schedule", command=self.see_schedule).pack(pady=5)
#         tk.Button(self.root, text="Edit schedule", command=self.edit_schedule).pack(pady=5)
#         tk.Button(self.root, text="Logout", command=self.main_menu).pack(pady=5)

#     def register_for_classes(self):
#         courses = self.user.register_for_classes()
#         course_list = "\n".join(courses)
#         course_code = simpledialog.askinteger("Input", f"Available Classes:\n{course_list}\nEnter the course code you want to register for:")
#         if course_code:
#             result = self.user.add_course_to_schedule(course_code)
#             messagebox.showinfo("Result", result)

#     def see_schedule(self):
#         schedule = self.user.see_schedule()
#         schedule_list = "\n".join([f"{course.course_code}: {course.course_name} - {course.instructor} - {course.schedule}" for course in schedule])
#         messagebox.showinfo("Schedule", f"Your Schedule:\n{schedule_list}")

#     def edit_schedule(self):
#         action = simpledialog.askstring("Input", "Enter 'add' to add a course or 'drop' to drop a course:").lower()
#         if action in ["add", "drop"]:
#             course_code = simpledialog.askinteger("Input", "Enter the course code:")
#             if course_code:
#                 result = self.user.edit_schedule(action, course_code)
#                 messagebox.showinfo("Result", result)
#         else:
#             messagebox.showerror("Error", "Invalid action.")

#     def instructor_menu(self):
#         self.clear_screen()
#         tk.Label(self.root, text="Instructor Menu", font=("Helvetica", 16)).pack(pady=10)
#         tk.Button(self.root, text="View schedule", command=self.view_schedule).pack(pady=5)
#         tk.Button(self.root, text="View registered students", command=self.view_registered_students).pack(pady=5)
#         tk.Button(self.root, text="Logout", command=self.main_menu).pack(pady=5)

#     def view_schedule(self):
#         courses = self.user.view_schedule()
#         course_list = "\n".join([f"{course.course_code}: {course.course_name} - {course.instructor} - {course.schedule}" for course in courses.values()])
#         messagebox.showinfo("Schedule", f"Your Schedule:\n{course_list}")

#     def view_registered_students(self):
#         students = self.user.view_registered_students()
#         for course_name, student_list in students.items():
#             student_names = "\n".join(student_list)
#             messagebox.showinfo("Registered Students", f"Course: {course_name}\nStudents:\n{student_names}")

#     def admin_menu(self):
#         self.clear_screen()
#         tk.Label(self.root, text="Admin Menu", font=("Helvetica", 16)).pack(pady=10)
#         tk.Button(self.root, text="Add course", command=self.add_course).pack(pady=5)
#         tk.Button(self.root, text="Remove course", command=self.remove_course).pack(pady=5)
#         tk.Button(self.root, text="Add user", command=self.add_user).pack(pady=5)
#         tk.Button(self.root, text="Remove user", command=self.remove_user).pack(pady=5)
#         tk.Button(self.root, text="Add student to course", command=self.add_student_to_course).pack(pady=5)
#         tk.Button(self.root, text="Remove student from course", command=self.remove_student_from_course).pack(pady=5)
#         tk.Button(self.root, text="View all courses", command=self.view_all_courses).pack(pady=5)
#         tk.Button(self.root, text="View roster", command=self.view_roster).pack(pady=5)
#         tk.Button(self.root, text="Logout", command=self.main_menu).pack(pady=5)

#     def add_course(self):
#         course_code = simpledialog.askinteger("Input", "Enter course code:")
#         course_name = simpledialog.askstring("Input", "Enter course name:")
#         instructor = simpledialog.askstring("Input", "Enter instructor username:")
#         schedule = simpledialog.askstring("Input", "Enter schedule:")
#         department = simpledialog.askstring("Input", "Enter department:")
#         semester = simpledialog.askstring("Input", "Enter semester:")
#         year = simpledialog.askinteger("Input", "Enter year:")
#         credits = simpledialog.askinteger("Input", "Enter credits:")
#         result = self.user.add_course(course_code, course_name, instructor, schedule, department, semester, year, credits)
#         messagebox.showinfo("Result", result)

#     def remove_course(self):
#         course_code = simpledialog.askinteger("Input", "Enter course code to remove:")
#         if course_code:
#             result = self.user.remove_course(course_code)
#             messagebox.showinfo("Result", result)

#     def add_user(self):
#         user_id = simpledialog.askinteger("Input", "Enter new ID number:")
#         username = simpledialog.askstring("Input", "Enter new username:")
#         password = simpledialog.askstring("Input", "Create a password:")
#         role = simpledialog.askstring("Input", "Enter role (student, instructor, admin):").lower()
#         name = simpledialog.askstring("Input", "Enter first name:")
#         surname = simpledialog.askstring("Input", "Enter last name:")
#         gradyear = major = email = title = hireyear = dept = office = ''
#         if role == 'student':
#             gradyear = simpledialog.askstring("Input", "Enter graduation year:")
#             major = simpledialog.askstring("Input", "Enter major:")
#             email = simpledialog.askstring("Input", "Enter email:")
#         elif role == 'instructor':
#             title = simpledialog.askstring("Input", "Enter title:")
#             hireyear = simpledialog.askinteger("Input", "Enter hire year:")
#             dept = simpledialog.askstring("Input", "Enter department:")
#             email = simpledialog.askstring("Input", "Enter email:")
#         elif role == 'admin':
#             title = simpledialog.askstring("Input", "Enter title:")
#             office = simpledialog.askstring("Input", "Enter office:")
#             email = simpledialog.askstring("Input", "Enter email:")
#         result = self.user.add_user(user_id, username, password, role, name, surname, gradyear, major, email, title, hireyear, dept, office)
#         messagebox.showinfo("Result", result)

#     def remove_user(self):
#         username = simpledialog.askstring("Input", "Enter username to remove:")
#         if username:
#             result = self.user.remove_user(username)
#             messagebox.showinfo("Result", result)

#     def add_student_to_course(self):
#         student_username = simpledialog.askstring("Input", "Enter student username:")
#         course_code = simpledialog.askinteger("Input", "Enter course code:")
#         if student_username and course_code:
#             result = self.user.add_student_to_course(student_username, course_code)
#             messagebox.showinfo("Result", result)

#     def remove_student_from_course(self):
#         student_username = simpledialog.askstring("Input", "Enter student username:")
#         course_code = simpledialog.askinteger("Input", "Enter course code:")
#         if student_username and course_code:
#             result = self.user.remove_student_from_course(student_username, course_code)
#             messagebox.showinfo("Result", result)

#     def view_all_courses(self):
#         courses = self.user.view_all_courses()
#         course_list = "\n".join(courses)
#         messagebox.showinfo("Courses", f"All Courses:\n{course_list}")

#     def view_roster(self):
#         course_code = simpledialog.askinteger("Input", "Enter course code:")
#         if course_code:
#             roster = self.user.view_roster(course_code)
#             roster_list = "\n".join(roster)
#             messagebox.showinfo("Roster", f"Roster for Course Code {course_code}:\n{roster_list}")

# if __name__ == "__main__":
#     root = tk.Tk()
#     app = RegistrationSystemApp(root)
#     root.mainloop()

#----------------------------------------------------------------------------------------------------------------------------

# import sqlite3 as sql
# import hashlib
# import tkinter as tk
# from tkinter import messagebox, simpledialog

# # Connect to the SQLite database
# database = sql.connect("LeopardWebDatabase.db")

# # Function to hash passwords
# def hash_password(password):
#     return hashlib.sha256(password.encode()).hexdigest()

# # Define the User class
# class User:
#     def __init__(self, username, password, role):
#         self.username = username
#         self.password = hash_password(password)
#         self.role = role

#     def authenticate(self):
#         cursor = database.execute("SELECT * FROM USER WHERE username = ? AND password = ?", (self.username, self.password))
#         return cursor.fetchone() is not None

# # Define the Course class
# class Course:
#     def __init__(self, course_code, course_name, instructor, schedule):
#         self.course_code = course_code
#         self.course_name = course_name
#         self.instructor = instructor
#         self.schedule = schedule

# # Define the Student class, inheriting from User
# class Student(User):
#     def __init__(self, username, password, role='student'):
#         super().__init__(username, password, role)
#         self.schedule = []

#     def register_for_classes(self):
#         courses = []
#         cursor = database.execute("SELECT CRN, TITLE, DEPARTMENT, TIME, DAYS, SEMESTER, YEAR, CREDITS FROM COURSE")
#         for row in cursor:
#             courses.append(f"{row[0]}: {row[1]}, {row[2]}, {row[3]}, {row[4]}, {row[5]}, {row[6]}, {row[7]} credits")
#         return courses

#     def add_course_to_schedule(self, course_code):
#         cursor = database.execute("SELECT * FROM COURSE WHERE CRN = ?", (course_code,))
#         course = cursor.fetchone()
#         if course:
#             self.schedule.append(Course(course[0], course[1], course[8], course[3]))
#             database.execute("INSERT INTO REGISTRATION (student_id, course_code) VALUES ((SELECT ID FROM USER WHERE username = ?), ?)", (self.username, course_code))
#             database.commit()
#             return "Course added to schedule and database updated."
#         else:
#             return "Invalid course code."

#     def see_schedule(self):
#         self.schedule.clear()
#         cursor = database.execute("""
#             SELECT c.CRN, c.TITLE, i.NAME, c.TIME
#             FROM COURSE c
#             JOIN REGISTRATION r ON c.CRN = r.course_code
#             JOIN USER u ON u.ID = r.student_id
#             JOIN INSTRUCTOR i ON c.instructor_id = i.ID
#             WHERE u.username = ?
#         """, (self.username,))
#         for row in cursor:
#             course = Course(row[0], row[1], row[2], row[3])
#             self.schedule.append(course)
#         return self.schedule

#     def edit_schedule(self, action, course_code):
#         if action == "add":
#             return self.add_course_to_schedule(course_code)
#         elif action == "drop":
#             self.schedule = [course for course in self.schedule if course.course_code != course_code]
#             database.execute("DELETE FROM REGISTRATION WHERE student_id = (SELECT ID FROM USER WHERE username = ?) AND course_code = ?", (self.username, course_code))
#             database.commit()
#             return "Course dropped from schedule."
#         else:
#             return "Invalid action."

# # Define the Instructor class, inheriting from User
# class Instructor(User):
#     def __init__(self, username, password, role='instructor'):
#         super().__init__(username, password, role)
#         self.courses_taught = {}

#     def assign_course(self, course):
#         self.courses_taught[course.course_name] = course

#     def view_schedule(self):
#         self.courses_taught.clear()
#         cursor = database.execute("SELECT * FROM COURSE WHERE instructor = ?", (self.username,))
#         for row in cursor:
#             course = Course(row[0], row[1], row[2], row[3])
#             self.courses_taught[course.course_name] = course
#         return self.courses_taught

#     def view_registered_students(self):
#         students = {}
#         for course_name, course in self.courses_taught.items():
#             students[course_name] = []
#             cursor = database.execute("SELECT s.NAME, s.SURNAME FROM STUDENT s JOIN REGISTRATION r ON s.ID = r.student_id WHERE r.course_code = ?", (course.course_code,))
#             for row in cursor:
#                 students[course_name].append(f"{row[0]} {row[1]}")
#         return students

# # Define the Admin class, inheriting from User
# class Admin(User):
#     def __init__(self, username, password, role='admin'):
#         super().__init__(username, password, role)

#     def add_course(self, course_code, course_name, instructor, schedule, department, semester, year, credits):
#         database.execute("INSERT INTO COURSE (CRN, TITLE, DEPARTMENT, TIME, DAYS, SEMESTER, YEAR, CREDITS, instructor_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, (SELECT ID FROM INSTRUCTOR WHERE EMAIL = ?))", 
#                          (course_code, course_name, department, schedule, 'N/A', semester, year, credits, instructor))
#         database.commit()
#         return "Course added to system."

#     def remove_course(self, course_code):
#         database.execute("DELETE FROM COURSE WHERE CRN = ?", (course_code,))
#         database.commit()
#         return "Course removed from system."

#     def add_user(self, user_id, username, password, role, name, surname, gradyear='', major='', email='', title='', hireyear=0, dept='', office=''):
#         hashed_password = hash_password(password)
#         try:
#             database.execute("INSERT INTO USER (ID, username, password, role) VALUES (?, ?, ?, ?)", (user_id, username, hashed_password, role))
#             if role == 'student':
#                 database.execute("INSERT INTO STUDENT (ID, NAME, SURNAME, USERNAME, GRADYEAR, MAJOR, EMAIL) VALUES (?, ?, ?, ?, ?, ?, ?)", 
#                                  (user_id, name, surname, username, gradyear, major, email))
#             elif role == 'instructor':
#                 database.execute("INSERT INTO INSTRUCTOR (ID, NAME, SURNAME, TITLE, HIREYEAR, DEPT, EMAIL) VALUES (?, ?, ?, ?, ?, ?, ?)", 
#                                  (user_id, name, surname, title, hireyear, dept, email))
#             elif role == 'admin':
#                 database.execute("INSERT INTO ADMIN (ID, NAME, SURNAME, TITLE, OFFICE, EMAIL) VALUES (?, ?, ?, ?, ?, ?)", 
#                                  (user_id, name, surname, title, office, email))
#             database.commit()
#             return "User added successfully."
#         except sql.IntegrityError:
#             return "ID number or username already exists. Try again."

#     def remove_user(self, username):
#         database.execute("DELETE FROM USER WHERE username = ?", (username,))
#         database.commit()
#         return "User removed successfully."

#     def add_student_to_course(self, student_username, course_code):
#         database.execute("INSERT INTO REGISTRATION (student_id, course_code) VALUES ((SELECT ID FROM USER WHERE username = ?), ?)", (student_username, course_code))
#         database.commit()
#         return "Student added to course."

#     def remove_student_from_course(self, student_username, course_code):
#         database.execute("DELETE FROM REGISTRATION WHERE student_id = (SELECT ID FROM USER WHERE username = ?) AND course_code = ?", (student_username, course_code))
#         database.commit()
#         return "Student removed from course."

#     def view_all_courses(self):
#         courses = []
#         cursor = database.execute("SELECT CRN, TITLE, DEPARTMENT, TIME, DAYS, SEMESTER, YEAR, CREDITS FROM COURSE")
#         for row in cursor:
#             courses.append(f"{row[0]}: {row[1]}, {row[2]}, {row[3]}, {row[4]}, {row[5]}, {row[6]}, {row[7]} credits")
#         return courses

#     def view_roster(self, course_code):
#         roster = []
#         cursor = database.execute("SELECT s.NAME, s.SURNAME FROM STUDENT s JOIN REGISTRATION r ON s.ID = r.student_id WHERE r.course_code = ?", (course_code,))
#         for row in cursor:
#             roster.append(f"{row[0]} {row[1]}")
#         return roster

# # GUI Implementation
# class RegistrationSystemApp:
#     def __init__(self, root):
#         self.root = root
#         self.root.title("College Registration System")

#         # Main menu
#         self.main_menu()

#     def main_menu(self):
#         self.clear_screen()
#         tk.Label(self.root, text="Main Menu", font=("Helvetica", 16)).pack(pady=10)
#         tk.Button(self.root, text="Login", command=self.login_screen).pack(pady=5)
#         tk.Button(self.root, text="Register", command=self.register_screen).pack(pady=5)
#         tk.Button(self.root, text="Exit", command=self.root.quit).pack(pady=5)

#     def clear_screen(self):
#         for widget in self.root.winfo_children():
#             widget.destroy()

#     def login_screen(self):
#         self.clear_screen()
#         tk.Label(self.root, text="Login", font=("Helvetica", 16)).pack(pady=10)

#         role_label = tk.Label(self.root, text="Role:")
#         role_label.pack(pady=5)
#         self.role_entry = tk.Entry(self.root)
#         self.role_entry.pack(pady=5)

#         username_label = tk.Label(self.root, text="Username:")
#         username_label.pack(pady=5)
#         self.username_entry = tk.Entry(self.root)
#         self.username_entry.pack(pady=5)

#         password_label = tk.Label(self.root, text="Password:")
#         password_label.pack(pady=5)
#         self.password_entry = tk.Entry(self.root, show="*")
#         self.password_entry.pack(pady=5)

#         tk.Button(self.root, text="Login", command=self.login).pack(pady=5)
#         tk.Button(self.root, text="Back", command=self.main_menu).pack(pady=5)

#     def register_screen(self):
#         self.clear_screen()
#         tk.Label(self.root, text="Register", font=("Helvetica", 16)).pack(pady=10)

#         role_label = tk.Label(self.root, text="Role:")
#         role_label.pack(pady=5)
#         self.role_entry = tk.Entry(self.root)
#         self.role_entry.pack(pady=5)

#         username_label = tk.Label(self.root, text="Username:")
#         username_label.pack(pady=5)
#         self.username_entry = tk.Entry(self.root)
#         self.username_entry.pack(pady=5)

#         password_label = tk.Label(self.root, text="Password:")
#         password_label.pack(pady=5)
#         self.password_entry = tk.Entry(self.root, show="*")
#         self.password_entry.pack(pady=5)

#         tk.Button(self.root, text="Register", command=self.register).pack(pady=5)
#         tk.Button(self.root, text="Back", command=self.main_menu).pack(pady=5)

#     def login(self):
#         role = self.role_entry.get().lower()
#         username = self.username_entry.get()
#         password = self.password_entry.get()

#         if role == "student":
#             user = Student(username, password)
#         elif role == "instructor":
#             user = Instructor(username, password)
#         elif role == "admin":
#             user = Admin(username, password)
#         else:
#             messagebox.showerror("Error", "Invalid role. Try again.")
#             return

#         if user.authenticate():
#             messagebox.showinfo("Success", f"Login successful. Welcome, {username}!")
#             self.user = user
#             if role == "student":
#                 self.student_menu()
#             elif role == "instructor":
#                 self.instructor_menu()
#             elif role == "admin":
#                 self.admin_menu()
#         else:
#             messagebox.showerror("Error", "Login failed. Invalid credentials.")

#     def register(self):
#         role = self.role_entry.get().lower()
#         username = self.username_entry.get()
#         password = self.password_entry.get()

#         hashed_password = hash_password(password)
#         try:
#             database.execute("INSERT INTO USER (username, password, role) VALUES (?, ?, ?)", (username, hashed_password, role))
#             if role == 'student':
#                 name = simpledialog.askstring("Input", "Enter student's first name:")
#                 surname = simpledialog.askstring("Input", "Enter student's last name:")
#                 gradyear = simpledialog.askstring("Input", "Enter student's graduation year:")
#                 major = simpledialog.askstring("Input", "Enter student's major:")
#                 email = simpledialog.askstring("Input", "Enter student's email:")
#                 database.execute("INSERT INTO STUDENT (NAME, SURNAME, USERNAME, GRADYEAR, MAJOR, EMAIL) VALUES (?, ?, ?, ?, ?, ?)", 
#                                  (name, surname, username, gradyear, major, email))
#             database.commit()
#             messagebox.showinfo("Success", "Registration successful.")
#             self.main_menu()
#         except sql.IntegrityError:
#             messagebox.showerror("Error", "Username already exists. Try again.")

#     def student_menu(self):
#         self.clear_screen()
#         tk.Label(self.root, text="Student Menu", font=("Helvetica", 16)).pack(pady=10)
#         tk.Button(self.root, text="Register for classes", command=self.register_for_classes).pack(pady=5)
#         tk.Button(self.root, text="See schedule", command=self.see_schedule).pack(pady=5)
#         tk.Button(self.root, text="Edit schedule", command=self.edit_schedule).pack(pady=5)
#         tk.Button(self.root, text="Logout", command=self.main_menu).pack(pady=5)

#     def register_for_classes(self):
#         courses = self.user.register_for_classes()
#         course_list = "\n".join(courses)
#         course_code = simpledialog.askinteger("Input", f"Available Classes:\n{course_list}\nEnter the course code you want to register for:")
#         if course_code:
#             result = self.user.add_course_to_schedule(course_code)
#             messagebox.showinfo("Result", result)

#     def see_schedule(self):
#         schedule = self.user.see_schedule()
#         schedule_list = "\n".join([f"{course.course_code}: {course.course_name} - {course.instructor} - {course.schedule}" for course in schedule])
#         messagebox.showinfo("Schedule", f"Your Schedule:\n{schedule_list}")

#     def edit_schedule(self):
#         action = simpledialog.askstring("Input", "Enter 'add' to add a course or 'drop' to drop a course:").lower()
#         if action in ["add", "drop"]:
#             course_code = simpledialog.askinteger("Input", "Enter the course code:")
#             if course_code:
#                 result = self.user.edit_schedule(action, course_code)
#                 messagebox.showinfo("Result", result)
#         else:
#             messagebox.showerror("Error", "Invalid action.")

#     def instructor_menu(self):
#         self.clear_screen()
#         tk.Label(self.root, text="Instructor Menu", font=("Helvetica", 16)).pack(pady=10)
#         tk.Button(self.root, text="View schedule", command=self.view_schedule).pack(pady=5)
#         tk.Button(self.root, text="View registered students", command=self.view_registered_students).pack(pady=5)
#         tk.Button(self.root, text="Logout", command=self.main_menu).pack(pady=5)

#     def view_schedule(self):
#         courses = self.user.view_schedule()
#         course_list = "\n".join([f"{course.course_code}: {course.course_name} - {course.instructor} - {course.schedule}" for course in courses.values()])
#         messagebox.showinfo("Schedule", f"Your Schedule:\n{course_list}")

#     def view_registered_students(self):
#         students = self.user.view_registered_students()
#         for course_name, student_list in students.items():
#             student_names = "\n".join(student_list)
#             messagebox.showinfo("Registered Students", f"Course: {course_name}\nStudents:\n{student_names}")

#     def admin_menu(self):
#         self.clear_screen()
#         tk.Label(self.root, text="Admin Menu", font=("Helvetica", 16)).pack(pady=10)
#         tk.Button(self.root, text="Add course", command=self.add_course).pack(pady=5)
#         tk.Button(self.root, text="Remove course", command=self.remove_course).pack(pady=5)
#         tk.Button(self.root, text="Add user", command=self.add_user).pack(pady=5)
#         tk.Button(self.root, text="Remove user", command=self.remove_user).pack(pady=5)
#         tk.Button(self.root, text="Add student to course", command=self.add_student_to_course).pack(pady=5)
#         tk.Button(self.root, text="Remove student from course", command=self.remove_student_from_course).pack(pady=5)
#         tk.Button(self.root, text="View all courses", command=self.view_all_courses).pack(pady=5)
#         tk.Button(self.root, text="View roster", command=self.view_roster).pack(pady=5)
#         tk.Button(self.root, text="Logout", command=self.main_menu).pack(pady=5)

#     def add_course(self):
#         course_code = simpledialog.askinteger("Input", "Enter course code:")
#         course_name = simpledialog.askstring("Input", "Enter course name:")
#         instructor = simpledialog.askstring("Input", "Enter instructor username:")
#         schedule = simpledialog.askstring("Input", "Enter schedule:")
#         department = simpledialog.askstring("Input", "Enter department:")
#         semester = simpledialog.askstring("Input", "Enter semester:")
#         year = simpledialog.askinteger("Input", "Enter year:")
#         credits = simpledialog.askinteger("Input", "Enter credits:")
#         result = self.user.add_course(course_code, course_name, instructor, schedule, department, semester, year, credits)
#         messagebox.showinfo("Result", result)

#     def remove_course(self):
#         course_code = simpledialog.askinteger("Input", "Enter course code to remove:")
#         if course_code:
#             result = self.user.remove_course(course_code)
#             messagebox.showinfo("Result", result)

#     def add_user(self):
#         user_id = simpledialog.askinteger("Input", "Enter new ID number:")
#         username = simpledialog.askstring("Input", "Enter new username:")
#         password = simpledialog.askstring("Input", "Create a password:")
#         role = simpledialog.askstring("Input", "Enter role (student, instructor, admin):").lower()
#         name = simpledialog.askstring("Input", "Enter first name:")
#         surname = simpledialog.askstring("Input", "Enter last name:")
#         gradyear = major = email = title = hireyear = dept = office = ''
#         if role == 'student':
#             gradyear = simpledialog.askstring("Input", "Enter graduation year:")
#             major = simpledialog.askstring("Input", "Enter major:")
#             email = simpledialog.askstring("Input", "Enter email:")
#         elif role == 'instructor':
#             title = simpledialog.askstring("Input", "Enter title:")
#             hireyear = simpledialog.askinteger("Input", "Enter hire year:")
#             dept = simpledialog.askstring("Input", "Enter department:")
#             email = simpledialog.askstring("Input", "Enter email:")
#         elif role == 'admin':
#             title = simpledialog.askstring("Input", "Enter title:")
#             office = simpledialog.askstring("Input", "Enter office:")
#             email = simpledialog.askstring("Input", "Enter email:")
#         result = self.user.add_user(user_id, username, password, role, name, surname, gradyear, major, email, title, hireyear, dept, office)
#         messagebox.showinfo("Result", result)

#     def remove_user(self):
#         username = simpledialog.askstring("Input", "Enter username to remove:")
#         if username:
#             result = self.user.remove_user(username)
#             messagebox.showinfo("Result", result)

#     def add_student_to_course(self):
#         student_username = simpledialog.askstring("Input", "Enter student username:")
#         course_code = simpledialog.askinteger("Input", "Enter course code:")
#         if student_username and course_code:
#             result = self.user.add_student_to_course(student_username, course_code)
#             messagebox.showinfo("Result", result)

#     def remove_student_from_course(self):
#         student_username = simpledialog.askstring("Input", "Enter student username:")
#         course_code = simpledialog.askinteger("Input", "Enter course code:")
#         if student_username and course_code:
#             result = self.user.remove_student_from_course(student_username, course_code)
#             messagebox.showinfo("Result", result)

#     def view_all_courses(self):
#         courses = self.user.view_all_courses()
#         course_list = "\n".join(courses)
#         messagebox.showinfo("Courses", f"All Courses:\n{course_list}")

#     def view_roster(self):
#         course_code = simpledialog.askinteger("Input", "Enter course code:")
#         if course_code:
#             roster = self.user.view_roster(course_code)
#             roster_list = "\n".join(roster)
#             messagebox.showinfo("Roster", f"Roster for Course Code {course_code}:\n{roster_list}")

# if __name__ == "__main__":
#     root = tk.Tk()
#     app = RegistrationSystemApp(root)
#     root.mainloop()
