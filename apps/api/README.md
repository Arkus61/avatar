# API App

FastAPI skeleton for the avatar backend.

## Local Commands

```bash
python -m compileall -q app
python -m unittest discover -s tests -p "test_*.py" -v
python -m uvicorn app.main:app --reload --port 8000
```

## Environment

Copy `.env.example` to `.env` and adjust as needed:

- `DB_HOST`
- `DB_PORT`
- `DB_NAME`
- `DB_USER`
