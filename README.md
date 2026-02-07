# FastAPI To-Do API with JWT

## Setup (Windows)

1. Extract the project.
2. Open terminal inside the folder.
3. Create virtual environment:
   python -m venv venv

4. Activate:
   venv\Scripts\activate

5. Install dependencies:
   pip install -r requirements.txt

6. Create .env file:
   Copy .env.example and rename to .env

7. Ensure PostgreSQL is running and database exists:
   CREATE DATABASE todo_db;

8. Run server:
   uvicorn app.main:app --reload

9. Open:
   http://127.0.0.1:8000/docs
