# MyToolbox
#### Video Demo: [CLICK HERE](https://youtu.be/U1vVFiTpEeE)
#### Description:

**MyToolbox** is a web application that allows users to generate **QR Codes** and **PDF files** in a secure, user-friendly environment.

### Features

**User Authentication**
Access to the tools is restricted to registered users only. Usernames and hashed passwords are stored in a **SQLite** table `users`.

**QR Code Generator**

**PDF Generator**

**Panel**

**Expiration System**

---

### QR Code Generator

- Users can generate QR codes by providing an URL, a name, and an expiration date (maximum of 30 days).
- QR code images are stored in the `static/qrcodes` directory.

- QR code data is saved in a **SQLite** table called `qrcodes`.

---

### PDF Generator

- Users can generate PDFs by specifying a name, content, and an expiration date (maximum of 30 days).
- PDFs are stored in a **private folder** named `private_pdfs`.
- When accessing a PDF, the app checks if the user requesting the file is the original creator.
- PDF data is saved in a **SQLite** table called `pdfs`.

---

### Expiration System

- On each user login, the app automatically checks if any of their QR codes or PDFs have expired.
- Expired entries are removed from both the database and the file system.

---

### Panel

- Users can preview, download, or delete their generated QR codes and PDFs.
- Users can also generate a QR code that links to a specific PDF.
- This link can be protected by a randomly generated password.

---

### Guest Access

- When a guest scans a QR code linked to a PDF and enters the correct password (if required), the file is automatically downloaded. (without giving access to private folders).
- Only the creator of a PDF can preview it within the app.

---

### File Storage

- Generated files, such as QR codes and PDFs, are stored in specific directories to ensure efficient organization and management. **QR codes** are saved in the `static/qrcodes` folder, while **PDFs** are stored in a private folder called `private_pdfs`. This folder is not directly accessible from the browser, ensuring that files remain protected. Access to the PDFs is restricted and verified, and only the creator of a file can preview or access it via a secured QR code.

---

### Protection

- Security is a key aspect of **MyToolbox**. User passwords are hashed using **Werkzeug**'s `generate_password_hash` function, ensuring that passwords are not stored in plain text in the SQLite database. Each user must authenticate before accessing the application’s features, with session management handled by **Flask-Session** to securely track user logins.
- **PDFs** are stored in a private folder, and access is limited: only the creator of the file can view it. If another user tries to access a PDF, the system verifies that they are the owner of the file before granting access.
- Additionally, the **QR codes** generated for PDFs can be password-protected by a randomly generated password, adding an extra layer of security for accessing sensitive resources.

---

### Design

- **MyToolbox** utilizes the **Cyborg** theme from **Bootstrap** to provide a modern and responsive design. The theme is optimized for both mobile and desktop use, ensuring a smooth and intuitive user experience. The dark-light color scheme is designed to enhance readability while remaining visually appealing.
- The minimalist design allows users to easily navigate between different features, such as generating QR codes and PDFs, and managing their files through the control panel. Interactions are straightforward, with options to preview, download, or delete generated files.

---

### Libraries

- **Flask**: Used for creating and managing the web application. It handles routing, user session management, and HTTP requests.
- **Flask-Session**: Manages server-side sessions to ensure a secure and seamless user experience.
- **SQLite**: A lightweight database used to store user information and metadata for QR codes and PDFs.
- **Werkzeug**: Used for password hashing with `generate_password_hash` and for managing uploaded files with `secure_filename`.
- **qrcode**: Generates QR code images from URLs specified by users.
- **secrets**: Used to generate secure, random passwords to protect QR code links.
- **fpdf**: Generates dynamic PDF files based on user-provided content.
- **datetime**: Handles expiration dates for QR codes and PDFs, enabling the app to check if a file has expired upon each login.
- **helpers.py**: Contains utility functions such as `login_required` (to enforce user login), `cleanup` (to delete expired QR codes and PDFs), `date_only` (to format expiration dates), and `MyPDF` (a custom class to handle PDF generation with `fpdf`).
- **os** and **io**: Used for managing files, directories, and data streams, assisting in the handling of QR codes and PDFs stored within the application.

---

MyToolbox combines simplicity and security to help users manage short-lived, shareable resources effectively.


----------

# My Toolbox

### Video Demo: [CLICK HERE](https://youtu.be/U1vVFiTpEeE)

## Description

**MyToolbox** is a web application that allows users to generate **QR Codes** and **PDF files** in a secure environment.
Ce projet a été pensé afin de faciliter le partage d'informations rapidement entre plusieurs personnes, le tout en permettant une expérience utilisateur simple et intuitive.

## Features

### 0. User Registration

### 1. QR Code Generator

### 2. PDF Generator

### 3. Panel

### 4. Expiration

### 5. Sharing

## Technologies Used

### Langages
- HTML, CSS, JS (Frontend)
- Python (backend)
- SQL (database)

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

## Storage


## How to use

All your files and folders are presented as a tree in the file explorer. You can switch from one to another by clicking a file in the tree.

