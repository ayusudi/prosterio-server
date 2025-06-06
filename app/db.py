import os
import snowflake.connector
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    conn = snowflake.connector.connect(
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema=os.getenv("SNOWFLAKE_SCHEMA"),
        ocsp_fail_open=True,
        ocsp_response_cache_filename=None,  # Disable OCSP caching
        insecure_mode=True  # Skip certificate validation - use with caution
    )
    return conn
