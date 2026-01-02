# User database: local start-up

Instructions for running the Postgres instance that backs the user database.

## Prerequisites
- Docker and Docker Compose v2 (`docker compose version` should work).
- Python 3.12+ with the project dependencies installed if you want to run the table-creation script.

## Configure environment
Create an `.env` file next to `docker-compose.yml` (i.e. in `backend/src/user_db/`). Docker Compose will read it automatically.

Recommended values (keep `DATABASE_URL` aligned with the Postgres settings):
```
POSTGRES_DB=dish_booking_user
POSTGRES_USER=dish_user
POSTGRES_PASSWORD=change_me # replace with something strong
DATABASE_URL=postgresql+psycopg2://dish_user:change_me@localhost:5433/dish_booking_user
```

## Start the database
From the user_db directory:
```
cd backend/src/user_db
docker compose up -d
```
This starts a Postgres 16 container named `dish_booking_user_db` on port `5433` with its data persisted in the `db_data` volume.

To watch logs while it boots:
```
docker compose logs -f db
```

## Create the tables
Once the container is healthy, seed the schema using the SQLAlchemy models:
```
cd ../..  # back to backend/ from backend/src/user_db
PYTHONPATH=src DATABASE_URL="postgresql+psycopg2://dish_user:change_me@localhost:5433/dish_booking_user" python -m src.user_db.init_db
```
Adjust the `DATABASE_URL` to match your chosen credentials. The command will fail fast if `DATABASE_URL` is missing.

## Stopping and resetting
- Stop: `docker compose down`
- Stop and wipe data: `docker compose down -v` (removes the `db_data` volume)

## Troubleshooting
- Port already in use: stop whatever is bound to `5433`, or change the published port in `docker-compose.yml` and your `DATABASE_URL`.
- Authentication failures: ensure `POSTGRES_USER`, `POSTGRES_PASSWORD`, and the credentials in `DATABASE_URL` all match.
