# 🛠️ ServiceHub - Home Services Platform

ServiceHub is a modern, full-featured web application built with Python and Django. It connects customers with trusted home service professionals and provides role-specific dashboards for customers, workers, and administrators.

---

## ✨ Key Features

The platform supports **three distinct user roles**, each with its own dedicated dashboard and functionalities.

---

### 👤 Customer Features

- **User Authentication**  
  Secure registration, login, logout, and password reset functionality.

- **Service Browse**  
  A stylish and intuitive interface to browse, search, and filter services.

- **Service Booking**  
  An easy multi-step form to book services with detailed requirements.

- **Appointment Tracking**  
  Dashboard to view pending, active, and completed appointments.

- **Feedback System**  
  Star-rating and comment system to review service providers.

- **Profile Management**  
  Users can view, update, and securely delete their profiles.

---

### 👷 Worker (Service Provider) Features

- **Specialized Registration**  
  Separate signup for service professionals with extra details.

- **Personalized Dashboard**  
  Stats such as completed jobs, current assignments, and average ratings.

- **Job Management**  
  Accept jobs, update job status, and mark them as completed.

- **Profile Management**  
  Update personal and service-related information.

- **Availability Toggle**  
  Easily toggle your availability status.

- **Feedback Review**  
  View feedback and ratings from clients.

- **Colleague Directory**  
  See and connect with other service providers on the platform.

---

### 👑 Admin Features

- **Comprehensive Dashboard**  
  KPIs, charts, and logs to monitor overall platform performance.

- **User Management**  
  View and manage all registered users and workers.

- **Worker Verification**  
  Approve/reject new service providers after verification.

- **Service Management**  
  Add, edit, and delete service categories (includes icons).

- **Location Management**  
  Create and manage country, state, and city information.

- **Job Assignment**  
  Manually assign jobs to available service providers.

- **Full Oversight**  
  Access all requests, feedback, and operational metrics.

---

## 🚀 Tech Stack

- **Backend**: Python, Django  
- **Database**: PostgreSQL  
- **Frontend**: HTML5, CSS3, JavaScript  
- **UI/UX**: Bootstrap 5, Font Awesome 6, jQuery (DataTables)  
- **Core Libraries**: Django Auth, Messages Framework  

---

## ⚙️ Getting Started

Follow the steps below to run the project locally for development/testing.

### ✅ Prerequisites

- Python 3.8+  
- pip  
- PostgreSQL  

---

## 🧰 Installation

### 1️⃣ Clone the Repository

```bash
git clone <your-repository-url>
cd <repository-folder>
```
### 2️⃣ Create and Activate Virtual Environment

```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3️⃣ Install Dependencies
-Create a requirements.txt file and add:
```php
Django
psycopg2-binary
Pillow

Then install them:

```bash
pip install -r requirements.txt
```
### 4️⃣ 🛠️ Configure PostgreSQL Database
-Open your_project/settings.py and update:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'your_db_name',
        'USER': 'your_db_user',
        'PASSWORD': 'your_db_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```
### 5️⃣ 📧 Configure Email (for Password Reset)

In the same settings.py file, add:
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'

💡 For Gmail, enable 2FA and use a 16-character App Password.
```

### 6️⃣ 🔃 Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 7️⃣ 👑 Create Superuser
```bash
python manage.py createsuperuser
```
### 8️⃣ ▶️ Run the Server
```bash
python manage.py runserver
```
- **Open your browser at: http://127.0.0.1:8000**

- **Admin Panel: http://127.0.0.1:8000/admin/**

### 📁 Recommended Folder Structure
```bash
ServiceHub/
├── manage.py
├── requirements.txt
├── your_project/
│   ├── settings.py
│   ├── urls.py
│   └── ...
├── apps/
│   ├── users/
│   ├── services/
│   ├── bookings/
│   └── ...
```

### 📬 Contact
- **Email: tanbirhasan569@gmail.com**
- **GitHub: github.com/Tanbir-Hasan-247**