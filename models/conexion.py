import pyodbc
from config import CONNECTION_STRING


class Conexion:

    @staticmethod
    def conectar():
        try:
            conexion = pyodbc.connect(CONNECTION_STRING)
            return conexion

        except Exception as e:
            print("Error de conexión")
            print(e)
            return None