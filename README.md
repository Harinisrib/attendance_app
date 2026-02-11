# ML-Based Attendance Pattern Mining System

A premium web application for managing student attendance and leveraging Machine Learning to identify attendance patterns, streaks, and at-risk students.

## Features

- **Faculty Authentication**: Secure login and management.
- **Classroom Management**: Create and manage multiple classes and student rosters.
- **Attendance Tracking**: Mark attendance for morning and afternoon sessions.
- **ML Pattern Mining**: 
    - consistency scoring
    - Attendance heatmaps
    - Student success/risk prediction
- **Modern UI**: Dark-themed, responsive dashboard with data visualizations.

## Tech Stack

- **Backend**: Python / Flask
- **Database**: SQLite with SQLAlchemy ORM
- **ML Engine**: Scikit-learn, Pandas, Numpy
- **Frontend**: HTML5, Vanilla CSS, Jinja2 Templates

## Project Structure

- `server/`: Backend Flask application, ML engine, and database.
- `client/`: Placeholder for future frontend work.
- `docs/`: Project documentation and architecture details.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd attendance_app
    ```

2.  **Navigate to the server directory**:
    ```bash
    cd server
    ```

3.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    .\venv\Scripts\activate  # Windows
    # source venv/bin/activate  # Unix/macOS
    ```

4.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

5.  **Configure environment variables**:
    Create a `.env` file in the `server/` directory:
    ```env
    SECRET_KEY=your-secret-key
    DATABASE_URI=sqlite:///instance/attendance.db
    ```

6.  **Run the application**:
    ```bash
    python app.py
    ```

## Development Workflow

### Branching Strategy
- `main`: Production-ready code only.
- `develop`: Primary integration branch for features.
- `feature/*`: Individual feature development (e.g., `feature/ml-engine`).
- `bugfix/*`: Critical bug fixes.

---
Created as part of Phase 1: Tech Stack & Architecture.
