from fastapi import FastAPI
from pydantic import BaseModel
import sqlite3
from datetime import datetime, date

app = FastAPI()

DATABASE_NAME = "leave_management.db"


def get_db_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            employee_name TEXT NOT NULL,
            department TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leave_requests (
            leave_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            employee_name TEXT NOT NULL,
            department TEXT NOT NULL,
            leave_type TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            reason TEXT NOT NULL,
            status TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def insert_sample_users():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR IGNORE INTO users
        (username, password, role, employee_name, department)
        VALUES (?, ?, ?, ?, ?)
    """, ("arul", "1234", "Employee", "Arul", "IT"))

    cursor.execute("""
        INSERT OR IGNORE INTO users
        (username, password, role, employee_name, department)
        VALUES (?, ?, ?, ?, ?)
    """, ("manager", "admin123", "Manager", "Manager", "HR"))

    conn.commit()
    conn.close()


create_tables()
insert_sample_users()


class LoginRequest(BaseModel):
    username: str
    password: str


class LeaveRequest(BaseModel):
    username: str
    employee_name: str
    department: str
    leave_type: str
    start_date: str
    end_date: str
    reason: str


@app.get("/")
def home():
    return {"message": "Employee Leave Management API is running"}


@app.post("/login")
def login(user: LoginRequest):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM users
        WHERE username = ? AND password = ?
    """, (user.username, user.password))

    result = cursor.fetchone()
    conn.close()

    if result:
        return {
            "login_status": "success",
            "username": result["username"],
            "role": result["role"],
            "employee_name": result["employee_name"],
            "department": result["department"]
        }

    return {
        "login_status": "failed",
        "message": "Invalid username or password"
    }


@app.post("/apply-leave")
def apply_leave(leave: LeaveRequest):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        start_date = datetime.strptime(leave.start_date, "%Y-%m-%d").date()
        end_date = datetime.strptime(leave.end_date, "%Y-%m-%d").date()
    except ValueError:
        conn.close()
        return {
            "status": "error",
            "message": "Invalid date format. Please use YYYY-MM-DD."
        }

    today = date.today()

    if start_date < today:
        conn.close()
        return {
            "status": "error",
            "message": "Start date cannot be a past date."
        }

    if end_date < today:
        conn.close()
        return {
            "status": "error",
            "message": "End date cannot be a past date."
        }

    if end_date < start_date:
        conn.close()
        return {
            "status": "error",
            "message": "End date cannot be before start date."
        }

    cursor.execute("""
        SELECT * FROM leave_requests
        WHERE username = ?
        AND status IN ('Pending', 'Approved')
        AND (
            date(start_date) <= date(?)
            AND date(end_date) >= date(?)
        )
    """, (
        leave.username,
        leave.end_date,
        leave.start_date
    ))

    existing_leave = cursor.fetchone()

    if existing_leave:
        conn.close()
        return {
            "status": "error",
            "message": "You already have a Pending or Approved leave request in this date range."
        }

    cursor.execute("""
        INSERT INTO leave_requests
        (username, employee_name, department, leave_type, start_date, end_date, reason, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        leave.username,
        leave.employee_name,
        leave.department,
        leave.leave_type,
        leave.start_date,
        leave.end_date,
        leave.reason,
        "Pending"
    ))

    conn.commit()
    conn.close()

    return {
        "status": "success",
        "message": "Leave request submitted successfully.",
        "leave_status": "Pending"
    }


@app.get("/my-leave-requests/{username}")
def get_my_leave_requests(username: str):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM leave_requests
        WHERE username = ?
        ORDER BY leave_id DESC
    """, (username,))

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


@app.get("/all-leave-requests")
def get_all_leave_requests():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM leave_requests
        ORDER BY leave_id DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


@app.put("/update-leave-status/{leave_id}")
def update_leave_status(leave_id: int, status: str):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM leave_requests
        WHERE leave_id = ?
    """, (leave_id,))

    leave_record = cursor.fetchone()

    if leave_record is None:
        conn.close()
        return {
            "status": "error",
            "message": "Invalid Leave ID. This leave request does not exist."
        }

    if status not in ["Approved", "Rejected"]:
        conn.close()
        return {
            "status": "error",
            "message": "Invalid status. Please choose Approved or Rejected."
        }

    if leave_record["status"] != "Pending":
        conn.close()
        return {
            "status": "error",
            "message": f"This leave request is already {leave_record['status']}."
        }

    cursor.execute("""
        UPDATE leave_requests
        SET status = ?
        WHERE leave_id = ?
    """, (status, leave_id))

    conn.commit()
    conn.close()

    return {
        "status": "success",
        "message": f"Leave request {status} successfully."
    }


@app.get("/employees")
def get_employees():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT user_id, username, role, employee_name, department
        FROM users
        ORDER BY user_id ASC
    """)

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


@app.get("/leave-statistics")
def get_leave_statistics():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT status, COUNT(*) as count
        FROM leave_requests
        GROUP BY status
    """)

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]