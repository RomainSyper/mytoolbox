from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Database models
class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    hash = db.Column(db.String(200), nullable=False)

class QRCode(db.Model):
    __tablename__ = "qrcodes"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    value = db.Column(db.String(200), nullable=False)  
    filename = db.Column(db.String(200), nullable=False) 
    expiration_date = db.Column(db.DateTime, nullable=False)
    link = db.Column(db.String(500), nullable=False)
    pdf_id = db.Column(db.Integer, db.ForeignKey('pdfs.id'), nullable=True)
    token = db.Column(db.String(50), nullable=True)

class PDF(db.Model):
    __tablename__ = "pdfs"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    filename = db.Column(db.String(300), nullable=False)
    expiration_date = db.Column(db.DateTime, nullable=False)