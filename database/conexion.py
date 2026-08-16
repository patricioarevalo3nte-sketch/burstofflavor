# database/conexion.py
import psycopg2
from config import CONNECTION_STRING

def obtener_conexion():
    try:
        conn = psycopg2.connect(CONNECTION_STRING)

        # Configurar la zona horaria para esta conexión
        with conn.cursor() as cursor:
            cursor.execute("SET TIME ZONE 'America/Guayaquil';")

        return conn

    except Exception as e:
        print(f"❌ Error crítico al conectar a Supabase (PostgreSQL): {e}")
        return None