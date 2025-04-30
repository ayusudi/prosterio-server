import bcrypt
import snowflake.connector
# The same password for all accounts
password = "XXXXXXXX"

# Hash the password
hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

# Snowflake connection parameters (adjust these with your Snowflake credentials)
conn = snowflake.connector.connect(
    user="XXXXXX_snowflake_user",
    password="XXXXXX_snowflake_password",
    account="XXXXXX_snowflake_account",
    warehouse="XXXXXX_snowflake_warehouse",
    database="XXXXXX_snowflake_database",
    schema="XXXXXX_snowflake_schema",
)


# SQL query to insert data into the table
insert_sql = """
INSERT INTO Users (name, email, password, role)
VALUES 
    (%s, %s, %s, %s)
"""

# Data for insertion (same hashed password for all users)
values = (
    'Tester', 'email', hashed_password, 'SUPERUSER',
)

# Execute the insert query
cur = conn.cursor()
cur.execute(insert_sql, values)

# Commit and close connection
conn.commit()
cur.close()
conn.close()

print("Data inserted successfully!")
