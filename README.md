# Library Management System

A modern library management system built with FastAPI and Python, featuring separate interfaces for administrators and members.

## Features

### Admin Panel
- Dashboard with statistics
- Manage books (add, edit, delete)
- View and manage members
- Track book borrowings and returns
- Generate reports

### Member Panel
- Personal dashboard
- View borrowed books
- Manage favorite books
- Book search functionality
- Profile management

## Technology Stack

- **Backend**: FastAPI
- **Frontend**: Jinja2 Templates, HTML, TailwindCSS
- **Database**: MySQL
- **Authentication**: JWT Tokens
- **Icons**: Font Awesome

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- MySQL

## Installation

1. Clone the repository
```bash
git clone <repository-url>
cd library-management-system
```

2. Create a virtual environment
```bash
python -m venv venv

# On Windows
.\venv\Scripts\activate

# On macOS/Linux
source venv/bin/
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory
```env
DB_USER=root
DB_PASSWORD=12345678
DB_HOST=localhost
DB_NAME=library
DB_PORT=3306

SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
```

5. Initialize the database
```bash
python init_db.py
```

## Running the Application

1. Start the FastAPI server
```bash
uvicorn app.main:app --reload
```

2. Access the application:
- Main site: `http://localhost:8000`
- Admin panel: `http://localhost:8000/admin/dashboard`
- Member dashboard: `http://localhost:8000/member/dashboard`
- API documentation: `http://localhost:8000/docs`

## Project Structure

```
library-management/
├── app/
│   ├── main.py
│   ├── database/
│   │   ├── models.py
│   │   └── schemas.py
│   ├── routers/
│   │   ├── admin.py
│   │   ├── auth.py
│   │   └── member.py
│   ├── templates/
│   │   ├── admin/
│   │   └── member/
│   ├── static/
│   │   ├── css/
│   │   ├── js/
│   │   └── img/
│   └── utils/
│       └── auth.py
├── tests/
├── .env
├── requirements.txt
└── README.md
```

## Dependencies

Main dependencies include:
- fastapi
- uvicorn
- sqlalchemy
- pymysql
- pydantic
- python-jose[cryptography]
- passlib[bcrypt]
- python-multipart
- jinja2