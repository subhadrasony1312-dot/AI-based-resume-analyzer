import psycopg2

try:
    conn = psycopg2.connect(
        database="resume_analyzer",
        user="postgres",
        password="SUBHADRA@19092005",
        host="localhost",
        port="5432"
    )

    cursor = conn.cursor()
    print("Connected to PostgreSQL successfully!")

except Exception as e:
    print("Error:", e)