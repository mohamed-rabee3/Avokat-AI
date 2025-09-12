## to run backend

# Activate virtual environment
venv\Scripts\Activate.ps1

# Start the server
python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000

