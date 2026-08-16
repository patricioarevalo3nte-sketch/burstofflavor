# models/usuario_model.py

from database.conexion import obtener_conexion
from werkzeug.security import check_password_hash


class UsuarioModel:
    def __init__(self, id, nombre, usuario, clave_hash, id_rol, rol_nombre=None, estado=1):
        self.id = id
        self.nombre = nombre
        self.usuario = usuario
        self.clave_hash = clave_hash
        self.id_rol = id_rol
        self.rol_nombre = rol_nombre
        self.estado = estado

    @staticmethod
    def buscar_por_username(username):
        """Busca un usuario activo por su nombre de usuario para el inicio de sesión"""
        conn = obtener_conexion()
        if not conn:
            return None

        cursor = conn.cursor()

        query = """
            SELECT
                u.id,
                u.nombre,
                u.usuario,
                u.clave_hash,
                u.id_rol,
                r.nombre AS rol_nombre,
                u.estado
            FROM usuarios u
            INNER JOIN roles r
                ON u.id_rol = r.id
            WHERE u.usuario = %s
              AND u.estado = TRUE
        """

        cursor.execute(query, (username,))
        row = cursor.fetchone()

        cursor.close()
        conn.close()

        if row:
            return UsuarioModel(
                row[0],
                row[1],
                row[2],
                row[3],
                row[4],
                rol_nombre=row[5],
                estado=row[6]
            )

        return None

    @staticmethod
    def verificar_password(clave_almacenada, clave_ingresada):
        """Soporta texto plano o hashes de Werkzeug"""
        if (
            clave_almacenada.startswith("pbkdf2:sha256:")
            or clave_almacenada.startswith("scrypt:")
        ):
            return check_password_hash(clave_almacenada, clave_ingresada)

        return clave_almacenada == clave_ingresada

    @staticmethod
    def obtener_todos():
        conn = obtener_conexion()
        if not conn:
            return []

        cursor = conn.cursor()

        query = """
            SELECT
                u.id,
                u.nombre,
                u.usuario,
                u.clave_hash,
                u.id_rol,
                r.nombre,
                u.estado
            FROM usuarios u
            INNER JOIN roles r
                ON u.id_rol = r.id
            WHERE u.estado = TRUE
            ORDER BY u.id
        """

        cursor.execute(query)
        rows = cursor.fetchall()

        cursor.close()
        conn.close()

        return [
            UsuarioModel(
                r[0],
                r[1],
                r[2],
                r[3],
                r[4],
                r[5],
                r[6]
            )
            for r in rows
        ]

    @staticmethod
    def obtener_por_id(id_usuario):
        conn = obtener_conexion()
        if not conn:
            return None

        cursor = conn.cursor()

        query = """
            SELECT
                id,
                nombre,
                usuario,
                clave_hash,
                id_rol,
                estado
            FROM usuarios
            WHERE id = %s
        """

        cursor.execute(query, (id_usuario,))
        row = cursor.fetchone()

        cursor.close()
        conn.close()

        if row:
            return UsuarioModel(
                row[0],
                row[1],
                row[2],
                row[3],
                row[4],
                estado=row[5]
            )

        return None

    @staticmethod
    def crear(nombre, usuario, clave, id_rol):
        conn = obtener_conexion()
        if not conn:
            return False

        cursor = conn.cursor()

        query = """
            INSERT INTO usuarios
                (nombre, usuario, clave_hash, id_rol)
            VALUES
                (%s, %s, %s, %s)
        """

        try:
            cursor.execute(query, (nombre, usuario, clave, id_rol))
            conn.commit()
            return True

        except Exception as e:
            conn.rollback()
            print(f"Error al crear usuario: {e}")
            return False

        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def actualizar(id_usuario, nombre, usuario, id_rol, clave=None):
        conn = obtener_conexion()
        if not conn:
            return False

        cursor = conn.cursor()

        try:
            if clave:
                query = """
                    UPDATE usuarios
                    SET
                        nombre = %s,
                        usuario = %s,
                        id_rol = %s,
                        clave_hash = %s
                    WHERE id = %s
                """

                cursor.execute(
                    query,
                    (nombre, usuario, id_rol, clave, id_usuario)
                )

            else:
                query = """
                    UPDATE usuarios
                    SET
                        nombre = %s,
                        usuario = %s,
                        id_rol = %s
                    WHERE id = %s
                """

                cursor.execute(
                    query,
                    (nombre, usuario, id_rol, id_usuario)
                )

            conn.commit()
            return True

        except Exception as e:
            conn.rollback()
            print(f"Error al actualizar usuario: {e}")
            return False

        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def eliminar_logico(id_usuario):
        conn = obtener_conexion()
        if not conn:
            return False

        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                UPDATE usuarios
                SET estado = FALSE
                WHERE id = %s
                """,
                (id_usuario,)
            )

            conn.commit()
            return True

        except Exception as e:
            conn.rollback()
            print(f"Error al eliminar usuario: {e}")
            return False

        finally:
            cursor.close()
            conn.close()