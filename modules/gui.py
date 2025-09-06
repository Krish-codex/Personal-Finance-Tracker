import os
import sys
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from modules import data_handler

class FinanceApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Personal Finance Tracker')
        self.geometry('1000x700')
        self.style = ttk.Style(self)
        self.theme = tk.StringVar(value='default')
        self.font_size = tk.IntVar(value=12)
        self.create_widgets()
        data_handler.init_db()
        self.refresh_summary()
        self.refresh_table()
        self.refresh_dashboard()

    def add_hover(self, btn):
        def on_enter(e):
            btn.configure(style='Hover.TButton')
        def on_leave(e):
            btn.configure(style='TButton')
        btn.bind('<Enter>', on_enter)
        btn.bind('<Leave>', on_leave)
        self.style.configure('Hover.TButton', background='#0078D7', foreground='white')

    def set_font_recursive(self, widget, font):
        try:
            widget.configure(font=font)
        except:
            pass
        for child in widget.winfo_children():
            self.set_font_recursive(child, font)

    def set_font_size(self, size):
        self.font_size.set(size)
        self.update_fonts()

    def update_fonts(self):
        font = ("Segoe UI", self.font_size.get())
        self.set_font_recursive(self, font)

    def create_widgets(self):
        # Main Options Frame
        options_frame = ttk.LabelFrame(self, text='Main Options')
        options_frame.pack(fill='x', padx=10, pady=10)
        btn_add = ttk.Button(options_frame, text='Add Transaction', command=self.focus_add_transaction)
        btn_add.pack(side='left', padx=5)
        self.add_hover(btn_add)
        btn_summary = ttk.Button(options_frame, text='View Summary', command=self.show_summary_popup)
        btn_summary.pack(side='left', padx=5)
        self.add_hover(btn_summary)
        btn_trends = ttk.Button(options_frame, text='View Monthly Trends', command=self.show_monthly_trends)
        btn_trends.pack(side='left', padx=5)
        self.add_hover(btn_trends)
        btn_export_csv = ttk.Button(options_frame, text='Export to CSV', command=self.export_csv)
        btn_export_csv.pack(side='left', padx=5)
        self.add_hover(btn_export_csv)
        btn_export_json = ttk.Button(options_frame, text='Export to JSON', command=self.export_json)
        btn_export_json.pack(side='left', padx=5)
        self.add_hover(btn_export_json)
        btn_export_pdf = ttk.Button(options_frame, text='Export to PDF', command=self.export_pdf)
        btn_export_pdf.pack(side='left', padx=5)
        self.add_hover(btn_export_pdf)
        btn_visualize = ttk.Button(options_frame, text='Visualize Spending', command=self.visualize_spending)
        btn_visualize.pack(side='left', padx=5)
        self.add_hover(btn_visualize)
        btn_webapp = ttk.Button(options_frame, text='Run Web App', command=self.run_web_app)
        btn_webapp.pack(side='left', padx=5)
        self.add_hover(btn_webapp)
        btn_exit = ttk.Button(options_frame, text='Exit', command=self.quit)
        btn_exit.pack(side='left', padx=5)
        self.add_hover(btn_exit)

        # Theme & Font Switch
        theme_frame = ttk.Frame(self)
        theme_frame.pack(fill='x', padx=10, pady=5)
        ttk.Label(theme_frame, text='Theme:').pack(side='left')
        ttk.Combobox(theme_frame, textvariable=self.theme, values=['default', 'clam', 'alt', 'classic', 'dark']).pack(side='left')
        ttk.Button(theme_frame, text='Apply', command=self.apply_theme).pack(side='left', padx=5)
        ttk.Label(theme_frame, text='Font Size:').pack(side='left', padx=10)
        font_small = ttk.Button(theme_frame, text='A-', command=lambda: self.set_font_size(max(8, self.font_size.get()-2)))
        font_small.pack(side='left')
        font_large = ttk.Button(theme_frame, text='A+', command=lambda: self.set_font_size(min(32, self.font_size.get()+2)))
        font_large.pack(side='left')
        self.add_hover(font_small)
        self.add_hover(font_large)

        # Entry Frame
        entry_frame = ttk.LabelFrame(self, text='Add Transaction')
        entry_frame.pack(fill='x', padx=10, pady=10)
        ttk.Label(entry_frame, text='Date:').grid(row=0, column=0)
        self.date_entry = DateEntry(entry_frame)
        self.date_entry.grid(row=0, column=1)
        ttk.Label(entry_frame, text='Amount:').grid(row=0, column=2)
        self.amount_entry = ttk.Entry(entry_frame)
        self.amount_entry.grid(row=0, column=3)
        ttk.Label(entry_frame, text='Category:').grid(row=0, column=4)
        self.category_combo = ttk.Combobox(entry_frame, values=data_handler.get_categories())
        self.category_combo.grid(row=0, column=5)
        ttk.Label(entry_frame, text='Type:').grid(row=0, column=6)
        self.type_combo = ttk.Combobox(entry_frame, values=['income', 'expense'])
        self.type_combo.grid(row=0, column=7)
        add_btn = ttk.Button(entry_frame, text='Add', command=self.add_transaction)
        add_btn.grid(row=0, column=8, padx=5)
        self.add_hover(add_btn)
        manage_btn = ttk.Button(entry_frame, text='Manage Categories', command=self.manage_categories)
        manage_btn.grid(row=0, column=9, padx=5)
        self.add_hover(manage_btn)

        # Filter Frame
        filter_frame = ttk.LabelFrame(self, text='Filter/Search')
        filter_frame.pack(fill='x', padx=10, pady=5)
        ttk.Label(filter_frame, text='Category:').pack(side='left')
        self.filter_category = ttk.Combobox(filter_frame, values=['All'] + data_handler.get_categories())
        self.filter_category.set('All')
        self.filter_category.pack(side='left')
        ttk.Label(filter_frame, text='Type:').pack(side='left')
        self.filter_type = ttk.Combobox(filter_frame, values=['All', 'income', 'expense'])
        self.filter_type.set('All')
        self.filter_type.pack(side='left')
        ttk.Label(filter_frame, text='Date from:').pack(side='left')
        self.filter_date_from = DateEntry(filter_frame)
        self.filter_date_from.pack(side='left')
        ttk.Label(filter_frame, text='to').pack(side='left')
        self.filter_date_to = DateEntry(filter_frame)
        self.filter_date_to.pack(side='left')
        filter_btn = ttk.Button(filter_frame, text='Apply Filter', command=self.refresh_table)
        filter_btn.pack(side='left', padx=5)
        self.add_hover(filter_btn)

        # Summary Frame
        self.summary_frame = ttk.LabelFrame(self, text='Summary')
        self.summary_frame.pack(fill='x', padx=10, pady=10)
        self.summary_label = ttk.Label(self.summary_frame, text='')
        self.summary_label.pack()

        # Budget Alert
        self.budget_limit = tk.DoubleVar(value=1000)
        budget_frame = ttk.LabelFrame(self, text='Budget Alert')
        budget_frame.pack(fill='x', padx=10, pady=10)
        ttk.Label(budget_frame, text='Set Budget Limit:').pack(side='left')
        ttk.Entry(budget_frame, textvariable=self.budget_limit).pack(side='left')
        self.budget_alert_label = ttk.Label(budget_frame, text='')
        self.budget_alert_label.pack(side='left', padx=10)

        # Transactions Table
        table_frame = ttk.Frame(self)
        table_frame.pack(fill='both', expand=True, padx=10, pady=10)
        self.tree = ttk.Treeview(table_frame, columns=('Date', 'Amount', 'Category', 'Type'), show='headings')
        for col in ('Date', 'Amount', 'Category', 'Type'):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120)
        self.tree.pack(side='left', fill='both', expand=True)
        self.tree.bind('<Double-1>', self.edit_transaction)
        scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side='right', fill='y')

        # Dashboard Frame
        dashboard_frame = ttk.LabelFrame(self, text='Dashboard')
        dashboard_frame.pack(fill='both', expand=True, padx=10, pady=10)
        self.dashboard_canvas = tk.Canvas(dashboard_frame, width=900, height=300)
        self.dashboard_canvas.pack()

    def apply_theme(self):
        self.style.theme_use(self.theme.get())

    def add_transaction(self):
        try:
            date = self.date_entry.get()
            amount = float(self.amount_entry.get())
            category = self.category_combo.get()
            t_type = self.type_combo.get()
            if not category or not t_type:
                messagebox.showerror('Error', 'Category and Type are required.')
                return
            data_handler.add_transaction(date, amount, category, t_type)
            self.refresh_table()
            self.refresh_summary()
            self.check_budget_alert()
            self.refresh_dashboard()
            messagebox.showinfo('Success', 'Transaction added!')
        except Exception as e:
            messagebox.showerror('Error', str(e))

    def refresh_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        df = data_handler.get_transactions()
        # Apply filters
        cat = self.filter_category.get()
        t_type = self.filter_type.get()
        date_from = self.filter_date_from.get()
        date_to = self.filter_date_to.get()
        if cat != 'All':
            df = df[df['category'] == cat]
        if t_type != 'All':
            df = df[df['type'] == t_type]
        if date_from:
            df = df[pd.to_datetime(df['date']) >= pd.to_datetime(date_from)]
        if date_to:
            df = df[pd.to_datetime(df['date']) <= pd.to_datetime(date_to)]
        for idx, row in df.iterrows():
            self.tree.insert('', 'end', iid=idx, values=(row['date'], row['amount'], row['category'], row['type']))

    def refresh_summary(self):
        total_income, total_expense, savings = data_handler.get_summary()
        self.summary_label.config(text=f'Total Income: {total_income:.2f} | Total Expense: {total_expense:.2f} | Savings: {savings:.2f}')

    def check_budget_alert(self):
        _, total_expense, _ = data_handler.get_summary()
        if total_expense > self.budget_limit.get():
            self.budget_alert_label.config(text='Budget Exceeded!', foreground='red')
        else:
            self.budget_alert_label.config(text='Within Budget', foreground='green')

    def refresh_dashboard(self):
        df = data_handler.get_transactions()
        fig, axs = plt.subplots(1, 2, figsize=(9, 3))
        # Pie chart
        expense_df = df[df['type'] == 'expense']
        if not expense_df.empty:
            category_totals = expense_df.groupby('category')['amount'].sum()
            axs[0].pie(category_totals, labels=category_totals.index, autopct='%1.1f%%')
            axs[0].set_title('Expenses by Category')
        else:
            axs[0].text(0.5, 0.5, 'No expense data', ha='center')
        # Monthly trend
        if not df.empty:
            df['month'] = pd.to_datetime(df['date']).dt.to_period('M')
            monthly = df.groupby(['month', 'type'])['amount'].sum().unstack(fill_value=0)
            monthly.plot(ax=axs[1], kind='bar', stacked=True)
            axs[1].set_title('Monthly Income vs Expense')
        else:
            axs[1].text(0.5, 0.5, 'No data', ha='center')
        plt.tight_layout()
        self.dashboard_canvas.delete('all')
        canvas = FigureCanvasTkAgg(fig, master=self.dashboard_canvas)
        canvas.draw()
        canvas.get_tk_widget().pack()
        plt.close(fig)

    def edit_transaction(self, event):
        item = self.tree.focus()
        if not item:
            return
        idx = int(item)
        df = data_handler.get_transactions()
        row = df.iloc[idx]
        edit_win = tk.Toplevel(self)
        edit_win.title('Edit Transaction')
        tk.Label(edit_win, text='Date:').grid(row=0, column=0)
        date_entry = DateEntry(edit_win)
        date_entry.set_date(row['date'])
        date_entry.grid(row=0, column=1)
        tk.Label(edit_win, text='Amount:').grid(row=1, column=0)
        amount_entry = tk.Entry(edit_win)
        amount_entry.insert(0, row['amount'])
        amount_entry.grid(row=1, column=1)
        tk.Label(edit_win, text='Category:').grid(row=2, column=0)
        category_combo = ttk.Combobox(edit_win, values=data_handler.get_categories())
        category_combo.set(row['category'])
        category_combo.grid(row=2, column=1)
        tk.Label(edit_win, text='Type:').grid(row=3, column=0)
        type_combo = ttk.Combobox(edit_win, values=['income', 'expense'])
        type_combo.set(row['type'])
        type_combo.grid(row=3, column=1)
        def save_edit():
            try:
                data_handler.edit_transaction(
                    idx,
                    date=date_entry.get(),
                    amount=float(amount_entry.get()),
                    category=category_combo.get(),
                    t_type=type_combo.get()
                )
                self.refresh_table()
                self.refresh_summary()
                self.refresh_dashboard()
                messagebox.showinfo('Success', 'Transaction updated!')
                edit_win.destroy()
            except Exception as e:
                messagebox.showerror('Error', str(e))
        def delete_row():
            try:
                data_handler.delete_transaction([idx])
                self.refresh_table()
                self.refresh_summary()
                self.refresh_dashboard()
                messagebox.showinfo('Success', 'Transaction deleted!')
                edit_win.destroy()
            except Exception as e:
                messagebox.showerror('Error', str(e))
        save_btn = ttk.Button(edit_win, text='Save', command=save_edit)
        save_btn.grid(row=4, column=0)
        self.add_hover(save_btn)
        delete_btn = ttk.Button(edit_win, text='Delete', command=delete_row)
        delete_btn.grid(row=4, column=1)
        self.add_hover(delete_btn)

    def manage_categories(self):
        cat_win = tk.Toplevel(self)
        cat_win.title('Manage Categories')
        tk.Label(cat_win, text='Categories:').pack()
        cat_listbox = tk.Listbox(cat_win)
        for cat in data_handler.get_categories():
            cat_listbox.insert('end', cat)
        cat_listbox.pack()
        new_cat_entry = tk.Entry(cat_win)
        new_cat_entry.pack()
        def add_cat():
            new_cat = new_cat_entry.get()
            if new_cat and data_handler.add_category(new_cat):
                cat_listbox.insert('end', new_cat)
                self.category_combo['values'] = data_handler.get_categories()
                self.filter_category['values'] = ['All'] + data_handler.get_categories()
                messagebox.showinfo('Success', f'Category "{new_cat}" added!')
            elif new_cat:
                messagebox.showerror('Error', f'Category "{new_cat}" already exists!')
            else:
                messagebox.showerror('Error', 'Category name cannot be empty!')
        def remove_cat():
            sel = cat_listbox.curselection()
            if sel:
                cat = cat_listbox.get(sel)
                if data_handler.remove_category(cat):
                    cat_listbox.delete(sel)
                    self.category_combo['values'] = data_handler.get_categories()
                    self.filter_category['values'] = ['All'] + data_handler.get_categories()
                    messagebox.showinfo('Success', f'Category "{cat}" removed!')
                else:
                    messagebox.showerror('Error', f'Failed to remove category "{cat}"!')
        add_cat_btn = ttk.Button(cat_win, text='Add', command=add_cat)
        add_cat_btn.pack()
        self.add_hover(add_cat_btn)
        remove_cat_btn = ttk.Button(cat_win, text='Remove', command=remove_cat)
        remove_cat_btn.pack()
        self.add_hover(remove_cat_btn)

    def export_csv(self):
        try:
            df = data_handler.get_transactions()
            data_handler.export_to_csv(df, 'export.csv')
            messagebox.showinfo('Export', 'Exported to export.csv!')
        except Exception as e:
            messagebox.showerror('Export Error', str(e))

    def export_json(self):
        try:
            df = data_handler.get_transactions()
            data_handler.export_to_json(df, 'export.json')
            messagebox.showinfo('Export', 'Exported to export.json!')
        except Exception as e:
            messagebox.showerror('Export Error', str(e))

    def export_pdf(self):
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas as pdfcanvas
            df = data_handler.get_transactions()
            filename = 'report.pdf'
            c = pdfcanvas.Canvas(filename, pagesize=letter)
            c.drawString(30, 750, 'FinanceTracker Report')
            y = 700
            for i, row in df.iterrows():
                c.drawString(30, y, f"{row['date']} | {row['amount']:.2f} | {row['category']} | {row['type']}")
                y -= 20
                if y < 50:
                    c.showPage()
                    y = 750
            c.save()
            messagebox.showinfo('Export', f'Exported to {filename}!')
        except Exception as e:
            messagebox.showerror('Export Error', str(e))

    def focus_add_transaction(self):
        self.amount_entry.focus_set()

    def show_summary_popup(self):
        total_income, total_expense, savings = data_handler.get_summary()
        messagebox.showinfo('Summary', f'Total Income: {total_income:.2f}\nTotal Expense: {total_expense:.2f}\nSavings: {savings:.2f}')

    def show_monthly_trends(self):
        trends = data_handler.monthly_trends()
        top = tk.Toplevel(self)
        top.title('Monthly Trends')
        txt = tk.Text(top, width=80, height=20)
        txt.pack()
        txt.insert('end', str(trends))

    def visualize_spending(self):
        import modules.visualizer as visualizer
        df = data_handler.get_transactions()
        visualizer.plot_spending_by_category(df)
        visualizer.plot_income_vs_expense(df)
        visualizer.plot_pie_by_category(df)

    def run_web_app(self):
        try:
            subprocess.Popen(['python', '-m', 'streamlit', 'run', 'modules/streamlit_app.py'])
            messagebox.showinfo('Web App', 'Web App started!')
        except Exception as e:
            messagebox.showerror('Web App Error', str(e))

if __name__ == '__main__':
    app = FinanceApp()
    app.mainloop()