import os
import qrcode
import secrets
import html
from flask import Flask, render_template, request, redirect, session, url_for, flash, send_file
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

from helpers import login_required, cleanup, date_only, MyPDF
from models import db, User, QRCode, PDF

app = Flask(__name__)

app.add_template_filter(date_only, 'date_only')

# Flask session configuration
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"

Session(app)

# SQLAlchemy configuration
app.config["SQLALCHEMY_DATABASE_URI"] = "[REDACTED]"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

# Migration
migrate = Migrate(app, db)


@app.route("/")
def index():
    if session.get("user_id"):
        user = User.query.get(session["user_id"])
        username = user.username if user else None
        return render_template("index.html", username=username)
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect("/")

    username_valid = None
    password_valid = None
    confirmation_valid = None

    if request.method == "POST":
        username = request.form.get("username").strip()
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        username_valid = bool(username)
        password_valid = bool(password and len(password) >= 6)
        confirmation_valid = password == confirmation

        if not username_valid or not password_valid or not confirmation_valid:
            return render_template("register.html",
                                   username_valid=username_valid,
                                   password_valid=password_valid,
                                   confirmation_valid=confirmation_valid,
                                   username=username)

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            username_valid = False
            return render_template("register.html",
                                   username_valid=username_valid,
                                   password_valid=password_valid,
                                   confirmation_valid=confirmation_valid,
                                   username=username)

        try:
            hash = generate_password_hash(password)
            user = User(username=username, hash=hash)
            db.session.add(user)
            db.session.commit()
        except Exception as e:
            app.logger.error(f"Erreur lors de l'ajout de l'utilisateur : {e}")
            return render_template("register.html",
                                   username_valid=False,
                                   password_valid=True,
                                   confirmation_valid=True,
                                   username=username)

        flash("Registration successful!", "success")
        return redirect("/login")

    return render_template("register.html",
                           username_valid=username_valid,
                           password_valid=password_valid,
                           confirmation_valid=confirmation_valid)


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect("/")
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()
        if not user or not check_password_hash(user.hash, password):
            flash("Invalid username or password", "error")
            return redirect("/login")
        session["user_id"] = user.id
        cleanup(session["user_id"])
        return redirect("/")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/qrcode", methods=["GET", "POST"])
@login_required
def generate_qrcode():
    if request.method == "POST":
        link = request.form.get("link")
        name = request.form.get("name")
        expiration = request.form.get("expiration")
        
        if not link or not name:
            flash("Both link and name are required", "error")
            return render_template("qrcode.html")
        
        today = datetime.today()
        expiration_date = datetime.strptime(expiration, "%Y-%m-%d") if expiration else today + timedelta(days=30)
        if expiration_date > today + timedelta(days=30) or expiration_date <= today:
            flash("Invalid expiration date", "error")
            return render_template("qrcode.html")
        
        qr = qrcode.QRCode(
            version=3,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=15,
            border=2,
        )
        qr.add_data(link)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        safe_name = secure_filename(name)  # Sécuriser le nom pour l'utiliser dans un fichier
        filename = f"{session['user_id']}_{safe_name}.png"  # Nom du fichier basé sur l'ID de l'utilisateur
        
        # Sauvegarder l'image dans le répertoire approprié
        path = os.path.join("static", "qrcodes", filename)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        img.save(path)
        
        # Enregistrer les informations dans la base de données
        qr_code = QRCode(
            user_id=session["user_id"], 
            value=name,  # Nom complet du QR Code
            filename=filename,  # Nom du fichier généré
            expiration_date=expiration_date, 
            link=link
        )
        db.session.add(qr_code)
        db.session.commit()
        
        flash("QR Code successfully generated!", "success")
        return redirect("/panel")
    
    return render_template("qrcode.html")


@app.route("/delete_qrcode/<int:qrcode_id>", methods=["POST"])
@login_required
def delete_qrcode(qrcode_id):
    qrcode = QRCode.query.filter_by(id=qrcode_id, user_id=session["user_id"]).first()
    if not qrcode:
        flash("QR Code not found or you do not have permission to delete it", "error")
        return redirect(url_for("panel"))
    file_path = os.path.join("static", "qrcodes", f"{qrcode.filename}")
    if os.path.exists(file_path):
        os.remove(file_path)
    db.session.delete(qrcode)
    db.session.commit()
    flash("QR Code deleted successfully!", "success")
    return redirect(url_for("panel"))

@app.route("/pdf", methods=["GET", "POST"])
@login_required
def pdf_generator():
    if request.method == "POST":
        name = request.form.get("name")
        content = request.form.get("content")
        expiration = request.form.get("expiration")
        
        # Vérification des champs nécessaires
        if not name or not content:
            flash("Require a name and some content", "error")
            return render_template("pdf.html")

        # Décodage du contenu HTML
        content = html.unescape(content)

        # Gestion de la date d'expiration
        today = datetime.today()
        expiration_date = datetime.strptime(expiration, "%Y-%m-%d") if expiration else today + timedelta(days=30)
        if expiration_date > today + timedelta(days=30) or expiration_date <= today:
            flash("Invalid expiration date", "error")
            return render_template("pdf.html")

        # Génération du PDF avec rendu HTML
        pdf = MyPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        pdf.render_html_content(content)  # <- méthode mise à jour

        # Sauvegarde du PDF
        user_id = session["user_id"]
        safe_name = secure_filename(name)
        filename = f"{user_id}_{safe_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
        path = os.path.join("private_pdfs", filename)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        pdf.output(path)

        # Sauvegarde dans la base de données
        new_pdf = PDF(user_id=user_id, name=name, filename=filename, expiration_date=expiration_date)
        db.session.add(new_pdf)
        db.session.commit()

        flash("PDF generated successfully!", "success")
        return redirect("/panel")
    
    return render_template("pdf.html")


@app.route("/download_pdf/<filename>", methods=["GET"])
@login_required
def download_pdf(filename):
    pdf = PDF.query.filter_by(filename=filename, user_id=session["user_id"]).first()
    if not pdf:
        flash("PDF not found or you do not have permission to download it", "error")
        return redirect(url_for("panel"))
    path = os.path.join("private_pdfs", filename)
    if not os.path.exists(path):
        flash("File not found", "error")
        return redirect(url_for("panel"))
    return send_file(path, as_attachment=True)

@app.route("/delete_pdf/<filename>", methods=["POST"])
@login_required
def delete_pdf(filename):
    pdf = PDF.query.filter_by(filename=filename, user_id=session["user_id"]).first()
    if not pdf:
        flash("PDF not found or you do not have permission to delete it", "error")
        return redirect(url_for("panel"))
    file_path = os.path.join("private_pdfs", filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    db.session.delete(pdf)
    db.session.commit()
    flash("PDF deleted successfully!", "success")
    return redirect(url_for("panel"))

@app.route("/create_qrcode_for_pdf", methods=["POST"])
@login_required
def create_qrcode_for_pdf():
    pdf_id = request.form.get("pdf_id")
    name = request.form.get("qrcode_name")
    expiration = request.form.get("expiration")
    password_required = request.form.get("password_protect")

    if not name or not expiration:
        flash("Name and expiration date needed", "error")
        return redirect(url_for("panel"))

    today = datetime.today()
    expiration_date = datetime.strptime(expiration, "%Y-%m-%d") if expiration else today + timedelta(days=30)

    if expiration_date > today + timedelta(days=30):
        flash("Expiration date is greater than 30 days", "error")
        return redirect(url_for("panel"))

    if expiration_date <= today:
        flash("Expiration date cannot be today or before", "error")
        return redirect(url_for("panel"))

    pdf = PDF.query.filter_by(id=pdf_id, user_id=session["user_id"]).first()
    if not pdf:
        flash("PDF not found", "error")
        return redirect(url_for("panel"))

    link = url_for("shared_pdf", filename=pdf.filename, _external=True)

    if password_required:
        password = secrets.token_urlsafe(12)
    else:
        password = None

    # Création du QR Code
    img = qrcode.make(link)
    safe_name = secure_filename(name)
    user_id = session["user_id"]
    filename = f"{session['user_id']}_{safe_name}.png"
    path = os.path.join("static", "qrcodes", filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)

    # Sauvegarde dans la base de données
    qr_code = QRCode(
        user_id=user_id, 
        value=safe_name,  # Nom complet du QR Code
        filename=filename,  # Nom du fichier généré
        expiration_date=expiration_date,
        link=link,
        pdf_id=pdf.id,
        password=password
    )
    db.session.add(qr_code)
    db.session.commit()

    flash("QR Code successfully generated !", "success")
    return redirect(url_for("panel"))

@app.route("/panel")
@login_required
def panel():
    # Récupérer les QR codes et les PDFs pour l'utilisateur
    qrcodes = QRCode.query.filter_by(user_id=session["user_id"]).all()
    pdfs = PDF.query.filter_by(user_id=session["user_id"]).all()

    # Créer le dictionnaire `qr_info` avec l'ID des PDFs comme clés
    qr_info = {}
    for qr in qrcodes:
        qr_info[qr.pdf_id] = {"link": qr.link, "password": qr.password}

    # Passer `qr_info` dans le contexte du template
    return render_template("panel.html", qrcodes=qrcodes, pdfs=pdfs, qr_info=qr_info)


@app.route("/shared/<filename>", methods=["GET", "POST"])
def shared_pdf(filename):
    pdf = PDF.query.filter_by(filename=filename).first()
    if not pdf:
        return "PDF not found", 404
    file_path = os.path.join("private_pdfs", filename)
    if not os.path.exists(file_path):
        return "File not found", 404

    # If password is required
    qrcode = QRCode.query.filter_by(pdf_id=pdf.id).first()
    if qrcode and qrcode.password:
        if request.method == "POST":
            entered_password = request.form.get("password")
            if entered_password == qrcode.password:
                return send_file(file_path, as_attachment=True)
            else:
                flash("Incorrect password", "error")
                return render_template("password_prompt.html", filename=filename)
        return render_template("password_prompt.html", filename=filename)

    # If no password is required
    return send_file(file_path, as_attachment=True)
