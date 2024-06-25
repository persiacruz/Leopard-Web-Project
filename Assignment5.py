import sqlite3 as sql
import hashlib

# Connect to the SQLite database
database = sql.connect("LeopardWebDatabase.db")

# Function to hash passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Function to initialize the database
def initialize_database():
    # Drop tables if they exist to start fresh
    database.execute("DROP TABLE IF EXISTS USER")
    database.execute("DROP TABLE IF EXISTS STUDENT")
    database.execute("DROP TABLE IF EXISTS INSTRUCTOR")
    database.execute("DROP TABLE IF EXISTS ADMIN")
    database.execute("DROP TABLE IF EXISTS COURSE")
    database.execute("DROP TABLE IF EXISTS REGISTRATION")
#Nadia completed this part
    # Create tables
    database.execute("""CREATE TABLE USER (
        ID INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        role TEXT NOT NULL
    );""")

    database.execute("""CREATE TABLE STUDENT (
        ID INTEGER PRIMARY KEY AUTOINCREMENT,
        NAME TEXT NOT NULL,
        SURNAME TEXT NOT NULL,
        USERNAME TEXT NOT NULL UNIQUE,
        GRADYEAR TEXT,
        MAJOR TEXT,
        EMAIL TEXT,
        FOREIGN KEY (USERNAME) REFERENCES USER(username)
    );""")

    database.execute("""CREATE TABLE INSTRUCTOR (
        ID INTEGER PRIMARY KEY AUTOINCREMENT,
        NAME TEXT NOT NULL,
        SURNAME TEXT NOT NULL,
        TITLE TEXT,
        HIREYEAR INTEGER,
        DEPT TEXT,
        EMAIL TEXT NOT NULL UNIQUE
    );""")

    database.execute("""CREATE TABLE ADMIN (
        ID INTEGER PRIMARY KEY AUTOINCREMENT,
        NAME TEXT NOT NULL,
        SURNAME TEXT NOT NULL,
        TITLE TEXT,
        OFFICE TEXT,
        EMAIL TEXT NOT NULL UNIQUE
    );""")

    database.execute("""CREATE TABLE COURSE (
        CRN INTEGER PRIMARY KEY,
        TITLE TEXT NOT NULL,
        DEPARTMENT TEXT NOT NULL,
        TIME TEXT NOT NULL,
        DAYS TEXT NOT NULL,
        SEMESTER TEXT NOT NULL,
        YEAR INTEGER NOT NULL,
        CREDITS INTEGER NOT NULL,
        instructor_id INTEGER,
        FOREIGN KEY (instructor_id) REFERENCES INSTRUCTOR(ID)
    );""")

    database.execute("""CREATE TABLE REGISTRATION (
        student_id INTEGER NOT NULL,
        course_code INTEGER NOT NULL,
        PRIMARY KEY (student_id, course_code),
        FOREIGN KEY (student_id) REFERENCES USER(ID),
        FOREIGN KEY (course_code) REFERENCES COURSE(CRN)
    );""")
#Persia completed this part
    # Insert sample admins and instructors into USER table
    admin_password = hash_password("adminpass")
    database.execute("INSERT INTO USER (username, password, role) VALUES ('hamiltonm', ?, 'admin')", (admin_password,))
    database.execute("INSERT INTO USER (username, password, role) VALUES ('rubinv', ?, 'admin')", (admin_password,))

    instructor_passwords = [hash_password("fourierj"), hash_password("patrickn"), hash_password("galileig"), hash_password("turinga"), hash_password("boumank")]
    instructor_usernames = ["fourierj", "patrickn", "galileig", "turinga", "boumank"]
    for i, username in enumerate(instructor_usernames):
        database.execute("INSERT INTO USER (username, password, role) VALUES (?, ?, 'instructor')", (username, instructor_passwords[i]))

    # Insert sample instructors into INSTRUCTOR table
    database.execute("INSERT INTO INSTRUCTOR (NAME, SURNAME, TITLE, HIREYEAR, DEPT, EMAIL) VALUES ('Joseph', 'Fourier', 'Full Prof.', 1820, 'BSEE', 'fourierj')")
    database.execute("INSERT INTO INSTRUCTOR (NAME, SURNAME, TITLE, HIREYEAR, DEPT, EMAIL) VALUES ('Nelson', 'Patrick', 'Full Prof.', 1994, 'HUSS', 'patrickn')")
    database.execute("INSERT INTO INSTRUCTOR (NAME, SURNAME, TITLE, HIREYEAR, DEPT, EMAIL) VALUES ('Galileo', 'Galilei', 'Full Prof.', 1600, 'BSAS', 'galileig')")
    database.execute("INSERT INTO INSTRUCTOR (NAME, SURNAME, TITLE, HIREYEAR, DEPT, EMAIL) VALUES ('Alan', 'Turing', 'Associate Prof.', 1940, 'BSCO', 'turinga')")
    database.execute("INSERT INTO INSTRUCTOR (NAME, SURNAME, TITLE, HIREYEAR, DEPT, EMAIL) VALUES ('Katie', 'Bouman', 'Assistant Prof.', 2019, 'BCOS', 'boumank')")

#Nadia completed this part
    # Insert sample students into STUDENT table
    student_password = hash_password("studentpass")
    student_names = [
        ("Isaac", "Newton", "newtoni", 1668, "BSAS", "newtoni"),
        ("Marie", "Curie", "curiem", 1903, "BSAS", "curiem"),
        ("Nikola", "Tesla", "telsan", 1878, "BSEE", "telsan"),
        ("Thomas", "Edison", "notcool", 1879, "BSEE", "notcool"),
        ("John", "von Neumann", "vonneumannj", 1923, "BSCO", "vonneumannj"),
        ("Grace", "Hopper", "hopperg", 1928, "BCOS", "hopperg"),
        ("Mae", "Jemison", "jemisonm", 1981, "BSCH", "jemisonm"),
        ("Mark", "Dean", "deanm", 1979, "BSCO", "deanm"),
        ("Michael", "Faraday", "faradaym", 1812, "BSAS", "faradaym"),
        ("Ada", "Lovelace", "lovelacea", 1832, "BCOS", "lovelacea")
    ]
#Persia completed this part
    for student in student_names:
        database.execute("INSERT INTO USER (username, password, role) VALUES (?, ?, 'student')", (student[2], student_password))
        database.execute("INSERT INTO STUDENT (NAME, SURNAME, USERNAME, GRADYEAR, MAJOR, EMAIL) VALUES (?, ?, ?, ?, ?, ?)", student)

    # Insert sample admins into ADMIN table
    database.execute("INSERT INTO ADMIN (NAME, SURNAME, TITLE, OFFICE, EMAIL) VALUES ('Margaret', 'Hamilton', 'President', 'Dobbs 1600', 'hamiltonm')")
    database.execute("INSERT INTO ADMIN (NAME, SURNAME, TITLE, OFFICE, EMAIL) VALUES ('Vera', 'Rubin', 'Vice-President', 'Wentworth 101', 'rubinv')")

    # Insert sample courses with instructors
    database.execute("INSERT INTO COURSE (CRN, TITLE, DEPARTMENT, TIME, DAYS, SEMESTER, YEAR, CREDITS, instructor_id) VALUES (33173, 'Applied Programming Concepts', 'BSCO', '8:00-8:50', 'M', 'Summer', 2024, 3, 4)")                                                              
    database.execute("INSERT INTO COURSE (CRN, TITLE, DEPARTMENT, TIME, DAYS, SEMESTER, YEAR, CREDITS, instructor_id) VALUES (33184, 'Analog Circuit Design', 'BSCO', '10:00-11:50', 'TR', 'Summer', 2024, 4, 4)")
    database.execute("INSERT INTO COURSE (CRN, TITLE, DEPARTMENT, TIME, DAYS, SEMESTER, YEAR, CREDITS, instructor_id) VALUES (33171, 'Advance Digital Circuit Design', 'BSCO', '12:00-1:50', 'WF', 'Summer', 2024, 4, 4)")
    database.execute("INSERT INTO COURSE (CRN, TITLE, DEPARTMENT, TIME, DAYS, SEMESTER, YEAR, CREDITS, instructor_id) VALUES (33172, 'Advance Digital Circuit Design-LAB', 'BSCO', '2:00-3:50', 'W', 'Summer', 2024, 0, 4)")
    database.execute("INSERT INTO COURSE (CRN, TITLE, DEPARTMENT, TIME, DAYS, SEMESTER, YEAR, CREDITS, instructor_id) VALUES (33182, 'Computer Networks for Engineers', 'BSCO', '8:00-9:20', 'MWF', 'Summer', 2024, 4, 4)")

    database.execute("INSERT INTO COURSE (CRN, TITLE, DEPARTMENT, TIME, DAYS, SEMESTER, YEAR, CREDITS, instructor_id) VALUES (10001, 'Engineering Calculus', 'Math', '8:00-9:00', 'MWF', 'Fall', 2024, 4, 1)")
    database.execute("INSERT INTO COURSE (CRN, TITLE, DEPARTMENT, TIME, DAYS, SEMESTER, YEAR, CREDITS, instructor_id) VALUES (10002, 'Probability and Statistics', 'Math', '9:00-10:00', 'TR', 'Fall', 2024, 3, 2)")
    database.execute("INSERT INTO COURSE (CRN, TITLE, DEPARTMENT, TIME, DAYS, SEMESTER, YEAR, CREDITS, instructor_id) VALUES (10003, 'Differential equations', 'Math', '10:00-11:00', 'MWF', 'Fall', 2024, 4, 3)")
    database.execute("INSERT INTO COURSE (CRN, TITLE, DEPARTMENT, TIME, DAYS, SEMESTER, YEAR, CREDITS, instructor_id) VALUES (10004, 'English 1', 'English', '11:00-12:00', 'TR', 'Fall', 2024, 3, 2)")
    database.execute("INSERT INTO COURSE (CRN, TITLE, DEPARTMENT, TIME, DAYS, SEMESTER, YEAR, CREDITS, instructor_id) VALUES (10005, 'English 2', 'English', '1:00-2:00', 'MWF', 'Fall', 2024, 3, 2)")
    database.execute("INSERT INTO COURSE (CRN, TITLE, DEPARTMENT, TIME, DAYS, SEMESTER, YEAR, CREDITS, instructor_id) VALUES (10006, 'Plague Literature', 'Humanities', '2:00-3:00', 'TR', 'Fall', 2024, 3, 3)")
    database.execute("INSERT INTO COURSE (CRN, TITLE, DEPARTMENT, TIME, DAYS, SEMESTER, YEAR, CREDITS, instructor_id) VALUES (10007, 'Folk Music in America', 'Humanities', '3:00-4:00', 'MWF', 'Fall', 2024, 3, 3)")
    database.execute("INSERT INTO COURSE (CRN, TITLE, DEPARTMENT, TIME, DAYS, SEMESTER, YEAR, CREDITS, instructor_id) VALUES (10008, 'Jazz', 'Humanities', '4:00-5:00', 'TR', 'Fall', 2024, 3, 3)")
    database.execute("INSERT INTO COURSE (CRN, TITLE, DEPARTMENT, TIME, DAYS, SEMESTER, YEAR, CREDITS, instructor_id) VALUES (10009, 'Object Oriented Programming', 'Electronics', '8:00-9:30', 'MW', 'Fall', 2024, 4, 4)")
    database.execute("INSERT INTO COURSE (CRN, TITLE, DEPARTMENT, TIME, DAYS, SEMESTER, YEAR, CREDITS, instructor_id) VALUES (10010, 'Analog Circuit Design', 'Electronics', '9:30-11:00', 'TR', 'Fall', 2024, 4, 4)")
    database.execute("INSERT INTO COURSE (CRN, TITLE, DEPARTMENT, TIME, DAYS, SEMESTER, YEAR, CREDITS, instructor_id) VALUES (10011, 'Applied Programming Concepts', 'Electronics', '11:00-12:30', 'MW', 'Fall', 2024, 4, 4)")
    database.execute("INSERT INTO COURSE (CRN, TITLE, DEPARTMENT, TIME, DAYS, SEMESTER, YEAR, CREDITS, instructor_id) VALUES (10012, 'Computer Networks for Engineers', 'Electronics', '1:00-2:30', 'TR', 'Fall', 2024, 4, 4)")

    # Commit the transactions
    database.commit()
    print("Database initialized with sample data.")
    
#Nadia completed this part
# Function to clear only dynamically added data
def clear_dynamic_data():
    database.execute("DELETE FROM USER WHERE username NOT IN ('hamiltonm', 'rubinv', 'fourierj', 'patrickn', 'galileig', 'turinga', 'boumank', 'newtoni', 'curiem', 'telsan', 'notcool', 'vonneumannj', 'hopperg', 'jemisonm', 'deanm', 'faradaym', 'lovelacea');")
    database.execute("DELETE FROM STUDENT WHERE USERNAME NOT IN ('newtoni', 'curiem', 'telsan', 'notcool', 'vonneumannj', 'hopperg', 'jemisonm', 'deanm', 'faradaym', 'lovelacea');")
    database.execute("DELETE FROM INSTRUCTOR WHERE EMAIL NOT IN ('fourierj', 'patrickn', 'galileig', 'turinga', 'boumank');")
    database.execute("DELETE FROM ADMIN WHERE EMAIL NOT IN ('hamiltonm', 'rubinv');")
    database.execute("DELETE FROM COURSE WHERE CRN NOT IN (33173, 33184, 33171, 33172, 33182, 10001, 10002, 10003, 10004, 10005, 10006, 10007, 10008, 10009, 10010, 10011, 10012);")
    database.execute("DELETE FROM REGISTRATION;")
    database.commit()
    print("Dynamic data cleared, base data kept intact.")

# Ask user if they want to clear dynamic data or continue with the existing data
choice = input("Do you want to (1) Clear dynamic data or (2) Continue with existing data? Enter 1 or 2: ")
if choice == '1':
    clear_dynamic_data()
elif choice == '2':
    print("Continuing with existing data.")
else:
    print("Invalid choice. Exiting...")

# Close the database connection
database.close()


