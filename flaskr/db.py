from mysql import connector
import os
from dotenv import load_dotenv

load_dotenv()


def get_db_connection():
    connection = connector.connect(
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        host=os.getenv('DB_HOST'),
        database=os.getenv('DB_NAME')
    )

    return connection
