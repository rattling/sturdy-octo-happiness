import sqlite3
import os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
PROMPTS_DIR = f"{PARENT_DIR}/prompts"
DB_PATH = f"{PARENT_DIR}/scm_db.sqlite"


import sqlite3


def extract_schema_as_markdown(db_path):
    """
    Extracts the schema of an SQLite database and formats it in Markdown.

    Args:
        db_path (str): Path to the SQLite database file.

    Returns:
        str: The database schema in Markdown format.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Query to get the schema for all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    schema_output = []
    for table in tables:
        table_name = table[0]
        schema_output.append(f"**Table: {table_name}**\n")

        # Get schema for each table
        cursor.execute(f"PRAGMA table_info('{table_name}');")
        columns = cursor.fetchall()

        for col in columns:
            col_name = col[1]
            col_type = col[2]
            is_primary = " PRIMARY KEY" if col[5] else ""
            is_not_null = " NOT NULL" if col[3] else ""
            schema_output.append(
                f"    - {col_name} {col_type}{is_primary}{is_not_null}"
            )

        schema_output.append("")  # Add a blank line for readability

    conn.close()
    return "\n".join(schema_output)


if __name__ == "__main__":
    schema = extract_schema_as_markdown(DB_PATH)
    print(schema)
    # save it to a schema.md file
    with open(f"{PROMPTS_DIR}/schema.md", "w") as f:
        f.write(schema)
