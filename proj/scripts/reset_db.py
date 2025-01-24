import sqlite3
import os
from proj.utils.path_helpers import get_db_dir


def reset_db():
    DB_DIR = get_db_dir("scm")
    DB_SCHEMA_SQL = f"{DB_DIR}/db_schema.sql"
    DB_FILE = f"{DB_DIR}/scm.db"

    # Remove the database file if it exists
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
        print(f"Existing database at {DB_FILE} removed.")

    # Connect to SQLite database (creates the file if it doesn't exist)
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Read and execute the SQL schema and data
    with open(f"{DB_SCHEMA_SQL}", "r") as schema_file:
        schema_sql = schema_file.read()
        cursor.executescript(schema_sql)

    # Commit changes and close the connection
    conn.commit()
    conn.close()

    print("Database setup and seeding completed successfully.")


if __name__ == "__main__":
    reset_db()
