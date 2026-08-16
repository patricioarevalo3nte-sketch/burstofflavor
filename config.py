# config.py

# Credenciales de tu nueva base de datos en Supabase (Región: Canadá)
DB_USER = "postgres.ofscbbmyfmexyzrguyfh"
DB_PASS = "ProyectoFinal01"
DB_HOST = "aws-0-ca-central-1.pooler.supabase.com"
DB_PORT = "5432"
DB_NAME = "postgres"

# Tu nueva cadena de conexión optimizada para PostgreSQL (psycopg2)
CONNECTION_STRING = (
    f"dbname='{DB_NAME}' "
    f"user='{DB_USER}' "
    f"password='{DB_PASS}' "
    f"host='{DB_HOST}' "
    f"port='{DB_PORT}'"
)