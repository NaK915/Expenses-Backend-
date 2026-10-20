# Expense Split Backend

This project is a FastAPI backend boilerplate for the Expense Split application.

## Features

- FastAPI application scaffold
- MongoDB persistence using Motor collections
- Local Hugging Face Transformers expense categorization
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
- `PATCH /users/me` — update preferred display currency
- `GET /users` — authenticated user directory
- `POST /groups` — create a group for the current user
- `POST /groups/{group_id}/members` — add a member by email
- `DELETE /groups/{group_id}/members/me` — leave a group
- `POST /groups/{group_id}/transactions` — create an expense or reimbursement
- `PATCH /transactions/{transaction_id}` — edit your own transaction
- `DELETE /transactions/{transaction_id}` — delete your own transaction
- `GET /groups/{group_id}/balances` — calculated balances
- `GET /currencies/rates?base=INR&quote=USD` — current exchange-rate estimate
- `GET /groups/{group_id}/settlements` — calculated settlement suggestions
- `GET /health` — database health check
- `GET /ready` — readiness check

## Notes

- MongoDB should be running at the URI configured in `.env`.
- Data is stored in the `users`, `groups`, and `transactions` collections.
- Expenses and reimbursements share the `transactions` model and collection.
- New accounts default to INR. Groups choose one currency at creation; older records without currency fields default to INR.
- Expenses support equal splits, exact per-member amounts, or weighted parts. Custom allocations are stored with each transaction and must sum to the expense total.
- Exchange rates are fetched by the API from ExchangeRate-API's open endpoint when requested; converted figures are estimates and group balances remain in the group's currency.
- When an expense is created without a category, the backend classifies its title plus optional description using a local Transformers zero-shot classifier. The description is also displayed with the expense. A category selected by the user is kept as-is.
- `HF_CATEGORY_MODEL` controls the classifier model and defaults to `facebook/bart-large-mnli`. Transformers downloads the model on first use and caches it locally; deployments should pre-cache model weights or allow the initial download.
- Embeddings use local `HuggingFaceEmbeddings` and `HF_EMBEDDINGS_MODEL`; no Hugging Face API token is needed for either default public model.
