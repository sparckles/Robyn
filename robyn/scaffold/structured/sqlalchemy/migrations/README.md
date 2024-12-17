
# Alembic Migrations

This directory contains database migrations managed by Alembic, a lightweight migration tool for SQLAlchemy applications.

## Configuration

Update the `sqlalchemy.url` in `alembic.ini` with your database connection string:

```
sqlalchemy.url = postgresql+psycopg://user:password@localhost:5432/yourdb
```

### Example Connection Strings:
- **PostgreSQL**: `postgresql+psycopg://user:password@localhost:5432/yourdb`
- **MySQL**: `mysql+pymysql://user:password@localhost:3306/yourdb`
- **SQLite**: `sqlite:///./test.db`

## Migrations Workflow

### Create a New Migration
Generate a migration script based on model changes:

```
alembic revision --autogenerate -m "describe your changes"
```

### Run Migrations
Apply all pending migrations:

```
alembic upgrade head
```

### Downgrade Migrations
Rollback the most recent migration:

```
alembic downgrade -1
```

Or downgrade to a specific revision:

```
alembic downgrade <revision_id>
```

### Common Commands

Other useful commands include:

- View the current migration status:
  
  ```
  alembic current
  ```

- View the migration history:
  
  ```
  alembic history
  ```
