"""Expenses Tracker - Streamlit app with AI insights via Ollama (local) or Groq (cloud)."""

import streamlit as st
from datetime import datetime, date, timedelta
import pandas as pd
import plotly.express as px

import db
import auth
from aggregator import aggregate_expenses
from ai_insights import generate_insights, _get_ai_status

# Page config
st.set_page_config(page_title="Expenses Tracker", page_icon="💰", layout="wide")

# Initialize database
db.init_db()

# Session state
if "expenses" not in st.session_state:
    st.session_state.expenses = []


def render_login():
    """Render login/signup form."""
    tab1, tab2 = st.tabs(["Sign in", "Sign up"])

    with tab1:
        with st.form("signin_form"):
            email = st.text_input("Email", type="default")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Sign in"):
                if email and password:
                    ok, err = auth.sign_in(email, password)
                    if ok:
                        st.success("Signed in!")
                        st.rerun()
                    else:
                        st.error(err)
                else:
                    st.warning("Enter email and password")

    with tab2:
        with st.form("signup_form"):
            email = st.text_input("Email", key="su_email")
            password = st.text_input("Password", type="password", key="su_pass")
            if st.form_submit_button("Create account"):
                if email and password:
                    if len(password) < 6:
                        st.error("Password must be at least 6 characters")
                    else:
                        ok, err = auth.sign_up(email, password)
                        if ok:
                            st.success(err)
                            st.rerun()
                        else:
                            st.error(err)
                else:
                    st.warning("Enter email and password")


def main():
    user = auth.get_current_user()
    user_id = user["id"] if user else None

    st.title("💰 Expenses Tracker")
    st.caption("Track expenses and get AI-powered insights")

    # Sidebar - Auth + Add expense
    with st.sidebar:
        if user:
            st.caption(f"Signed in as **{user['email']}**")
            if st.button("Sign out"):
                auth.sign_out()
                st.rerun()
            st.divider()

        st.header("Add Expense")
        with st.form("add_expense_form", clear_on_submit=True):
            amount = st.number_input("Amount", min_value=0.01, step=0.01, format="%.2f")
            category = st.selectbox("Category", db.DEFAULT_CATEGORIES)
            expense_date = st.date_input("Date", value=date.today())
            description = st.text_input("Description", placeholder="Optional note")
            submitted = st.form_submit_button("Add")

            if submitted and amount > 0:
                db.add_expense(
                    amount=float(amount),
                    category=category,
                    date=expense_date.isoformat(),
                    description=description.strip(),
                    user_id=user_id,
                )
                st.success("Expense added!")
                st.rerun()

        st.divider()
        st.caption(f"AI insights: {_get_ai_status()}")

    # Date range filter
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        date_from = st.date_input("From", value=date.today() - timedelta(days=90))
    with col2:
        date_to = st.date_input("To", value=date.today())

    # Fetch expenses
    expenses = db.get_all_expenses(
        date_from=date_from.isoformat(),
        date_to=date_to.isoformat(),
        user_id=user_id,
    )

    if not expenses:
        st.info("No expenses in this period. Add some via the sidebar!")
        return

    # Tabs: Expenses | Charts | AI Insights
    tab1, tab2, tab3 = st.tabs(["📋 Expenses", "📊 Charts", "🤖 AI Insights"])

    with tab1:
        df = pd.DataFrame(expenses)
        df["date"] = pd.to_datetime(df["date"]).dt.date

        # Summary stats
        total = df["amount"].sum()
        st.metric("Total Spending", f"${total:,.2f}")
        st.dataframe(
            df[["date", "amount", "category", "description"]],
            use_container_width=True,
            hide_index=True,
        )

        # Delete expense
        st.subheader("Delete Expense")
        with st.form("delete_form"):
            options = [(e["id"], f"${e['amount']:.2f} - {e['category']} ({e['date']})") for e in expenses]
            to_delete = st.selectbox("Select expense to delete", options, format_func=lambda x: x[1])
            if st.form_submit_button("Delete"):
                db.delete_expense(to_delete[0], user_id=user_id)
                st.success("Deleted!")
                st.rerun()

    with tab2:
        by_category = df.groupby("category")["amount"].sum().sort_values(ascending=False)
        col_a, col_b = st.columns(2)

        with col_b:
            st.subheader("Spending by Category")
            st.bar_chart(by_category)

        with col_a:
            st.subheader("Category Share")
            fig = px.pie(
                values=by_category.values,
                names=by_category.index,
                title="",
                hole=0.4,
            )
            st.plotly_chart(fig, use_container_width=True)

        # Monthly trend
        df["month"] = pd.to_datetime(df["date"]).dt.to_period("M").astype(str)
        monthly = df.groupby("month")["amount"].sum()
        st.subheader("Monthly Trend")
        st.line_chart(monthly)

    with tab3:
        st.subheader("AI-Powered Insights")
        st.caption("Analyzes your spending patterns and suggests improvements")

        if st.button("Generate Insights", type="primary"):
            aggregated = aggregate_expenses(expenses)
            with st.spinner("Analyzing your expenses..."):
                insights = generate_insights(aggregated)
            st.markdown(insights)
            st.session_state.last_insights = insights
        elif "last_insights" in st.session_state:
            st.markdown(st.session_state.last_insights)


if __name__ == "__main__":
    # Auth gate: when Supabase + Auth configured, require login
    if auth.is_auth_configured():
        user = auth.get_current_user()
        if not user:
            st.title("💰 Expenses Tracker")
            st.caption("Sign in to access your expenses")
            render_login()
        else:
            main()
    else:
        # No auth configured (e.g. local SQLite) - run without auth
        main()
