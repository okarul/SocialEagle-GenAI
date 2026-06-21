import streamlit as st
import requests
import pandas as pd
from datetime import date
import urllib.parse
import altair as alt

API_URL = "http://127.0.0.1:8001"

st.set_page_config(
    page_title="Employee Leave Management",
    layout="wide"
)


logo_svg = """
<svg width="90" height="90" viewBox="0 0 90 90" xmlns="http://www.w3.org/2000/svg">
  <rect width="90" height="90" rx="22" fill="#2563eb"/>
  <rect x="20" y="24" width="50" height="46" rx="6" fill="white"/>
  <rect x="20" y="24" width="50" height="12" rx="6" fill="#93c5fd"/>
  <circle cx="32" cy="47" r="4" fill="#2563eb"/>
  <circle cx="45" cy="47" r="4" fill="#2563eb"/>
  <circle cx="58" cy="47" r="4" fill="#2563eb"/>
  <circle cx="32" cy="60" r="4" fill="#16a34a"/>
  <circle cx="45" cy="60" r="4" fill="#f97316"/>
  <circle cx="58" cy="60" r="4" fill="#dc2626"/>
</svg>
"""

logo_url = "data:image/svg+xml;utf8," + urllib.parse.quote(logo_svg)


st.markdown("""
<style>
.block-container {
    padding-top: 1.2rem;
}

.main-header {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 22px;
    margin-top: 5px;
    margin-bottom: 18px;
    padding: 26px 20px;
    border-radius: 22px;
    background: linear-gradient(135deg, #0f172a, #1e3a8a, #2563eb);
    box-shadow: 0px 8px 28px rgba(37, 99, 235, 0.35);
}

.header-logo {
    width: 82px;
    height: 82px;
    border-radius: 20px;
    box-shadow: 0px 6px 18px rgba(0,0,0,0.35);
}

.header-title {
    text-align: center;
    font-size: 44px;
    font-weight: 900;
    color: #ffffff;
    letter-spacing: 0.5px;
}

.header-subtitle {
    text-align: center;
    font-size: 17px;
    color: #dbeafe;
    margin-top: 6px;
}

.login-title {
    text-align: center;
    font-size: 34px;
    font-weight: 900;
    color: white;
    margin-top: 0px;
    margin-bottom: 8px;
}

.login-subtitle {
    text-align: center;
    font-size: 15px;
    color: #d1d5db;
    margin-bottom: 20px;
}

.login-note {
    text-align: center;
    font-size: 13px;
    color: #9ca3af;
    margin-top: 14px;
}

div.stButton > button {
    border-radius: 12px;
    height: 48px;
    font-weight: 700;
}

.dashboard-card {
    height: 155px;
    padding: 18px;
    border-radius: 18px;
    color: white;
    text-align: center;
    box-shadow: 0px 4px 12px rgba(0,0,0,0.25);
    margin-bottom: 18px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
}

.blue-card {
    background: linear-gradient(135deg, #4f67e9, #2f3fbf);
}

.orange-card {
    background: linear-gradient(135deg, #ea6b1f, #c74b17);
}

.green-card {
    background: linear-gradient(135deg, #439b49, #2f7338);
}

.red-card {
    background: linear-gradient(135deg, #c92d32, #9f2026);
}

.purple-card {
    background: linear-gradient(135deg, #9333ea, #6b21a8);
}

.teal-card {
    background: linear-gradient(135deg, #438f84, #31776e);
}

.card-title {
    height: 48px;
    font-size: 22px;
    font-weight: 750;
    line-height: 1.25;
    display: flex;
    justify-content: center;
    align-items: center;
}

.card-value {
    font-size: 46px;
    font-weight: 900;
    line-height: 1;
}

.insight-box {
    min-height: 135px;
    background-color: #f8fafc;
    color: #0f172a;
    padding: 22px 26px;
    border-left: 8px solid #2563eb;
    border-radius: 14px;
    margin-top: 18px;
    margin-bottom: 10px;
    font-size: 18px;
    line-height: 1.7;
}

.warning-box {
    min-height: 150px;
    background-color: #fff7ed;
    color: #7c2d12;
    padding: 24px 28px;
    border-left: 8px solid #f97316;
    border-radius: 14px;
    margin-top: 18px;
    margin-bottom: 10px;
    font-size: 20px;
    line-height: 1.7;
}

.success-box {
    min-height: 150px;
    background-color: #ecfdf5;
    color: #14532d;
    padding: 24px 28px;
    border-left: 8px solid #16a34a;
    border-radius: 14px;
    margin-top: 18px;
    margin-bottom: 10px;
    font-size: 20px;
    line-height: 1.7;
}

.empty-table-box {
    height: 240px;
    border: 1px solid rgba(255,255,255,0.15);
    border-radius: 12px;
    padding: 24px;
    color: #d1d5db;
    display: flex;
    align-items: center;
    justify-content: center;
}
</style>
""", unsafe_allow_html=True)


st.markdown(f"""
<div class="main-header">
    <img src="{logo_url}" class="header-logo">
    <div>
        <div class="header-title">Employee Leave Management System</div>
        <div class="header-subtitle">
            Smart leave request, approval, and workforce availability dashboard
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = ""

if "role" not in st.session_state:
    st.session_state.role = ""

if "employee_name" not in st.session_state:
    st.session_state.employee_name = ""

if "department" not in st.session_state:
    st.session_state.department = ""


def show_horizontal_bar_chart(data, label_column, value_column):
    chart = (
        alt.Chart(data)
        .mark_bar(cornerRadiusEnd=6)
        .encode(
            x=alt.X(
                f"{value_column}:Q",
                title=None,
                axis=alt.Axis(grid=True, tickMinStep=1)
            ),
            y=alt.Y(
                f"{label_column}:N",
                title=None,
                sort="-x",
                axis=alt.Axis(labelLimit=220)
            ),
            tooltip=[label_column, value_column]
        )
        .properties(height=280)
    )

    st.altair_chart(chart, use_container_width=True)


if st.session_state.logged_in == False:

    col1, col2, col3 = st.columns([1.4, 1, 1.4])

    with col2:
        st.markdown(
            '<div class="login-title">Login</div>',
            unsafe_allow_html=True
        )

        st.markdown(
            '<div class="login-subtitle">Employee Leave Management Portal</div>',
            unsafe_allow_html=True
        )

        username = st.text_input(
            "Username",
            placeholder="Enter username"
        )

        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter password"
        )

        login_button = st.button(
            "Login",
            use_container_width=True
        )

        st.markdown(
            '<div class="login-note">Employee and Manager role-based access</div>',
            unsafe_allow_html=True
        )

        if login_button:
            login_data = {
                "username": username,
                "password": password
            }

            try:
                response = requests.post(
                    f"{API_URL}/login",
                    json=login_data
                )

                if response.status_code == 200:
                    result = response.json()

                    if result["login_status"] == "success":
                        st.session_state.logged_in = True
                        st.session_state.username = result["username"]
                        st.session_state.role = result["role"]
                        st.session_state.employee_name = result["employee_name"]
                        st.session_state.department = result["department"]

                        st.success("Login successful.")
                        st.rerun()
                    else:
                        st.error("Invalid username or password.")
                else:
                    st.error("Backend connection error.")

            except requests.exceptions.ConnectionError:
                st.error("FastAPI backend is not running. Please start backend on port 8001.")


else:
    st.sidebar.success(f"Logged in as: {st.session_state.employee_name}")
    st.sidebar.write(f"Role: {st.session_state.role}")

    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.role = ""
        st.session_state.employee_name = ""
        st.session_state.department = ""
        st.rerun()

    if st.session_state.role == "Employee":
        menu = st.sidebar.radio(
            "Employee Menu",
            [
                "Employee Dashboard",
                "Apply Leave",
                "My Leave History"
            ]
        )

        if menu == "Employee Dashboard":
            st.header("Employee Dashboard")
            st.info("Welcome to the Employee Dashboard.")

            col1, col2 = st.columns(2)
            col1.write(f"Employee Name: {st.session_state.employee_name}")
            col2.write(f"Department: {st.session_state.department}")

            st.write("You can apply for leave and view your own leave history.")

        elif menu == "Apply Leave":
            st.header("Apply Leave")

            st.write(f"Employee Name: {st.session_state.employee_name}")
            st.write(f"Department: {st.session_state.department}")

            leave_type = st.selectbox(
                "Leave Type",
                [
                    "Annual Leave",
                    "Medical Leave",
                    "Emergency Leave",
                    "Unpaid Leave"
                ]
            )

            today = date.today()

            start_date = st.date_input(
                "Start Date",
                min_value=today
            )

            end_date = st.date_input(
                "End Date",
                min_value=today
            )

            reason = st.text_area("Reason for Leave")

            if st.button("Submit Leave Request"):
                if not reason:
                    st.warning("Please enter reason for leave.")

                elif end_date < start_date:
                    st.error("End date cannot be before start date.")

                else:
                    leave_data = {
                        "username": st.session_state.username,
                        "employee_name": st.session_state.employee_name,
                        "department": st.session_state.department,
                        "leave_type": leave_type,
                        "start_date": str(start_date),
                        "end_date": str(end_date),
                        "reason": reason
                    }

                    try:
                        response = requests.post(
                            f"{API_URL}/apply-leave",
                            json=leave_data
                        )

                        if response.status_code == 200:
                            result = response.json()

                            if result["status"] == "success":
                                st.success(result["message"])
                            else:
                                st.error(result["message"])
                        else:
                            st.error("Unable to submit leave request.")

                    except requests.exceptions.ConnectionError:
                        st.error("FastAPI backend is not running. Please start backend on port 8001.")

        elif menu == "My Leave History":
            st.header("My Leave History")

            try:
                response = requests.get(
                    f"{API_URL}/my-leave-requests/{st.session_state.username}"
                )

                if response.status_code == 200:
                    leave_requests = response.json()

                    if leave_requests:
                        df = pd.DataFrame(leave_requests)
                        st.dataframe(df, use_container_width=True)
                    else:
                        st.info("No leave history found.")
                else:
                    st.error("Unable to fetch leave history.")

            except requests.exceptions.ConnectionError:
                st.error("FastAPI backend is not running. Please start backend on port 8001.")


    elif st.session_state.role == "Manager":
        menu = st.sidebar.radio(
            "Manager Menu",
            [
                "Manager Dashboard",
                "Approve / Reject Leave",
                "View All Leave History",
                "Employee Details",
                "Leave Statistics"
            ]
        )

        if menu == "Manager Dashboard":
            st.header("Manager Dashboard")
            st.info("Welcome to the Manager Dashboard.")

            st.write("""
            Managers can view all leave requests, approve or reject leave,
            view employee details, and check leave statistics.
            """)

        elif menu == "Approve / Reject Leave":
            st.header("Approve / Reject Leave")

            try:
                response = requests.get(f"{API_URL}/all-leave-requests")

                if response.status_code == 200:
                    leave_requests = response.json()

                    if leave_requests:
                        df = pd.DataFrame(leave_requests)

                        st.subheader("All Leave Requests")
                        st.dataframe(df, use_container_width=True)

                        pending_leave_requests = [
                            leave for leave in leave_requests
                            if leave["status"] == "Pending"
                        ]

                        if pending_leave_requests:
                            st.subheader("Update Leave Status")

                            leave_options = {
                                f"Leave ID {leave['leave_id']} - {leave['employee_name']} - {leave['start_date']} to {leave['end_date']}": leave["leave_id"]
                                for leave in pending_leave_requests
                            }

                            selected_leave = st.selectbox(
                                "Select Valid Pending Leave Request",
                                list(leave_options.keys())
                            )

                            leave_id = leave_options[selected_leave]

                            status = st.selectbox(
                                "Select Status",
                                ["Approved", "Rejected"]
                            )

                            if st.button("Update Status"):
                                update_response = requests.put(
                                    f"{API_URL}/update-leave-status/{leave_id}",
                                    params={"status": status}
                                )

                                if update_response.status_code == 200:
                                    result = update_response.json()

                                    if result["status"] == "success":
                                        st.success(result["message"])
                                        st.rerun()
                                    else:
                                        st.error(result["message"])
                                else:
                                    st.error("Unable to update status.")
                        else:
                            st.info("No pending leave requests available for approval.")

                    else:
                        st.info("No leave requests available.")
                else:
                    st.error("Unable to fetch leave requests.")

            except requests.exceptions.ConnectionError:
                st.error("FastAPI backend is not running. Please start backend on port 8001.")

        elif menu == "View All Leave History":
            st.header("View All Leave History")

            try:
                response = requests.get(f"{API_URL}/all-leave-requests")

                if response.status_code == 200:
                    leave_requests = response.json()

                    if leave_requests:
                        df = pd.DataFrame(leave_requests)
                        st.dataframe(df, use_container_width=True)
                    else:
                        st.info("No leave history found.")
                else:
                    st.error("Unable to fetch leave history.")

            except requests.exceptions.ConnectionError:
                st.error("FastAPI backend is not running. Please start backend on port 8001.")

        elif menu == "Employee Details":
            st.header("Employee Details")

            try:
                response = requests.get(f"{API_URL}/employees")

                if response.status_code == 200:
                    employees = response.json()

                    if employees:
                        df = pd.DataFrame(employees)
                        st.dataframe(df, use_container_width=True)
                    else:
                        st.info("No employee records found.")
                else:
                    st.error("Unable to fetch employee details.")

            except requests.exceptions.ConnectionError:
                st.error("FastAPI backend is not running. Please start backend on port 8001.")

        elif menu == "Leave Statistics":
            st.header("Leave Statistics & Management Insights")

            try:
                response = requests.get(f"{API_URL}/all-leave-requests")

                if response.status_code == 200:
                    leave_requests = response.json()

                    if leave_requests:
                        df = pd.DataFrame(leave_requests)

                        df["start_date"] = pd.to_datetime(df["start_date"], errors="coerce")
                        df["end_date"] = pd.to_datetime(df["end_date"], errors="coerce")

                        df["is_valid_date_range"] = df["end_date"] >= df["start_date"]

                        df["leave_days"] = 0
                        df.loc[df["is_valid_date_range"], "leave_days"] = (
                            df.loc[df["is_valid_date_range"], "end_date"]
                            - df.loc[df["is_valid_date_range"], "start_date"]
                        ).dt.days + 1

                        valid_df = df[df["is_valid_date_range"] == True]
                        invalid_df = df[df["is_valid_date_range"] == False]

                        total_requests = len(df)
                        pending_count = len(df[df["status"] == "Pending"])
                        approved_count = len(df[df["status"] == "Approved"])
                        rejected_count = len(df[df["status"] == "Rejected"])

                        approval_rate = round((approved_count / total_requests) * 100, 1)
                        rejection_rate = round((rejected_count / total_requests) * 100, 1)

                        approved_leave_days = valid_df[
                            valid_df["status"] == "Approved"
                        ]["leave_days"].sum()

                        pending_leave_days = valid_df[
                            valid_df["status"] == "Pending"
                        ]["leave_days"].sum()

                        today_datetime = pd.to_datetime("today").normalize()

                        upcoming_approved = valid_df[
                            (valid_df["status"] == "Approved")
                            & (valid_df["start_date"] >= today_datetime)
                        ]

                        st.subheader("One-Page Management Dashboard")

                        col1, col2, col3, col4 = st.columns(4)

                        with col1:
                            st.markdown(f"""
                            <div class="dashboard-card blue-card">
                                <div class="card-title">Total Requests</div>
                                <div class="card-value">{total_requests}</div>
                            </div>
                            """, unsafe_allow_html=True)

                        with col2:
                            st.markdown(f"""
                            <div class="dashboard-card orange-card">
                                <div class="card-title">Pending Approvals</div>
                                <div class="card-value">{pending_count}</div>
                            </div>
                            """, unsafe_allow_html=True)

                        with col3:
                            st.markdown(f"""
                            <div class="dashboard-card green-card">
                                <div class="card-title">Approved Leaves</div>
                                <div class="card-value">{approved_count}</div>
                            </div>
                            """, unsafe_allow_html=True)

                        with col4:
                            st.markdown(f"""
                            <div class="dashboard-card red-card">
                                <div class="card-title">Rejected Leaves</div>
                                <div class="card-value">{rejected_count}</div>
                            </div>
                            """, unsafe_allow_html=True)

                        col5, col6, col7, col8 = st.columns(4)

                        with col5:
                            st.markdown(f"""
                            <div class="dashboard-card purple-card">
                                <div class="card-title">Approval Rate</div>
                                <div class="card-value">{approval_rate}%</div>
                            </div>
                            """, unsafe_allow_html=True)

                        with col6:
                            st.markdown(f"""
                            <div class="dashboard-card red-card">
                                <div class="card-title">Rejection Rate</div>
                                <div class="card-value">{rejection_rate}%</div>
                            </div>
                            """, unsafe_allow_html=True)

                        with col7:
                            st.markdown(f"""
                            <div class="dashboard-card teal-card">
                                <div class="card-title">Approved Leave Days</div>
                                <div class="card-value">{int(approved_leave_days)}</div>
                            </div>
                            """, unsafe_allow_html=True)

                        with col8:
                            st.markdown(f"""
                            <div class="dashboard-card orange-card">
                                <div class="card-title">Pending Leave Days</div>
                                <div class="card-value">{int(pending_leave_days)}</div>
                            </div>
                            """, unsafe_allow_html=True)

                        st.divider()

                        chart_col1, chart_col2 = st.columns(2)

                        with chart_col1:
                            st.subheader("Leave Status Overview")

                            status_summary = df["status"].value_counts().reset_index()
                            status_summary.columns = ["Status", "Count"]

                            show_horizontal_bar_chart(
                                status_summary,
                                "Status",
                                "Count"
                            )

                        with chart_col2:
                            st.subheader("Leave Type Demand")

                            leave_type_summary = df["leave_type"].value_counts().reset_index()
                            leave_type_summary.columns = ["Leave Type", "Count"]

                            show_horizontal_bar_chart(
                                leave_type_summary,
                                "Leave Type",
                                "Count"
                            )

                        st.divider()

                        insight_col1, insight_col2 = st.columns(2)

                        with insight_col1:
                            st.subheader("Department-wise Leave Days")

                            if not valid_df.empty:
                                dept_summary = valid_df.groupby("department")["leave_days"].sum().reset_index()
                                dept_summary = dept_summary.sort_values(
                                    by="leave_days",
                                    ascending=False
                                )

                                st.dataframe(
                                    dept_summary,
                                    use_container_width=True,
                                    height=240
                                )

                                top_department = dept_summary.iloc[0]["department"]
                                top_department_days = dept_summary.iloc[0]["leave_days"]

                                st.markdown(f"""
                                <div class="insight-box">
                                    <b>Management Insight:</b><br>
                                    The highest leave demand is from the <b>{top_department}</b> department,
                                    with <b>{int(top_department_days)}</b> leave day(s). Management should review
                                    team coverage and backup planning.
                                </div>
                                """, unsafe_allow_html=True)
                            else:
                                st.markdown(
                                    '<div class="empty-table-box">No valid leave records available.</div>',
                                    unsafe_allow_html=True
                                )

                        with insight_col2:
                            st.subheader("Employee-wise Leave Pattern")

                            if not valid_df.empty:
                                employee_summary = valid_df.groupby("employee_name").agg(
                                    total_requests=("leave_id", "count"),
                                    total_leave_days=("leave_days", "sum")
                                ).reset_index()

                                employee_summary = employee_summary.sort_values(
                                    by="total_leave_days",
                                    ascending=False
                                )

                                st.dataframe(
                                    employee_summary,
                                    use_container_width=True,
                                    height=240
                                )

                                top_employee = employee_summary.iloc[0]["employee_name"]
                                top_employee_days = employee_summary.iloc[0]["total_leave_days"]

                                st.markdown(f"""
                                <div class="insight-box">
                                    <b>Management Insight:</b><br>
                                    <b>{top_employee}</b> has the highest total leave days,
                                    with <b>{int(top_employee_days)}</b> day(s). This should be reviewed
                                    with business context and workload planning.
                                </div>
                                """, unsafe_allow_html=True)
                            else:
                                st.markdown(
                                    '<div class="empty-table-box">No valid leave records available.</div>',
                                    unsafe_allow_html=True
                                )

                        st.divider()

                        action_col1, action_col2 = st.columns(2)

                        with action_col1:
                            st.subheader("Pending Approval Attention")

                            pending_leaves = valid_df[valid_df["status"] == "Pending"]

                            if not pending_leaves.empty:
                                st.dataframe(
                                    pending_leaves[
                                        [
                                            "leave_id",
                                            "employee_name",
                                            "department",
                                            "leave_type",
                                            "start_date",
                                            "end_date",
                                            "leave_days",
                                            "reason"
                                        ]
                                    ],
                                    use_container_width=True,
                                    height=240
                                )
                            else:
                                st.markdown(
                                    '<div class="empty-table-box">No pending leave requests.</div>',
                                    unsafe_allow_html=True
                                )

                            if not pending_leaves.empty:
                                st.markdown(f"""
                                <div class="warning-box">
                                    <b>Action Required:</b><br>
                                    There are <b>{pending_count}</b> pending leave request(s).
                                    Managers should review them early to avoid scheduling conflicts.
                                </div>
                                """, unsafe_allow_html=True)
                            else:
                                st.markdown("""
                                <div class="success-box">
                                    <b>Good Status:</b><br>
                                    No pending leave requests. All leave requests are already actioned.
                                </div>
                                """, unsafe_allow_html=True)

                        with action_col2:
                            st.subheader("Upcoming Approved Leaves")

                            if not upcoming_approved.empty:
                                upcoming_approved = upcoming_approved.sort_values(by="start_date")

                                st.dataframe(
                                    upcoming_approved[
                                        [
                                            "leave_id",
                                            "employee_name",
                                            "department",
                                            "leave_type",
                                            "start_date",
                                            "end_date",
                                            "leave_days"
                                        ]
                                    ],
                                    use_container_width=True,
                                    height=240
                                )
                            else:
                                st.markdown(
                                    '<div class="empty-table-box">No upcoming approved leaves.</div>',
                                    unsafe_allow_html=True
                                )

                            if not upcoming_approved.empty:
                                st.markdown("""
                                <div class="warning-box">
                                    <b>Planning Reminder:</b><br>
                                    Upcoming approved leaves should be reviewed to ensure staff coverage,
                                    handover readiness, and work continuity.
                                </div>
                                """, unsafe_allow_html=True)
                            else:
                                st.markdown("""
                                <div class="success-box">
                                    <b>Good Status:</b><br>
                                    No upcoming approved leaves at the moment.
                                </div>
                                """, unsafe_allow_html=True)

                        st.divider()

                        if not invalid_df.empty:
                            st.subheader("Data Quality Alert")

                            st.error(
                                "Some old leave records have invalid date ranges where end date is earlier than start date. "
                                "These records are excluded from leave day calculations."
                            )

                            st.dataframe(
                                invalid_df[
                                    [
                                        "leave_id",
                                        "employee_name",
                                        "department",
                                        "leave_type",
                                        "start_date",
                                        "end_date",
                                        "status"
                                    ]
                                ],
                                use_container_width=True,
                                height=240
                            )

                        st.subheader("Overall Management View")

                        st.markdown("""
                        <div class="insight-box">
                            <b>Executive Summary:</b><br>
                            This dashboard provides a quick view of leave demand, approval workload,
                            employee availability, and operational coverage risks. Management should
                            focus on pending approvals, high leave concentration by department, and
                            upcoming approved leaves to maintain business continuity.
                        </div>
                        """, unsafe_allow_html=True)

                    else:
                        st.info("No leave data available for statistics.")
                else:
                    st.error("Unable to fetch leave statistics.")

            except requests.exceptions.ConnectionError:
                st.error("FastAPI backend is not running. Please start backend on port 8001.")