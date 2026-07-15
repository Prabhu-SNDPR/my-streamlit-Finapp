import streamlit as st
import sqlite3
import random
import string
import os

# --- ADD THIS RIGHT AFTER YOUR IMPORTS ---

# 1. Page Config (Make sure this is the VERY FIRST streamlit command)
st.set_page_config(
    page_title="My Streamlit App",
    page_icon="🎯",
    layout="centered"
)

# 2. Styling (Color and font size)
st.markdown(
    """
    <style>
    h1 {
        color: #2E4053 !important;  /* Change this hex code to match your logo */
        font-size: 38px !important;
    }
    p, span, label {
        color: #2C3E50 !important;
        font-size: 18px !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# 3. Display the Logo
LOGO_FILENAME = "SNDPRlogo.png"  # <-- Change this to your logo's file name

if os.path.exists(LOGO_FILENAME):
    st.image(LOGO_FILENAME, width=150) 
else:
   st.warning("Logo image 'SNDPRlogo.png' not found in the repository folder.")

# ----------------------------------------

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect("SNDPR-Group.db")
    cursor = conn.cursor()
    
    # Create Employee Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            empid TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    
    # Create Customer Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            custid TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# --- HELPER FUNCTIONS ---
def generate_unique_id(prefix):
    """Generates an ID like EMP-12345 or CUST-12345"""
    digits = "".join(random.choices(string.digits, k=5))
    return f"{prefix}-{digits}"

def register_user(user_type, name, phone, email, password):
    conn = sqlite3.connect("SNDPR-Group.db")
    cursor = conn.cursor()
    try:
        if user_type == "Employee":
            unique_id = generate_unique_id("EMP")
            cursor.execute(
                "INSERT INTO employees (empid, name, phone, email, password) VALUES (?, ?, ?, ?, ?)",
                (unique_id, name, phone, email, password)
            )
            role_id = f"Employee ID: {unique_id}"
        else:
            unique_id = generate_unique_id("CUST")
            cursor.execute(
                "INSERT INTO customers (custid, name, phone, email, password) VALUES (?, ?, ?, ?, ?)",
                (unique_id, name, phone, email, password)
            )
            role_id = f"Customer ID: {unique_id}"
            
        conn.commit()
        return True, unique_id
    except sqlite3.IntegrityError:
        return False, "Email already exists in our database."
    finally:
        conn.close()

def verify_user(user_type, user_id, password):
    conn = sqlite3.connect("SNDPR-Group.db")
    cursor = conn.cursor()
    if user_type == "Employee":
        cursor.execute("SELECT name FROM employees WHERE empid = ? AND password = ?", (user_id, password))
    else:
        cursor.execute("SELECT name FROM customers WHERE custid = ? AND password = ?", (user_id, password))
    user = cursor.fetchone()
    conn.close()
    return user[0] if user else None


# --- APPLICATION UI ---
st.set_page_config(page_title="SNDPR-Groups", layout="centered")
init_db()

# Session State Initialization
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_role = None
    st.session_state.user_id = None
    st.session_state.user_name = None

# Logout Action
if st.session_state.logged_in:
    if st.sidebar.button("Log Out"):
        st.session_state.logged_in = False
        st.session_state.user_role = None
        st.session_state.user_id = None
        st.session_state.user_name = None
        st.rerun()

# --- 1. GATEWAY SCREEN (Login / Registration) ---
if not st.session_state.logged_in:
    st.title("SNDPR Groups")
    
    # Selection: Login vs Create Account
    action = st.radio("Choose Action", ["Login with Existing Account", "Create New Account"], horizontal=True)
    
    # Selection: Employee vs Customer
    user_type = st.selectbox("Select User Type", ["Employee", "Customer"])
    
    st.markdown("---")
    
    if action == "Create New Account":
        st.subheader(f"Register as a new {user_type}")
        
        with st.form("register_form", clear_on_submit=True):
            name = st.text_input("Name")
            phone = st.text_input("Phone Number")
            email = st.text_input("Mail ID")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Submit")
            
            if submit:
                if not name or not phone or not email or not password:
                    st.error("Please fill out all fields.")
                else:
                    success, result = register_user(user_type, name, phone, email, password)
                    if success:
                        st.success(f"Registration Successful! Your unique ID is: **{result}**")
                        st.info("Write this ID down! Use it to login on the 'Login with Existing Account' tab.")
                    else:
                        st.error(f"Registration Failed: {result}")
                        
    elif action == "Login with Existing Account":
        st.subheader(f"{user_type} Login")
        
        with st.form("login_form"):
            user_id = st.text_input(f"Enter {user_type} ID (e.g. {'EMP-XXXXX' if user_type == 'Employee' else 'CUST-XXXXX'})")
            password = st.text_input("Password", type="password")
            login_btn = st.form_submit_button("Login")
            
            if login_btn:
                user_name = verify_user(user_type, user_id, password)
                if user_name:
                    st.session_state.logged_in = True
                    st.session_state.user_role = user_type
                    st.session_state.user_id = user_id
                    st.session_state.user_name = user_name
                    st.success("Login Successful!")
                    st.rerun()
                else:
                    st.error("Invalid ID or Password. Please try again.")

# --- 2. LOGGED IN PORTALS ---
else:
    st.title(f"Welcome, {st.session_state.user_name} 👋")
    st.caption(f"Logged in as {st.session_state.user_role} ({st.session_state.user_id})")
    st.markdown("---")
    
    # EMPLOYEE DASHBOARD
    if st.session_state.user_role == "Employee":
        tab1, tab2, tab3 = st.tabs(["📅 Add Attendance", "💵 Payslip", "✉️ Offer Letter"])
        
        with tab1:
            st.header("Mark Daily Attendance")
            date = st.date_input("Select Date")
            status = st.radio("Status", ["Present", "Sick Leave", "Paid Leave"])
            if st.button("Submit Attendance"):
                st.success(f"Attendance marked as '{status}' for {date}.")
                
        with tab2:
            st.header("Your Payslips")
            st.info("No payslips released for this month yet.")
            st.download_button("Download Previous Payslip (PDF Template)", "Sample Payslip Content", file_name="payslip.txt")
            
        with tab3:
            st.header("Your Offer Letter")
            st.write("Below is your official appointment letter.")
            st.info("Drafted on Employee onboard date. Contact HR for revisions.")
            
    # CUSTOMER DASHBOARD
    elif st.session_state.user_role == "Customer":
        tab1, tab2, tab3 = st.tabs(["💰 Active Loan", "✅ Closed Loan", "📝 Request Loan"])
        
        with tab1:
            st.header("Active Loans")
            # Static mock up of loan data
            st.metric(label="Currently Available Loan Amount", value="$14,500", delta="- $500 this month")
            st.write("**Next payment due date:** August 1st")
            
        with tab2:
            st.header("Closed Loans history")
            st.dataframe({
                "Loan Reference": ["LN-9831", "LN-4412"],
                "Amount Paid": ["$5,000", "$12,000"],
                "Total Premium Paid": ["$5,400", "$13,100"],
                "Status": ["Fully Paid & Closed", "Fully Paid & Closed"]
            })
            
        with tab3:
            st.header("Apply for a New Loan")
            with st.form("loan_request_form"):
                amount = st.number_input("Requested Loan Amount", min_value=500, max_value=100000, value=5000)
                tenure = st.selectbox("Tenure Plan", ["6 Months", "12 Months", "24 Months", "36 Months"])
                purpose = st.text_area("Purpose of Loan")
                submit_req = st.form_submit_button("Submit Loan Application")
                
                if submit_req:
                    st.success("Your application has been received! Our loan officers will contact you shortly.")
