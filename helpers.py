import os
from flask import redirect, render_template, session
from functools import wraps
from cs50 import SQL
from datetime import datetime
from fpdf import FPDF, HTMLMixin

db = SQL("sqlite:///toolbox.db")

# From finance (CS50 pset problem)
def login_required(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function

# Deleting the expired qrcodes and pdf
def cleanup(user_id):
    today = datetime.now()

    expired_qrcodes = db.execute("SELECT id, value, expiration_date FROM qrcodes WHERE user_id = ? AND expiration_date < ?", user_id, today)
    expired_pdfs = db.execute("SELECT id, filename, expiration_date FROM pdfs WHERE user_id = ? AND expiration_date < ?", user_id, today)

    for qrcode in expired_qrcodes:
        filename = qrcode["value"]
        file_path = os.path.join("static", "qrcodes", f"{filename}.png")

        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"File not found : {file_path}")
        else:
            print(f"File not found : {file_path}")

        db.execute("DELETE FROM qrcodes WHERE id = ?", qrcode["id"])
        print(f"Row delete for ID : {qrcode['id']}")

    for pdf in expired_pdfs:
        filename = pdf["filename"]
        file_path = os.path.join("private_pdfs", filename)

        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"File not found : {file_path}")
        else:
            print(f"File not found : {file_path}")

        db.execute("DELETE FROM pdfs WHERE id = ?", pdf["id"])
        print(f"Row delete for ID : {pdf["id"]}")

# Deleting the h-m-s to display only the date
def date_only(value):
    if isinstance(value, datetime):
        return value.strftime('%Y-%m-%d')
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S").strftime('%Y-%m-%d')
    except Exception:
        return value

class MyPDF(FPDF, HTMLMixin):
    pass
