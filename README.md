# StockMate - Inventory & Billing System

Flask inventory and billing project prepared for Render deployment.

## Render settings
- Runtime: Python 3
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn app:app`

The app uses SQLite for this demo version. On Render's free web service, the local filesystem is ephemeral, so database changes should not be treated as permanent. For permanent online inventory/sales data, migrate the database to PostgreSQL or use a persistent storage option.
