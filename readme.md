
🏥 CareConnect – Rural Healthcare Management System






CareConnect is a comprehensive, role-based healthcare platform designed to bridge the gap between rural patients and medical professionals. It digitizes the complete appointment lifecycle — from discovering doctors to maintaining lifelong digital medical records.

✨ Live Demo

🌐 Try it here:
https://psatyateja.pythonanywhere.com/

🎯 Problem Statement

In many rural areas, healthcare access is inefficient and fragmented:

❌ Patients don’t know which doctors are available

❌ No online appointment booking

❌ Long manual queues at hospitals

❌ No centralized medical history

❌ Poor post-visit communication

✅ CareConnect solves these challenges by creating a fully digital healthcare ecosystem.
🏗️ System Architecture

The application follows Django’s MVT (Model-View-Template) architecture.

Tech Stack
Layer	Technology
Backend	Python, Django 4.2
Frontend	HTML, CSS, Bootstrap 5, JavaScript
Database	SQLite (Dev), PostgreSQL (Production-ready)
Authentication	Django Built-in Auth + Role-Based Access
Payments	Razorpay (Test Mode)
Deployment	PythonAnywhere
👥 User Roles & Features
👤 Patient

Register and manage profile

Search doctors by specialty, hospital, or name

Book, view, and cancel appointments

View digital prescriptions & medical history

Make secure online consultation payments

Track payment history

👨‍⚕️ Doctor

Personalized dashboard

Set weekly availability slots

Accept/reject appointment requests

Access patient history during consultation

Add diagnosis, prescriptions, and notes

🏥 Admin

Centralized admin dashboard

Approve and verify doctors

Manage hospitals and users

View platform analytics (appointments, trends, performance)

🗄️ Core Database Models

User – Extended with role (Patient / Doctor / Admin)

DoctorProfile – specialty, hospital, consultation_fee, availability

PatientProfile – age, gender, blood_group, emergency_contact

Appointment – patient, doctor, date, time, status

MedicalRecord – diagnosis, prescription, notes

Payment – amount, status, Razorpay transaction ID

🚀 Getting Started
Prerequisites

Python 3.10+

pip

Git

VS Code (recommended)

🔧 Installation
# Clone the repository
git clone https://github.com/satyatejaa/CCSH.git
cd CCSH

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Apply migrations
python manage.py migrate

# Create admin user
python manage.py createsuperuser

# Run development server
python manage.py runserver

Visit:

http://127.0.0.1:8000/
💳 Payment Integration (Razorpay)

CareConnect includes Razorpay integration (Test Mode).

Test Card Details

Card Number: 4242 4242 4242 4242

Expiry: Any future date

CVV: Any 3 digits

After successful payment:

Appointment status updates

Payment record is stored

Consultation becomes accessible

☁️ Deployment

Currently deployed on PythonAnywhere (Free Tier).

Deployment Steps

Push code to GitHub

Create PythonAnywhere web app

Configure virtual environment

Collect static files

Update ALLOWED_HOSTS

Set DEBUG = False

🛠️ Technologies Used

Django

Django REST Framework (Concept)

Bootstrap 5

SQLite / PostgreSQL

Razorpay API

Git & GitHub

PythonAnywhere

🔮 Future Enhancements

Email & SMS appointment reminders

Video consultation (WebRTC integration)

React Native mobile app

Advanced hospital analytics dashboard

Multi-language support

📧 Contact

Project Maintainer:
Satya Teja Peddireddy

📩 Email: satyatejapeddireddi@gmail.com

🐙 GitHub: https://github.com/satyatejaa

📄 License

This project is licensed under the MIT License.
See the LICENSE file for details.
