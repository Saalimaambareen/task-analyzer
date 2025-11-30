# Task Analyzer 

This repository contains a Django backend and a simple frontend implementing the Smart Balanced priority algorithm described in the assignment.

## Quick start

1. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
2. Run migrations and start the server:
   ```bash
   cd backend
   python manage.py migrate
   python manage.py runserver
   ```
3. Open `frontend/index.html` in browser or serve it with a static server.

## API
- POST /api/tasks/analyze/?strategy=smart|simple|fastest|impact|deadline
  - body: JSON array of tasks or `{ "tasks": [...] }`
- POST /api/tasks/suggest/?strategy=smart
  - body: JSON array of tasks

## Notes
- Smart Balanced algorithm is in `backend/tasks/scoring.py`.
- Unit tests are in `backend/tasks/tests.py`..
