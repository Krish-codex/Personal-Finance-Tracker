import os
import json
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict
import pandas as pd

# Paths and defaults
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
CSV_PATH = os.path.join(BASE_DIR, 'data.csv')
JSON_PATH = os.path.join(BASE_DIR, 'data.json')
CATEGORIES_PATH = os.path.join(BASE_DIR, 'categories.json')
UNDO_PATH = os.path.join(BASE_DIR, 'undo.json')
RECURRING_PATH = os.path.join(BASE_DIR, 'recurring.json')
COLUMNS = ['date', 'amount', 'category', 'type']

# Per-user support: switch filenames when set
_CURRENT_USER: Optional[str] = None

def _user_paths():
    if _CURRENT_USER:
        return (os.path.join(BASE_DIR, f'data_{_CURRENT_USER}.csv'),
                os.path.join(BASE_DIR, f'data_{_CURRENT_USER}.json'))
    return (CSV_PATH, JSON_PATH)

def set_user(username: Optional[str]):
    """Set current user (simple per-user file switching)."""
    global _CURRENT_USER
    _CURRENT_USER = username

def init_db():
    csvp, _ = _user_paths()
    if not os.path.exists(csvp):
        pd.DataFrame(columns=COLUMNS).to_csv(csvp, index=False)

def _read_df() -> pd.DataFrame:
    csvp, _ = _user_paths()
    if not os.path.exists(csvp):
        init_db()
    try:
        return pd.read_csv(csvp)
    except Exception:
        return pd.DataFrame(columns=COLUMNS)

def _write_df(df: pd.DataFrame):
    csvp, _ = _user_paths()
    df.to_csv(csvp, index=False)

# Undo stack helpers
def _load_undo() -> List[dict]:
    try:
        if os.path.exists(UNDO_PATH):
            with open(UNDO_PATH, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return []

def _save_undo(stack: List[dict]):
    try:
        with open(UNDO_PATH, 'w') as f:
            json.dump(stack[-50:], f)
    except Exception:
        pass

def _push_undo(action: dict):
    stack = _load_undo()
    stack.append(action)
    _save_undo(stack)

def undo_last() -> bool:
    stack = _load_undo()
    if not stack:
        return False
    last = stack.pop()
    try:
        if last['action'] == 'add':
            df = _read_df()
            idx = last.get('index')
            if idx is not None and idx < len(df):
                df = df.drop(index=idx).reset_index(drop=True)
                _write_df(df)
        elif last['action'] == 'delete':
            df = _read_df()
            rows = last.get('rows', [])
            if rows:
                df = pd.concat([df, pd.DataFrame(rows, columns=COLUMNS)], ignore_index=True)
                _write_df(df)
        elif last['action'] == 'edit':
            df = _read_df()
            idx = last.get('index')
            old = last.get('old')
            if idx is not None and old is not None:
                for k, v in old.items():
                    df.at[idx, k] = v
                _write_df(df)
        _save_undo(stack)
        return True
    except Exception:
        return False

# Categories management
def get_categories() -> List[str]:
    default = ['Food', 'Rent', 'Utilities', 'Salary', 'Other']
    if os.path.exists(CATEGORIES_PATH):
        try:
            with open(CATEGORIES_PATH, 'r') as f:
                cats = json.load(f)
            if isinstance(cats, list):
                return cats
        except Exception:
            pass
    return default

def add_category(cat: str) -> bool:
    cats = get_categories()
    if cat in cats:
        return False
    cats.append(cat)
    with open(CATEGORIES_PATH, 'w') as f:
        json.dump(cats, f)
    return True

def remove_category(cat: str) -> bool:
    cats = get_categories()
    if cat not in cats:
        return False
    cats.remove(cat)
    with open(CATEGORIES_PATH, 'w') as f:
        json.dump(cats, f)
    return True

# Validation
def _validate_date(d: str) -> bool:
    try:
        datetime.strptime(d, '%Y-%m-%d')
        return True
    except Exception:
        return False

def add_transaction(date: str, amount, category: str, t_type: str):
    if not _validate_date(str(date)):
        raise ValueError('date must be YYYY-MM-DD')
    try:
        amount = float(amount)
        if amount <= 0:
            raise ValueError('amount must be positive')
    except Exception:
        raise ValueError('amount must be a number > 0')
    if category not in get_categories():
        raise ValueError('invalid category')
    if t_type not in ['income', 'expense']:
        raise ValueError("type must be 'income' or 'expense'")
    df = _read_df()
    new = pd.DataFrame([{'date': date, 'amount': amount, 'category': category, 'type': t_type}], columns=COLUMNS)
    if df.empty:
        df = new
    else:
        df = pd.concat([df, new], ignore_index=True)
    _write_df(df)
    _push_undo({'action': 'add', 'index': len(df)-1})

def edit_transaction(index: int, date: Optional[str] = None, amount: Optional[float] = None,
                     category: Optional[str] = None, t_type: Optional[str] = None):
    df = _read_df()
    if index < 0 or index >= len(df):
        raise IndexError('index out of range')
    old = df.loc[index].to_dict()
    if date is not None:
        if not _validate_date(str(date)):
            raise ValueError('date must be YYYY-MM-DD')
        df.at[index, 'date'] = date
    if amount is not None:
        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError('amount must be positive')
        except Exception:
            raise ValueError('amount must be a number > 0')
        df.at[index, 'amount'] = amount
    if category is not None:
        if category not in get_categories():
            raise ValueError('invalid category')
        df.at[index, 'category'] = category
    if t_type is not None:
        if t_type not in ['income', 'expense']:
            raise ValueError("type must be 'income' or 'expense'")
        df.at[index, 'type'] = t_type
    _write_df(df)
    _push_undo({'action': 'edit', 'index': index, 'old': old})

def delete_transaction(indices: List[int]):
    df = _read_df()
    rows = df.loc[indices].to_dict(orient='records') if len(indices) else []
    df = df.drop(index=indices).reset_index(drop=True)
    _write_df(df)
    _push_undo({'action': 'delete', 'rows': rows})

# Exports
def export_to_csv(df: pd.DataFrame, filename: str):
    df.to_csv(filename, index=False)

def export_to_json(df: pd.DataFrame, filename: str):
    df.to_json(filename, orient='records', lines=True)

def export_to_excel(df: pd.DataFrame, filename: str):
    df.to_excel(filename, index=False)

def export_to_pdf(df: pd.DataFrame, filename: str):
    from fpdf import FPDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Arial', size=10)
    colw = pdf.w / (len(df.columns) + 1)
    rowh = pdf.font_size * 1.6
    for c in df.columns:
        pdf.cell(colw, rowh, str(c), border=1)
    pdf.ln(rowh)
    for _, r in df.iterrows():
        for itm in r:
            pdf.cell(colw, rowh, str(itm), border=1)
        pdf.ln(rowh)
    pdf.output(filename)

# Summaries
def get_transactions() -> pd.DataFrame:
    return _read_df()

def get_summary():
    df = _read_df()
    total_income = df[df['type'] == 'income']['amount'].sum() if not df.empty else 0
    total_expense = df[df['type'] == 'expense']['amount'].sum() if not df.empty else 0
    return total_income, total_expense, total_income - total_expense

def monthly_trends():
    df = _read_df()
    if df.empty:
        return pd.DataFrame()
    df['month'] = pd.to_datetime(df['date']).dt.to_period('M')
    return df.groupby(['month', 'category'])['amount'].sum().unstack(fill_value=0)

# Recurring rules
def add_recurring(rule: Dict):
    rules = []
    if os.path.exists(RECURRING_PATH):
        try:
            with open(RECURRING_PATH, 'r') as f:
                rules = json.load(f)
        except Exception:
            rules = []
    rules.append(rule)
    with open(RECURRING_PATH, 'w') as f:
        json.dump(rules, f)

def apply_recurring(until_date: Optional[str] = None):
    if not os.path.exists(RECURRING_PATH):
        return
    with open(RECURRING_PATH, 'r') as f:
        rules = json.load(f)
    df = _read_df()
    for r in rules:
        start = datetime.strptime(r['start_date'], '%Y-%m-%d').date()
        end = date.today() if not until_date else datetime.strptime(until_date, '%Y-%m-%d').date()
        freq = r.get('freq', 'monthly')
        cur = start
        while cur <= end:
            exists = ((df['date'] == cur.strftime('%Y-%m-%d')) & (df['amount'] == r['amount']) & (df['category'] == r['category']) & (df['type'] == r['type'])).any()
            if not exists:
                new_row = pd.DataFrame([{'date': cur.strftime('%Y-%m-%d'), 'amount': r['amount'], 'category': r['category'], 'type': r['type']}], columns=COLUMNS)
                if df.empty:
                    df = new_row
                else:
                    df = pd.concat([df, new_row], ignore_index=True)
            if freq == 'daily':
                cur = cur + timedelta(days=1)
            elif freq == 'weekly':
                cur = cur + timedelta(weeks=1)
            else:
                month = cur.month + 1
                year = cur.year + (month - 1) // 12
                month = ((month - 1) % 12) + 1
                day = min(cur.day, 28)
                cur = date(year, month, day)
    _write_df(df)