import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px

def plot_spending_by_category(df):
    category_totals = df[df['type']=='expense'].groupby('category')['amount'].sum().reset_index()
    fig = px.bar(category_totals, x='category', y='amount', title='Spending by Category', labels={'amount':'Amount', 'category':'Category'})
    return fig

def plot_income_vs_expense(df):
    monthly = df.copy()
    monthly['month'] = pd.to_datetime(monthly['date']).dt.to_period('M').astype(str)
    summary = monthly.groupby(['month', 'type'])['amount'].sum().reset_index()
    fig = px.bar(summary, x='month', y='amount', color='type', barmode='group', title='Monthly Income vs Expense')
    return fig

def plot_pie_by_category(df):
    category_totals = df[df['type']=='expense'].groupby('category')['amount'].sum().reset_index()
    fig = px.pie(category_totals, values='amount', names='category', title='Expense Distribution by Category')
    return fig