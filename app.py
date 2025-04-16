import os

from cs50 import SQL
from flask import Flask, render_template, request, redirect, session, url_for
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash

from helpers import login_required

app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["DEBUG"] = True
app.config['TEMPLATES_AUTO_RELOAD'] = True  # Active le rechargement automatique des templates
Session(app)


db = SQL("sqlite:///toolbox.db")
    
# Homepage
@app.route("/")
def index():
    
    return render_template("index.html")

# Register
@app.route("/register")
def register():

    session.clear()

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Checking for validity
        if not username or not password: 
            return "Missing username or password", 400
            
        if password != confirmation:
            return "Passwords doesnt match", 400
        
        hash = generate_password_hash(password)
        
        try:
            db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, hash)
        except:
            return "Username already taken", 400
        
        return redirect("/login")

    return render_template("register.html")


# Login
@app.route("/login")
def login():

    session.clear()

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Checking for validity
        if not username or not password: 
            return "Missing username or password", 400
        
        rows = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])

        # Check if username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], password
        ):
            return "Invalid username and/or password", 400
        
        # Remember
        session["user_id"] = rows[0]["id"]

        return redirect("/")
    
    return render_template("login.html")


# Log out
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


if __name__ == "__main__":
    app.run(debug=True)
