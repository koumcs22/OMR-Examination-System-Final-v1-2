import sqlite3
from pathlib import Path
from datetime import datetime
import json

APP_DIR = Path.home() / "OMRExaminationSystem"
DB_PATH = APP_DIR / "omr.db"
APP_DIR.mkdir(parents=True, exist_ok=True)

SCHEMA = """
CREATE TABLE IF NOT EXISTS school (
 id INTEGER PRIMARY KEY CHECK(id=1),
 name TEXT, phone TEXT, email TEXT, address1 TEXT, address2 TEXT,
 country TEXT, state TEXT, city TEXT, pincode TEXT, logo_path TEXT
);
CREATE TABLE IF NOT EXISTS users (
 id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password_hash TEXT,
 role TEXT NOT NULL, first_name TEXT, last_name TEXT, phone TEXT, email TEXT,
 active INTEGER DEFAULT 1, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS faculty_subjects (
 id INTEGER PRIMARY KEY AUTOINCREMENT, faculty_id INTEGER, class_name TEXT, subject TEXT
);
CREATE TABLE IF NOT EXISTS students (
 id INTEGER PRIMARY KEY AUTOINCREMENT, student_code TEXT UNIQUE NOT NULL,
 first_name TEXT NOT NULL, last_name TEXT, phone TEXT, class_name TEXT,
 section TEXT, email TEXT, active INTEGER DEFAULT 1, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS imports (
 id INTEGER PRIMARY KEY AUTOINCREMENT, file_name TEXT, imported_at TEXT,
 total INTEGER, success INTEGER, failed INTEGER
);
CREATE TABLE IF NOT EXISTS examinations (
 id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, session TEXT,
 class_name TEXT, section TEXT, subject TEXT, exam_date TEXT,
 template_id TEXT, per_question REAL DEFAULT 1, negative_marking INTEGER DEFAULT 0,
 negative_deduction REAL DEFAULT 0, total_questions INTEGER DEFAULT 0,
 status TEXT DEFAULT 'Draft', created_by INTEGER, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS questions (
 id INTEGER PRIMARY KEY AUTOINCREMENT, exam_id INTEGER NOT NULL, question_no INTEGER,
 question_text TEXT, options_json TEXT, correct_answer TEXT, marks REAL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS omr_sheets (
 id INTEGER PRIMARY KEY AUTOINCREMENT, exam_id INTEGER, sheet_uid TEXT UNIQUE,
 roll_number TEXT, image_path TEXT, scan_status TEXT DEFAULT 'Pending',
 confidence REAL, recognized_answers_json TEXT, scanned_at TEXT
);
CREATE TABLE IF NOT EXISTS evaluations (
 id INTEGER PRIMARY KEY AUTOINCREMENT, exam_id INTEGER, student_id INTEGER,
 sheet_id INTEGER, automatic_marks REAL DEFAULT 0, correction_marks REAL DEFAULT 0,
 grace_marks REAL DEFAULT 0, final_marks REAL DEFAULT 0, status TEXT DEFAULT 'Pending',
 finalized INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS audit_log (
 id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, event_time TEXT,
 student TEXT, examination TEXT, question_no TEXT, old_value TEXT, new_value TEXT,
 old_marks REAL, new_marks REAL, reason TEXT
);
CREATE TABLE IF NOT EXISTS grades (
 id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, min_pct REAL, max_pct REAL
);
CREATE TABLE IF NOT EXISTS distributions (
 id INTEGER PRIMARY KEY AUTOINCREMENT, exam_id INTEGER, channel TEXT, recipient TEXT,
 sent_at TEXT, status TEXT, error_message TEXT
);
CREATE TABLE IF NOT EXISTS settings (
 key TEXT PRIMARY KEY, value TEXT
);
"""

def connect():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    return con

def init_db():
    con = connect()
    con.executescript(SCHEMA)
    if con.execute("SELECT COUNT(*) FROM school").fetchone()[0] == 0:
        con.execute("""INSERT INTO school(id,name,phone,email,address1,address2,country,state,city,pincode)
                       VALUES(1,?,?,?,?,?,?,?,?,?)""",
                    ("Sunrise Public School","+91 98765 43210","admin@sunrise.example",
                     "12 School Road","","India","West Bengal","Kolkata","700001"))
    if con.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
        # demo local admin; change password from Settings in production
        con.execute("""INSERT INTO users(username,password_hash,role,first_name,last_name,email,created_at)
                       VALUES(?,?,?,?,?,?,?)""",
                    ("admin","admin","Administrator","School","Admin","admin@sunrise.example",datetime.now().isoformat()))
    if con.execute("SELECT COUNT(*) FROM grades").fetchone()[0] == 0:
        con.executemany("INSERT INTO grades(name,min_pct,max_pct) VALUES(?,?,?)",
                        [("A+",90,100),("A",80,89.99),("B+",70,79.99),("B",60,69.99),("C",50,59.99),("D",40,49.99),("E",0,39.99)])
    con.commit(); con.close()

def query(sql, params=()):
    try:
        con=connect()
        rows=con.execute(sql,params).fetchall()
        con.close()
        return rows
    except Exception as e:
        print(f"Database query error: {e}")
        return []

def execute(sql, params=()):
    try:
        con=connect()
        cur=con.execute(sql,params)
        con.commit()
        lastid=cur.lastrowid
        con.close()
        return lastid
    except Exception as e:
        print(f"Database execute error: {e}")
        raise