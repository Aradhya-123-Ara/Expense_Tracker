# app.py
import streamlit as st
import sqlite3
import pandas as pd
from datetime import date
import bcrypt

# -------------------------
# DATABASE
# -------------------------
conn = sqlite3.connect("finance.db", check_same_thread=False)
c = conn.cursor()

c.execute('''
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password_hash BLOB
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS expenses(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    date TEXT,
    category TEXT,
    amount REAL
)
''')
conn.commit()

# -------------------------
# FUNCTIONS
# -------------------------
def create_user(username, password):
    try:
        pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, pw_hash))
        conn.commit()
        return True
    except:
        return False

def authenticate_user(username, password):
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    user = c.fetchone()
    if user and bcrypt.checkpw(password.encode(), user[2]):
        return {"id": user[0], "username": user[1]}
    return None

def add_expense(user_id, exp_date, category, amount):
    c.execute("INSERT INTO expenses (user_id, date, category, amount) VALUES (?, ?, ?, ?)",
              (user_id, exp_date, category, amount))
    conn.commit()

def get_user_expenses(user_id):
    c.execute("SELECT date, category, amount FROM expenses WHERE user_id=?", (user_id,))
    rows = c.fetchall()
    return [{"date": r[0], "category": r[1], "amount": r[2]} for r in rows]

# -------------------------
# APP
# -------------------------
st.title("💰 Personal Finance Tracker")

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

menu = ["Login", "Sign Up"]
choice = st.sidebar.selectbox("Menu", menu)

# -------------------------
# AUTH
# -------------------------
if not st.session_state["logged_in"]:
    if choice == "Sign Up":
        st.subheader("Create Account")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Sign Up"):
            if create_user(username, password):
                st.success("Account created! Please login.")
            else:
                st.error("Username already exists!")

    if choice == "Login":
        st.subheader("Login")
        st.info("New user? Please Sign Up first.")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            user = authenticate_user(username, password)
            if user:
                st.session_state["logged_in"] = True
                st.session_state["user_id"] = user["id"]
                st.success(f"Welcome {username}!")
            else:
                st.error("Invalid credentials")

# -------------------------
# MAIN APP
# -------------------------
if st.session_state.get("logged_in"):

    st.subheader("Add Expense")

    exp_date = st.date_input("Date", value=date.today())
    category = st.selectbox("Category", ["Food", "Transport", "Bills", "Entertainment", "Other"])
    amount = st.number_input("Amount (₹)", min_value=0.0)

    if st.button("Add Expense"):
        add_expense(st.session_state["user_id"], str(exp_date), category, amount)
        st.success("Expense added!")

    # -------------------------
    # TABLE VIEW
    # -------------------------
    st.subheader("📋 Your Expenses")

    expenses = get_user_expenses(st.session_state["user_id"])

    if expenses:
        df = pd.DataFrame(expenses)
        df['date'] = pd.to_datetime(df['date'])

        st.dataframe(df.sort_values(by='date', ascending=False))

        # -------------------------
        # CATEGORY TOTAL
        # -------------------------
        st.subheader("📊 Category-wise Total")

        cat_sum = df.groupby('category')['amount'].sum().reset_index()
        st.dataframe(cat_sum)

        # -------------------------
        # PREDICTION
        # -------------------------
        st.subheader("🔮 Expected Next Month Expense")

        df['Month'] = df['date'].dt.to_period('M')
        monthly_sum = df.groupby('Month')['amount'].sum()

        if len(monthly_sum) >= 2:
            avg_spending = monthly_sum.mean()
            st.success(f"💰 You may spend approx ₹{avg_spending:.2f} next month.")
        else:
            st.info("Add at least 2 months of data for prediction.")

    else:
        st.info("No expenses added yet.")
