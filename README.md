# Expense Split Backend

This project is a FastAPI backend boilerplate for the Expense Split application.

## Features

- FastAPI application scaffold
- MongoDB persistence using Motor collections
- LangChain + Hugging Face integration
- Health and readiness endpoints
- Environment-based configuration

## Setup

1. Create a Python virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Copy environment variables:
   ```bash
   cp .env.example .env
   ```

4. Update values in `.env` for your local setup.

5. Start the development server:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

MongoDB must be running at `MONGODB_URI` before starting the API. The application
creates indexes for users, groups, and transactions during startup and does not
fall back to in-memory storage.

## Endpoints

- `GET /` — app metadata
- `POST /auth/register` — create an account and receive a JWT
- `POST /auth/login` — authenticate and receive a JWT
- `GET /auth/me` — current authenticated profile
- `GET /users` — authenticated user directory
- `POST /groups` — create a group for the current user
- `POST /groups/{group_id}/members` — add a member by email
- `DELETE /groups/{group_id}/members/me` — leave a group
- `POST /groups/{group_id}/transactions` — create an expense or reimbursement
- `PATCH /transactions/{transaction_id}` — edit your own transaction
- `DELETE /transactions/{transaction_id}` — delete your own transaction
- `GET /groups/{group_id}/balances` — calculated balances
- `GET /groups/{group_id}/settlements` — calculated settlement suggestions
- `GET /health` — database health check
- `GET /ready` — readiness check

## Notes

- MongoDB should be running at the URI configured in `.env`.
- Data is stored in the `users`, `groups`, and `transactions` collections.
- Expenses and reimbursements share the `transactions` model and collection.
- Hugging Face model access requires a valid API token if the chosen model requires it.
- The included LLM setup is a starter configuration and can be expanded for your app-specific logic.
