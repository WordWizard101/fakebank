# Fake Bank App

A Django-based banking application for managing user accounts, transactions, and admin functions.

## Website URL
- Development: http://127.0.0.1:8000/
- Production: [Add production URL if applicable]

## Installation
1. Clone the repository: `git clone <your-repo-url>`
2. Install dependencies: `pip install -r requirements.txt`
3. Set up PostgreSQL: Configure `fakebank/settings.py` with your database credentials (e.g., NAME='fakebank_db', USER='root', PASSWORD='pass1pass1', HOST='localhost', PORT='5432').
4. Run migrations: `python3 manage.py migrate`
5. Start the server: `python3 manage.py runserver`

## Usage
- Log in as `root`/`pass1pass1` for admin access or register a new user.
- Access features like account management, transactions, and admin dashboard.
