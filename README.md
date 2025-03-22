# Campus Picks

A Django-based project for campus sport bets that integrates both MongoDB and SQL-based models.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Running Management Commands](#running-management-commands)
- [Project Structure](#project-structure)
- [License](#license)

---

## Prerequisites

1. **Python 3.7+** (Recommended 3.8 or higher)
2. **Pip** (Python package manager)
3. **Virtualenv** (optional but recommended)
4. **MongoDB** installed and **listening on port 27017** (default port)  
   - If you do not already have MongoDB installed, refer to the [official MongoDB documentation](https://docs.mongodb.com/manual/installation/) for your platform.
   - Make sure the MongoDB service is running before starting the Django application.
5. **SQL Database** (e.g., SQLite, PostgreSQL, or MySQL) configured for Django’s SQL models.

---

## Installation

1. **Clone the Repository**  
   ```bash
   git clone https://github.com/your-username/your-repo.git
   cd your-repo
   ```

2. **(Optional) Create and Activate a Virtual Environment**  
   ```bash
   python -m venv venv
   source venv/bin/activate  # On macOS/Linux
   venv\Scripts\activate     # On Windows
   ```

3. **Install Dependencies**  
   ```bash
   pip install -r requirements.txt
   ```

---

## Configuration

1. **Django Settings**  
   - By default, the Django settings are located in `campus_picks/campus_picks/settings.py`.
   - Adjust the `DATABASES` or other settings if needed.
     - **MongoDB Connection:** Ensure that your MongoDB instance is running on port `27017`. Update any connection strings in your settings if your setup differs.
     - **SQL Database Connection:** This project also contains SQL-based models. If you plan to use a SQL database (e.g., SQLite, PostgreSQL, or MySQL), update the `DATABASES` configuration accordingly.

---

## Running the Application

1. **Apply Migrations**  
   This project includes SQL models alongside MongoDB integrations. It is necessary to run Django migrations to set up the SQL database schema as well as apply any changes for Django’s internal apps:
   ```bash
   python manage.py migrate
   ```

2. **Run the Server**  
   ```bash
   python manage.py runserver
   ```
   The development server will start at [http://127.0.0.1:8000/](http://127.0.0.1:8000/) by default.

---

## Running Management Commands

This project includes custom management commands that handle analytics scheduling and sports data integration. You must run these commands to set up recurring tasks or schedule necessary jobs.

1. **Schedule Analytics**  
   Located in the `analytics_engine/management/commands/schedule_analytics.py` file:
   ```bash
   python manage.py schedule_analytics
   ```
   This command schedules analytics-related jobs.

2. **Run Sports Data Scheduler**  
   Located in the `sports_data_integration/management/commands/run_scheduler.py` file:
   ```bash
   python manage.py run_scheduler
   ```
   This command handles the sports data integration tasks, setting up schedules to fetch or process sports data.

Make sure you run these commands (and keep them running or schedule them as needed) so that analytics and sports data synchronization occur correctly in your environment.

---

## Project Structure

A simplified view of the repository structure (omitting some folders such as `__pycache__`, `migrations`, and static/media directories for brevity):

```
.
├── campus_picks
│   ├── acid_db
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── tests.py
│   │   └── views.py
│   ├── analytics_engine
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── management
│   │   │   └── commands
│   │   │       └── schedule_analytics.py
│   │   ├── models.py
│   │   ├── tests.py
│   │   └── views.py
│   ├── api_gateway
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── tests.py
│   │   ├── urls.py
│   │   └── views.py
│   ├── bet_management
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── tests.py
│   │   └── views.py
│   ├── campus_picks
│   │   ├── asgi.py
│   │   ├── celery.py
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── location_processor
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── tests.py
│   │   └── views.py
│   ├── manage.py
│   ├── realtime
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── tests.py
│   │   └── views.py
│   ├── sports_data_integration
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── management
│   │   │   └── commands
│   │   │       └── run_scheduler.py
│   │   ├── models.py
│   │   ├── task.py
│   │   ├── tests.py
│   │   ├── urls.py
│   │   └── views.py
│   └── user_management
│       ├── admin.py
│       ├── apps.py
│       ├── models.py
│       ├── tests.py
│       ├── urls.py
│       └── views.py
├── prueba.py
├── README.md
└── requirements.txt
```

---

## License

(Include your license information here, e.g. MIT License, Apache License, etc.)

---

**Happy coding!**  
If you run into any issues, please open an issue or reach out with questions.