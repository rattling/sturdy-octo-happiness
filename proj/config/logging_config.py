import logging
import os
from logging.handlers import RotatingFileHandler


# Function to set up logging
def setup_logging(log_dir="../../logs", log_file="workflow.log"):
    # Ensure the logs directory exists
    os.makedirs(log_dir, exist_ok=True)

    log_path = os.path.join(log_dir, log_file)

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(
                log_path, mode="w"
            ),  # Overwrite log file on each run
            logging.StreamHandler(),  # Keep console logging
        ],
    )
