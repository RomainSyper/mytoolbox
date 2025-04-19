# My Toolbox

### Video Demo: [CLICK HERE](https://youtu.be/U1vVFiTpEeE)

## Description

**MyToolbox** is a web application that allows users to generate **QR Codes** and **PDF files** in a secure environment.
This project has been created to facilitate the sharing of information between several people, with a simple and intuitive user experience.

## Features

### 0. User Registration
To enable My ToolBox users to access their history, it is necessary to create an account in order to access all the features.
The user must go to the registration page. Then he has to choose his username and his password. The username must be unique.
Once the user has registered, he's redirected to the login page. The user must again enter his username and password to access all the features of My Toolbox.

### 1. QR Code Generator
The QR Code Generator tool has been designed to provide an easy access to links (external or internal). The user must enter the link to which the QR Code will redirect, as well the name of the QR Code (this enables the user to identify it in his Panel)
Finally, the user chooses the QR Code's expiration date. The defualt expiration date is +30 days; the user can choose to reduce it but cannot go beyond this. This feature avoid the saturation of the hard disk and database. Once the QR Code has been generated, the user is redirect to his Panel.

### 2. PDF Generator
The PDF Generator tool has been designed to make PDF creation quick and easy. The aim is to make it possible to create a short PDF without having to use a word processor.
The user must specify the name of the document and its expiration date. The expiration date works in the same as the QR Code one. Finally, users can write their text in the insertion zone provided.

### 3. Panel
The panel is a dashboard giving access to the history of QR Codes and PDFs that have been created. It is divided into these two categories to make the interface user friendly.
In both cases, users can preview, download and delete. But the PDFs category brings an additional feature : generate a QR Code while creating an access link to the PDF file. (see **Sharing** section)

### 4. Expiration
As explained above, QR Codes and PDFs always have an expiry date. For this project, we had to find a way of checking whether the user's QR Codes and PDFs has expired, without having to deploy the web app and use a complex system.
It was therefore decided th check each time the user logged on whether one or more PDFs/QR Codes had expired. If so, the rows in the database and the files in the hard disk are delete.

### 5. Sharing

The sharing feature is used when an user decides to generate a QR Code on his Panel in order to share a PDF file he has created. The user must enter the name of the QR Code, the expiration date and whether he want a password to secure access to the document.
If a password has been chosen, the user wishing to access the document must enter a password (see **Guest access** section).
This password is generated automatically. The PDF creator always has access to the document without having to enter the password.

### 6. Guest access

When a user who is not logged in (here called *guest*) wishes to open a document locked by a password, he must enter the password in order to access it. The document is downloaded automatically. If no password is required, the document is downloaded without asking for a password.

## Technologies Used

### Frontend
- HTML
- CSS
	- Boostrap + Bootstrap Icons
	- Bootswatch - Cyborg theme
- Javascript
	- Bootstrap
	- Quill JS

### Backend
- Python

### Database
- SQLite

### Framework
- Flask
- Jinja

### Libraries

#### Standard Python Libraries
- os
- secrets
- datetime
- functools

#### Web Framework & Extensions
- Flask
- flask_session
- werkzeug.security
- werkzeug.utils

#### Database
- cs50.SQL

#### PDF & QR Code
- fpdf / HTMLMixin
- qrcode

## Security

Passwords are **hashed** and stored in an SQLite database.
File names are secured to avoid any risk of SQL injection.

## Storage

**/static/qrcodes** -> Storage of QR Codes

**/private_pdfs** -> Storage of PDFs
The aim is to secure PDFs and not allow just any user to access them. By creating the folder outside the "static" folder, we can restrict access authorizations. When a user wishes to access a PDF via this path, we chack that the user is the creator.

**toolbox.db (sqlite)**
-> Table *users*
-> Table *qrcodes*
-> Table *pdfs*
