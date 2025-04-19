import os
import qrcode
import secrets

from cs50 import SQL
from flask import Flask, render_template, request, redirect, session, url_for, flash, send_file
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from fpdf import FPDF, HTMLMixin

from helpers import login_required, cleanup, date_only, MyPDF

app = Flask(__name__)

app.add_template_filter(date_only, 'date_only')

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = SQL("sqlite:///toolbox.db")

# Homepage
@app.route("/")
def index():
    if session.get("user_id"):
        row = db.execute("SELECT username FROM users WHERE id = ?", session["user_id"])
        username = row[0]["username"]
        return render_template("index.html", username=username)
    else:
        return render_template("index.html")

# Register
@app.route("/register", methods=["GET", "POST"])
def register():

    if session.get("user_id"):
        return redirect("/")

    username_valid = None
    password_valid = None
    confirmation_valid = None

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if not username:
            username_valid = False
        else:
            username_valid = True

        if not password or len(password) < 6:
            password_valid = False
        else:
            password_valid = True

        if password != confirmation:
            confirmation_valid = False
        else:
            confirmation_valid = True

        if not username_valid or not password_valid or not confirmation_valid:
            return render_template("register.html",
                                   username_valid=username_valid,
                                   password_valid=password_valid,
                                   confirmation_valid=confirmation_valid,
                                   username=username)

        hash = generate_password_hash(password)

        try:
            db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, hash)
        except:
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


# Login
@app.route("/login", methods=["GET", "POST"])
def login():

    if session.get("user_id"):
        return redirect("/")

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Checking for validity
        if not username or not password:
            flash("Missing username or password", "error")
            return redirect("/login")

        rows = db.execute("SELECT * FROM users WHERE username = ?", username)

        # Check if username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password):
            flash("Invalid username or password", "error")
            return redirect("/login")

        # Success
        session["user_id"] = rows[0]["id"]

        # Check old QR Code to delete
        cleanup(session["user_id"])

        return redirect("/")

    error_message = session.pop("error_message", None)

    return render_template("login.html")


# Log out
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# QR CODE (Credit to : https://www.youtube.com/watch?v=2yTlvPSIePs&ab)
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

        if not expiration:
            expiration_date = datetime.now() + timedelta(days=30)
        else:
            expiration_date = datetime.strptime(expiration, "%Y-%m-%d")

        if expiration_date > today + timedelta(days=30):
            flash("Expiration date is greater than 30 days", "error")
            return render_template("qrcode.html")

        if expiration_date <= today:
            flash("Expiration date cannot be today or before", "error")
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

        safe_name = secure_filename(name)
        user_id = session["user_id"]
        filename = f"{user_id}_{safe_name}.png"
        name_without_ext = filename.replace(".png", "")
        path = os.path.join("static", "qrcodes", filename)

        os.makedirs(os.path.dirname(path), exist_ok=True)

        img.save(path)

        db.execute("INSERT INTO qrcodes (user_id, value, expiration_date, link) VALUES (?, ?, ?, ?)", session["user_id"], name_without_ext, expiration_date, link)

        flash("QR Code successfully generated!", "success")

        return redirect(url_for("panel"))

    return render_template("qrcode.html")

@app.route("/download_qrcode/<int:qrcode_id>")
@login_required
def download_qrcode(qrcode_id):

    qrcode = db.execute("SELECT * FROM qrcodes WHERE id = ? AND user_id = ?", qrcode_id, session["user_id"])

    if not qrcode:
        flash("You don't have permission to download this QR Code.", "error")
        return redirect(url_for("panel"))

    filename = qrcode[0]["value"]
    file_path = os.path.join("static", "qrcodes", f"{filename}.png")

    if not os.path.exists(file_path):
        flash("File not found", "error")
        return redirect(url_for("panel"))

    return send_file(file_path, as_attachment=True)


@app.route("/delete_qrcode/<int:qrcode_id>", methods=["POST"])
@login_required
def delete_qrcode(qrcode_id):
    # Check if user is the owner
    qrcode = db.execute("SELECT * FROM qrcodes WHERE id = ? AND user_id = ?", qrcode_id, session["user_id"])

    if not qrcode:
        flash("QR Code not found or you do not have permission to delete it", "error")
        return redirect(url_for("panel"))

    # Get path
    filename = qrcode[0]["value"]
    file_path = os.path.join("static", "qrcodes", f"{filename}.png")

    # Dete from static folder
    if os.path.exists(file_path):
        os.remove(file_path)

    # Delete from database
    db.execute("DELETE FROM qrcodes WHERE id = ?", qrcode_id)

    flash("QR Code deleted successfully!", "success")
    return redirect(url_for("panel"))


@app.route("/pdf", methods=["GET", "POST"])
@login_required
def pdf_generator():

    if request.method == "POST":
        name = request.form.get("name")
        content = request.form.get("content")
        expiration = request.form.get("expiration")

        if not name or not content:
            flash("Require a name and some content", error)
            return render_template("pdf.html")

        today = datetime.today()

        if not expiration:
            expiration_date = datetime.now() + timedelta(days=30)
        else:
            expiration_date = datetime.strptime(expiration, "%Y-%m-%d")

        if expiration_date > today + timedelta(days=30):
            flash("Expiration date is greater than 30 days", "error")
            return render_template("pdf.html")

        if expiration_date <= today:
            flash("Expiration date cannot be today or before", "error")
            return render_template("pdf.html")

        # PDF Creation
        pdf = MyPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        pdf.write_html(f"{content}")

        # Saving
        user_id = session["user_id"]
        safe_name = secure_filename(name)
        filename = f"{user_id}_{safe_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
        path = os.path.join("private_pdfs", filename)

        os.makedirs(os.path.dirname(path), exist_ok=True)
        pdf.output(path)

        # DB Storage
        db.execute(
            "INSERT INTO pdfs (user_id, name, filename, expiration_date) VALUES (?, ?, ?, ?)",
            user_id,
            safe_name,
            filename,
            expiration_date
        )

        flash("PDF generated successfully!", "success")
        return redirect(url_for("panel"))

    return render_template("pdf.html")

@app.route("/download_pdf/<filename>", methods=["GET", "POST"])
@login_required
def download_pdf(filename):

    pdf = db.execute("SELECT * FROM pdfs WHERE filename = ? AND user_id = ?", filename, session["user_id"])

    if not pdf:
        flash("You don't have access to this PDF", "error")
        return redirect(url_for("panel"))

    path = os.path.join("private_pdfs", filename)
    if not os.path.exists(path):
        flash("File not found", "error")
        return redirect(url_for("panel"))

    return send_file(path, as_attachment=True)

@app.route("/delete_pdf/<filename>", methods=["POST"])
@login_required
def delete_pdf(filename):

    pdf = db.execute("SELECT * FROM pdfs WHERE filename = ? AND user_id = ?", filename, session["user_id"])

    if not pdf:
        flash("PDF not found or you do not have permission to delete it", "error")
        return redirect(url_for("panel"))

    # Get path
    filename = pdf[0]["filename"]
    file_path = os.path.join("private_pdfs", filename)

    # Delete file from folder
    if os.path.exists(file_path):
        os.remove(file_path)

    # Delete file from db
    db.execute("DELETE FROM pdfs WHERE filename = ?", filename)

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

    if not expiration:
        expiration_date = datetime.now() + timedelta(days=30)
    else:
        expiration_date = datetime.strptime(expiration, "%Y-%m-%d")

    if expiration_date > today + timedelta(days=30):
        flash("Expiration date is greater than 30 days", "error")
        return redirect(url_for("panel"))

    if expiration_date <= today:
        flash("Expiration date cannot be today or before", "error")
        return redirect(url_for("panel"))

    pdf = db.execute("SELECT * FROM pdfs WHERE id = ? AND user_id = ?", pdf_id, session["user_id"])
    if not pdf:
        flash("PDF introuvable", "error")
        return redirect(url_for("panel"))

    token = secrets.token_urlsafe(12)
    link = url_for("shared_pdf", filename=pdf[0]["filename"], _external=True)

    if password_required:
        password = token
    else:
        password = None

    img = qrcode.make(link)

    safe_name = secure_filename(name)
    user_id = session["user_id"]
    filename = f"{user_id}_{safe_name}.png"
    name_without_ext = filename.replace(".png", "")
    path = os.path.join("static", "qrcodes", filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)

    img.save(path)

    # DB Saving
    db.execute("""INSERT INTO qrcodes (user_id, value, expiration_date, link, pdf_id, token, password)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
                       user_id,
                       name_without_ext,
                       expiration_date,
                       link,
                       pdf_id,
                       token,
                       password)

    flash("QR Code successfully generated!", "success")
    return redirect(url_for("panel"))


@app.route("/panel")
@login_required
def panel():

    qrcodes = db.execute("SELECT * FROM qrcodes WHERE user_id = ?", session["user_id"])
    pdfs = db.execute("SELECT * FROM pdfs WHERE user_id = ?", session["user_id"])

    # Create a dict about informations of QR Codes for each PDF
    qr_info = {}
    for qrcode in qrcodes:
        qr_info[qrcode["pdf_id"]] = {
            "link": qrcode["link"],
            "password": qrcode["password"]
        }

    return render_template("panel.html", qrcodes=qrcodes, pdfs=pdfs, qr_info=qr_info)


@app.route("/shared/<filename>", methods=["GET", "POST"])
def shared_pdf(filename):
    # Find PDF
    pdfs = db.execute("SELECT * FROM pdfs WHERE filename = ?", filename)
    if not pdfs:
        return "PDF not found", 404
    pdf = pdfs[0]

    if "user_id" in session and pdf["user_id"] == session["user_id"]:
        file_path = os.path.join("private_pdfs", filename)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=False)

    # Get QR Code
    qrcodes = db.execute("SELECT * FROM qrcodes WHERE pdf_id = ?", pdf["id"])
    if not qrcodes:
        return "QR Code not found", 404
    qrcode = qrcodes[0]

    # If password needed
    if qrcode["password"]:
        if request.method == "POST":
            entered_password = request.form.get("password")
            if entered_password == qrcode["password"]:
                file_path = os.path.join("private_pdfs", filename)
                if os.path.exists(file_path):
                    return send_file(file_path, as_attachment=True)
                else:
                    return "File not found", 404
            else:
                flash("Incorrect password", "error")
                return render_template("password_prompt.html", filename=filename)

        return render_template("password_prompt.html", filename=filename)

    # If no password needed
    file_path = os.path.join("private_pdfs", filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        return "File not found", 404
