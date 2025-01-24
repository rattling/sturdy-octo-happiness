from proj.config.logging_config import setup_logging
import logging

setup_logging()


class CORE:
    def __init__(self, cursor):
        self.cursor = cursor
        self.message = Message(cursor)


class Message:
    def __init__(self, cursor):
        self.cursor = cursor

    def write_message(self, message: str):
        """
        Sends or logs a message.

        Args:
            message (str): The resolved message to send or log.

        Returns:
            dict: A dictionary containing the message that was sent or logged.
        """
        try:
            logging.info(f"Message Sent: {message}")
            return {"status": "success", "message": message}
        except Exception as e:
            logging.error(f"Error sending message: {e}")
            return {"status": "failure", "error": str(e)}


# def query_table(cursor, table, condition, output_fields):
#     sql = f"SELECT {output_fields} FROM {table}"
#     if condition:
#         sql += f" WHERE {condition}"
#     cursor.execute(sql)
#     rows = cursor.fetchall()
#     return [
#         dict(zip([col[0] for col in cursor.description], row)) for row in rows
#     ]


# def update_table(cursor, table, condition, updates):
#     set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
#     sql = f"UPDATE {table} SET {set_clause} WHERE {condition}"
#     cursor.execute(sql, list(updates.values()))
#     return cursor.rowcount
