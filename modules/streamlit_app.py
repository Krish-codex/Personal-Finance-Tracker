import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import streamlit as st
import pandas as pd
from modules import data_handler, visualizer

st.set_page_config(page_title="Personal Finance Tracker", layout="wide")

# Sidebar - Category Management
st.sidebar.header("Manage Categories")
categories = data_handler.get_categories()
new_category = st.sidebar.text_input("Add New Category")
if st.sidebar.button("Add Category"):
    if new_category:
        if data_handler.add_category(new_category):
            st.sidebar.success(f"Category '{new_category}' added.")
            st.rerun()
        else:
            st.sidebar.warning(f"Category '{new_category}' already exists.")
    else:
        st.sidebar.error("Enter a category name.")
remove_category = st.sidebar.selectbox("Remove Category", categories)
if st.sidebar.button("Remove Category"):
    if data_handler.remove_category(remove_category):
        st.sidebar.success(f"Category '{remove_category}' removed.")
        st.rerun()
    else:
        st.sidebar.error(f"Category '{remove_category}' could not be removed.")

# --- User and Undo controls ---
st.sidebar.markdown("---")
st.sidebar.header("User / Utilities")
user = st.sidebar.text_input("Switch User (leave blank for default)")
if st.sidebar.button("Switch User"):
    data_handler.set_user(user if user else None)
    st.sidebar.success(f"Switched to user: {user or 'default'}")
    st.rerun()

if st.sidebar.button("Undo Last Action"):
    ok = data_handler.undo_last()
    if ok:
        st.sidebar.success("Last action undone.")
        st.rerun()
    else:
        st.sidebar.info("Nothing to undo.")

# CSV Importer
st.sidebar.markdown("---")
st.sidebar.header("Import Transactions (CSV)")
uploaded = st.sidebar.file_uploader("Upload CSV (date,amount,category,type)", type=['csv'])
if uploaded is not None:
    try:
        import io
        uploaded_df = pd.read_csv(io.BytesIO(uploaded.read()))
        # Expect columns: date, amount, category, type
        st.sidebar.write(f"Imported {len(uploaded_df)} rows")
        if st.sidebar.button("Append Imported to Dataset"):
            added = 0
            for _, row in uploaded_df.iterrows():
                try:
                    data_handler.add_transaction(str(row['date']), row['amount'], row['category'], row['type'])
                    added += 1
                except Exception as e:
                    # skip invalid rows
                    continue
            st.sidebar.success(f"Appended {added} rows")
            st.rerun()
    except Exception as e:
        st.sidebar.error(f"Failed to read CSV: {e}")

# Sidebar - Add Transaction
st.sidebar.header("Add Transaction")
date = st.sidebar.date_input("Date")
amount = st.sidebar.number_input("Amount", min_value=0.01, step=1.00, format="%.2f")
category = st.sidebar.selectbox("Category", categories)
t_type = st.sidebar.selectbox("Type", ["income", "expense"])
if st.sidebar.button("Add Transaction"):
    try:
        data_handler.add_transaction(str(date), amount, category, t_type)
        st.sidebar.success("Transaction added!")
        st.rerun()
    except Exception as e:
        st.sidebar.error(f"Error: {e}")

# Sidebar - Filters
st.sidebar.header("Filters")
filter_category = st.sidebar.multiselect("Category", categories, default=categories)
filter_type = st.sidebar.multiselect("Type", ["income", "expense"], default=["income", "expense"])
amount_range = st.sidebar.slider("Amount Range", 0.0, 10000.0, (0.0, 10000.0), step=1.00)

# Main - Data Table
st.title("FinanceTracker Dashboard")
df = data_handler.get_transactions()
if not df.empty:
    df_filtered = df[df["category"].isin(filter_category) & df["type"].isin(filter_type) & (df["amount"] >= amount_range[0]) & (df["amount"] <= amount_range[1])]
    st.dataframe(df_filtered, width='stretch')
else:
    st.info("No transactions found.")
    df_filtered = pd.DataFrame(columns=df.columns)  # Ensure df_filtered is always defined

# --- Transaction Editing ---
st.subheader("Edit Transaction")
if not df_filtered.empty:
    edit_index = st.number_input("Transaction Index to Edit", min_value=0, max_value=len(df_filtered)-1, step=1)
    edit_date = st.text_input("New Date (YYYY-MM-DD)", value=str(df_filtered.iloc[edit_index]['date']))
    edit_amount = st.number_input("New Amount", min_value=0.01, value=float(df_filtered.iloc[edit_index]['amount']), format="%.2f")
    edit_category = st.selectbox("New Category", categories, index=categories.index(df_filtered.iloc[edit_index]['category']) if df_filtered.iloc[edit_index]['category'] in categories else 0)
    edit_type = st.selectbox("New Type", ["income", "expense"], index=0 if df_filtered.iloc[edit_index]['type']=='income' else 1)
    if st.button("Update Transaction"):
        try:
            # Map filtered index to original index
            original_index = df_filtered.index[edit_index]
            data_handler.edit_transaction(
                original_index,
                date=edit_date,
                amount=edit_amount,
                category=edit_category,
                t_type=edit_type
            )
            st.success("Transaction updated!")
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")
else:
    st.info("No transactions to edit.")

# --- Advanced Export Options ---
st.subheader("Export Data")
if not df_filtered.empty:
    csv = df_filtered.to_csv(index=False).encode('utf-8')
    st.download_button("Download CSV", data=csv, file_name="export.csv", mime="text/csv")
    json_data = df_filtered.to_json(orient="records", lines=True).encode('utf-8')
    st.download_button("Download JSON", data=json_data, file_name="export.json", mime="application/json")
    import tempfile
    import os
    if st.button("Download PDF"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            data_handler.export_to_pdf(df_filtered, tmp.name)
            tmp.seek(0)
            st.download_button("Download PDF", data=tmp.read(), file_name="export.pdf", mime="application/pdf")
        os.unlink(tmp.name)
    if st.button("Download Excel"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            data_handler.export_to_excel(df_filtered, tmp.name)
            tmp.seek(0)
            st.download_button("Download Excel", data=tmp.read(), file_name="export.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        os.unlink(tmp.name)
else:
    st.info("No data to export.")

# Main - Summary
st.subheader("Summary")
total_income, total_expense, savings = data_handler.get_summary()
st.metric("Total Income", f"{total_income:.2f}")
st.metric("Total Expense", f"{total_expense:.2f}")
st.metric("Savings", f"{savings:.2f}")

# Budget Alert
budget_limit = st.sidebar.number_input("Budget Limit", min_value=0.0, value=1000.0, step=1.00, format="%.2f")
if budget_limit <= 0:
    st.warning("Set a budget limit greater than 0 to enable alerts and progress.")
else:
    if total_expense > budget_limit:
        st.error("Budget Exceeded!")
    else:
        st.success("Within Budget")
    # Show budget usage as a progress bar and percentage
    try:
        usage = float(total_expense) / float(budget_limit)
        usage_clamped = min(1.0, max(0.0, usage))
        st.progress(usage_clamped)
        st.caption(f"Budget usage: {usage * 100:.1f}% ({total_expense:.2f} / {budget_limit:.2f})")
    except Exception:
        pass

# Tabs for Visualizations & Analytics
st.subheader("Visualizations & Analytics")
tabs = st.tabs(["Spending by Category", "Monthly Trends", "Expense Pie Chart", "Monthly Summary"]) 

with tabs[0]:
    expense_df = df_filtered[df_filtered["type"] == "expense"]
    if not expense_df.empty:
        fig = visualizer.plot_spending_by_category(expense_df)
        st.plotly_chart(fig, width='stretch')
    else:
        st.info("No expense data to show.")

with tabs[1]:
    if not df_filtered.empty:
        fig = visualizer.plot_income_vs_expense(df_filtered)
        st.plotly_chart(fig, width='stretch')
    else:
        st.info("No data to show.")

with tabs[2]:
    expense_df = df_filtered[df_filtered["type"] == "expense"]
    if not expense_df.empty:
        fig = visualizer.plot_pie_by_category(expense_df)
        st.plotly_chart(fig, width='stretch')
    else:
        st.info("No expense data to show.")

with tabs[3]:
    st.write("### Monthly Summary Table")
    try:
        monthly = data_handler.monthly_trends()
        st.dataframe(monthly, width='stretch')
    except Exception as e:
        st.info(f"No monthly summary available. {e}")

# Delete Transactions
st.subheader("Delete Transactions")
selected_rows = st.multiselect("Select rows to delete", df_filtered.index.tolist())
if st.button("Delete Selected"):
    if selected_rows:
        try:
            data_handler.delete_transaction(selected_rows)
            st.success("Deleted selected transactions.")
            st.rerun()
        except Exception as e:
            st.error(f"Error deleting transactions: {e}")
    else:
        st.error("No rows selected.")