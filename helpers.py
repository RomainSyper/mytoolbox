import os
from flask import redirect, render_template, session
from functools import wraps
from datetime import datetime
from fpdf import FPDF, HTMLMixin
from html import unescape
from bs4 import BeautifulSoup

from models import db, User, QRCode, PDF


# Vérification de connexion de l'utilisateur
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

# Suppression des QR codes et PDFs expirés
def cleanup(user_id):
    today = datetime.now()

    # QR Codes expirés
    expired_qrcodes = QRCode.query.filter(QRCode.user_id == user_id, QRCode.expiration_date < today).all()
    for qrcode in expired_qrcodes:
        file_path = os.path.join("static", "qrcodes", f"{qrcode.value}.png")
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Deleted file: {file_path}")
        else:
            print(f"File not found: {file_path}")
        db.session.delete(qrcode)
        print(f"Deleted QR Code with ID: {qrcode.id}")

    # PDFs expirés
    expired_pdfs = PDF.query.filter(PDF.user_id == user_id, PDF.expiration_date < today).all()
    for pdf in expired_pdfs:
        file_path = os.path.join("private_pdfs", pdf.filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Deleted file: {file_path}")
        else:
            print(f"File not found: {file_path}")
        db.session.delete(pdf)
        print(f"Deleted PDF with ID: {pdf.id}")

    # Commit des modifications
    db.session.commit()

# Supprimer les heures/minutes/secondes pour n'afficher que la date
def date_only(value):
    if isinstance(value, datetime):
        return value.strftime('%Y-%m-%d')
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S").strftime('%Y-%m-%d')
    except Exception:
        return value

class MyPDF(FPDF, HTMLMixin):
    def __init__(self):
        super().__init__()

    def render_html_content(self, html_content):
        # Utilise le moteur HTML de fpdf2 pour conserver le formatage
        self.write_html(html_content)
