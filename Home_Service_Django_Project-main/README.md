ServiceHub - Home Services Platform 🛠️
ServiceHub is a modern, full-featured web application designed to connect customers with trusted home service professionals. Built with Python and Django, this platform provides a seamless experience for users to book services, for workers to manage jobs, and for administrators to oversee the entire operation.

✨ Key Features
The platform is divided into three distinct user roles, each with its own dedicated dashboard and functionalities.

👤 Customer Features:
User Authentication: Secure registration, login, logout, and password reset functionality.

Service Browse: A "fancy" and attractive interface to browse, search, and filter available services.

Service Booking: An intuitive multi-step form to book services with detailed information.

Appointment Tracking: A dedicated dashboard to view the status of pending, active, and completed appointments.

Feedback System: An interactive star-rating system for leaving reviews for service providers.

Profile Management: Users can view, edit, and securely delete their own profiles.

👷 Worker (Service Provider) Features:
Specialized Registration: A dedicated registration form for service providers.

Personalized Dashboard: A "fancy" dashboard showing worker-specific stats like jobs completed, active jobs, and average rating.

Job Management: View available jobs, accept new jobs, and mark active jobs as complete.

Profile Management: View and edit personal and professional details.

Availability Toggle: Easily set availability status (Available/Unavailable).

Feedback Review: View all feedback and ratings received from customers.

Colleague Directory: Browse a visual directory of other professionals on the platform.

👑 Admin Features:
Comprehensive Dashboard: A command center with KPI cards, charts, and recent activity feeds for a complete overview of the platform.

User Management: View and manage all registered customers and service providers.

Worker Verification: A system to approve and verify new service providers.

Service Management: Full CRUD (Create, Read, Update, Delete) functionality for service categories, including icon management.

Location Management: Easily add and manage countries, states, and cities.

Job Assignment: Manually assign pending service requests to the appropriate workers.

Full Oversight: View all requests, assigned jobs, and customer feedback across the entire platform.

🚀 Tech Stack
Backend: Python, Django

Database: PostgreSQL

Frontend: HTML5, CSS3, JavaScript

UI/UX: Bootstrap 5, Font Awesome 6, jQuery (for DataTables)

Core Django Libraries: Django Authentication, Django Messages Framework

⚙️ Getting Started
Follow these instructions to get the project up and running on your local machine for development and testing.

Prerequisites
Python (3.8 or newer)

Pip (Python package installer)

PostgreSQL (or another database of your choice)

Installation
Clone the repository:

Bash

git clone <your-repository-url>
cd <repository-folder>
Create and activate a virtual environment:

Bash

# For Windows
python -m venv venv
.\venv\Scripts\activate

# For macOS/Linux
python3 -m venv venv
source venv/bin/activate
Install the required packages:
Create a file named requirements.txt in your root project directory and add the following:

Django
psycopg2-binary 
Pillow
Then, run the installation command:

Bash

pip install -r requirements.txt
Configure your Database in settings.py:
Open your_project/settings.py and update the DATABASES section to connect to your PostgreSQL database.

Python

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
Configure Email Settings in settings.py:
For the password reset feature to work, configure your SMTP email settings. For Gmail, you will need to generate an App Password.

Python

# settings.py
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-16-character-app-password'
Run Database Migrations:

Bash

python manage.py makemigrations
python manage.py migrate
Create a Superuser (Admin):
This will be your first admin account to manage the site.

Bash

python manage.py createsuperuser
Follow the prompts to create your admin account.

Run the Development Server:

Bash

python manage.py runserver
The project will be available at http://127.0.0.1:8000/. You can log in to the admin panel at http://127.0.0.1:8000/admin/.