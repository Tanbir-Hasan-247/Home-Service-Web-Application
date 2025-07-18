# 🛠️ ServiceHub - Home Services Platform

ServiceHub is a modern, full-featured web application built with Python and Django. It connects customers with trusted home service professionals and provides role-specific dashboards for customers, workers, and administrators.

![Python](https://img.shields.io/badge/Python-3.12+-blue?style=for-the-badge&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-5.2-darkgreen?style=for-the-badge&logo=django&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14.0-blue?style=for-the-badge&logo=postgresql&logoColor=white)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-purple?style=for-the-badge&logo=bootstrap&logoColor=white)

---

## 📜 Table of Contents

- [Key Features](#-key-features)
- [Screenshots](#-screenshots)
- [Tech Stack](#-tech-stack)
- [Getting Started](#️-getting-started)
- [Usage](#-usage)
- [Project Structure](#-project-structure)
- [License](#-license)

---

## ✨ Key Features

The platform supports **three distinct user roles**, each with its own dedicated dashboard and functionalities.

### 👤 Customer Features
- **User Authentication:** Secure registration, login, logout, and password reset functionality.
- **Service Browse:** A stylish and intuitive interface to browse, search, and filter services.
- **Service Booking:** An easy multi-step form to book services with detailed requirements.
- **Appointment Tracking:** Dashboard to view pending, active, and completed appointments.
- **Feedback System:** Star-rating and comment system to review service providers.
- **Profile Management:** Users can view, update, and securely delete their profiles.

### 👷 Worker (Service Provider) Features
- **Specialized Registration:** Dedicated sign-up process for professionals with extra details.
- **Personalized Dashboard:** Overview of jobs completed, active jobs, and average rating.
- **Job Management:** Accept new jobs, update job status, and mark them as completed.
- **Profile Management:** Edit personal and service-related information.
- **Availability Toggle:** Easily set yourself as Available or Unavailable.
- **Feedback Review:** View customer ratings and reviews.
- **Colleague Directory:** Visual directory of other workers on the platform.

### 👑 Admin Features
- **Comprehensive Dashboard:** KPIs, charts, and activity feeds for total platform overview.
- **User Management:** View and manage all registered users and workers.
- **Worker Verification:** Approve or reject service provider applications.
- **Service Management:** Full CRUD for service categories, including icons.
- **Location Management:** Add/edit countries, states, and cities.
- **Job Assignment:** Manually assign jobs to available service providers.
- **Full Oversight:** Access all requests, feedback, and operational metrics.

---

## 📸 Screenshots

*(Here you can add screenshots of your application)*

| Homepage | Admin Dashboard | Worker Profile |
| :---: | :---: | :---: |
| ![Homepage](<path/to/your/homepage_screenshot.png>) | ![Admin Dashboard](<path/to/your/admin_dashboard_screenshot.png>) | ![Worker Profile](<path/to/your/worker_profile_screenshot.png>) |

---

## 🚀 Tech Stack

- **Backend**: Python, Django
- **Database**: PostgreSQL
- **Frontend**: HTML5, CSS3, JavaScript
- **UI/UX**: Bootstrap 5, Font Awesome 6, jQuery (for DataTables)
- **Core Libraries**: Django Authentication, Django Messages Framework

---

## ⚙️ Getting Started

Follow the steps below to run the project locally.

### ✅ Prerequisites

- Python 3.8+
- pip
- PostgreSQL

### 🧰 Installation

1.  **Clone the Repository**
    ```bash
    git clone <your-repository-url>
    cd <repository-folder>
    ```

2.  **Create and Activate Virtual Environment**
    ```bash
    # Windows
    python -m venv venv
    .\venv\Scripts\activate

    # macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install Dependencies**
    Create a `requirements.txt` file with the following content:
    ```
    Django
    psycopg2-binary
    Pillow
    ```
    Then, install the packages:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables (Recommended for Security)**
    Create a file named `.env` in the root directory of your project. **Do not commit this file to Git.** Add your sensitive information here:
    ```
    SECRET_KEY=your-django-secret-key
    DEBUG=True
    
    DB_NAME=your_db_name
    DB_USER=your_db_user
    DB_PASSWORD=your_db_password

    EMAIL_USER=your-email@gmail.com
    EMAIL_PASS=your-16-character-app-password
    ```
    To use these variables, you will need to install a package like `python-decouple`:
    ```bash
    pip install python-decouple
    ```
    Then, in `settings.py`, import `config` from `decouple` and replace your hardcoded settings.
    
    ```python
    # settings.py
    from decouple import config

    SECRET_KEY = config('SECRET_KEY')
    DEBUG = config('DEBUG', default=False, cast=bool)
    
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME'),
            'USER': config('DB_USER'),
            'PASSWORD': config('DB_PASSWORD'),
            'HOST': 'localhost',
            'PORT': '5432',
        }
    }
    
    EMAIL_HOST_USER = config('EMAIL_USER')
    EMAIL_HOST_PASSWORD = config('EMAIL_PASS')
    ```

5.  **Set up the Database**
    In PostgreSQL, create a new database that matches the `DB_NAME` you set in your `.env` file.
    ```sql
    CREATE DATABASE your_db_name;
    ```
    Then, run the Django migrations:
    ```bash
    python manage.py makemigrations
    python manage.py migrate
    ```

6.  **Create a Superuser**
    ```bash
    python manage.py createsuperuser
    ```

7.  **Run the Server**
    ```bash
    python manage.py runserver
    ```
    The application will be available at **`http://127.0.0.1:8000/`**.

---

## 🖥️ Usage

-   **Admin**: Log in with your superuser account. You will be redirected to the admin dashboard to manage the platform.
-   **Worker**: Register through the "Become a Provider" flow. Your account will be inactive until an Admin verifies you.
-   **Customer**: Register as a regular user to browse and book services.

---

## 📁 Project Structure