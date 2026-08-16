# controllers/productos_controller.py
import os
import time
from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from database.conexion import obtener_conexion

productos_blueprint = Blueprint('productos', __name__, url_prefix='/productos')
CARPETA_IMAGENES = os.path.join('static', 'img')

CATEGORIA_DEFAULT = 'General'


def generar_codigo():
    """Genera un código interno único (ya no lo escribe el usuario)."""
    return f"PRD{int(time.time() * 1000)}"


def procesar_imagen(file_input, codigo_producto, imagen_actual=None):
    if file_input and file_input.filename != '':
        _, ext = os.path.splitext(file_input.filename)
        nombre_archivo = f"{codigo_producto}{ext.lower()}"
        os.makedirs(CARPETA_IMAGENES, exist_ok=True)
        ruta_completa = os.path.join(CARPETA_IMAGENES, nombre_archivo)
        file_input.save(ruta_completa)
        return nombre_archivo
    return imagen_actual


@productos_blueprint.route('/')
def listar_productos():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    conn = obtener_conexion()
    productos = []

    if conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, nombre, categoria, descripcion, precio, precio_compra, stock, imagen
            FROM productos
            WHERE estado = TRUE
            ORDER BY id ASC
        """)

        rows = cursor.fetchall()

        for r in rows:
            productos.append({
                'id': r[0],
                'nombre': r[1],
                'categoria': r[2],
                'descripcion': r[3],
                'precio': float(r[4]),
                'precio_compra': float(r[5]),
                'stock': r[6],
                'imagen': r[7]
            })

        conn.close()

    return render_template(
        'productos/productos.html',
        usuario=session.get('full_name'),
        rol=session.get('rol'),
        productos=productos
    )


# ---------- CREAR ----------
@productos_blueprint.route('/crear', methods=['POST'])
def crear_producto():
    try:
        nombre = (request.form.get('nombre') or '').strip()
        categoria = (request.form.get('categoria') or '').strip() or CATEGORIA_DEFAULT
        descripcion = (request.form.get('descripcion') or '').strip()

        precio_raw = request.form.get('precio')
        precio_compra_raw = request.form.get('precio_compra')
        stock_raw = request.form.get('stock')

        if not nombre:
            return jsonify(success=False, message="El nombre es obligatorio."), 400

        try:
            precio = float(precio_raw)
            precio_compra = float(precio_compra_raw)
            stock = int(stock_raw)
        except (TypeError, ValueError):
            return jsonify(success=False, message="Precio, precio de compra y stock deben ser numéricos."), 400

        codigo = generar_codigo()

        archivo_imagen = request.files.get('imagen_file')
        nombre_imagen = procesar_imagen(archivo_imagen, codigo)

        conn = obtener_conexion()

        if not conn:
            return jsonify(success=False, message="No se pudo conectar a la base de datos."), 500

        try:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO productos
                (nombre, categoria, descripcion, precio, precio_compra, stock, imagen, estado, fecha_creacion)
                VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE, NOW())
            """, (
                nombre,
                categoria,
                descripcion,
                precio,
                precio_compra,
                stock,
                nombre_imagen
            ))

            conn.commit()

        except Exception as e:
            conn.rollback()
            return jsonify(success=False, message=f"Error al guardar el producto: {e}"), 500

        finally:
            conn.close()

        return jsonify(success=True, message="Producto creado correctamente.")

    except Exception as e:
        return jsonify(success=False, message=f"Error inesperado: {e}"), 500


# ---------- EDITAR ----------
@productos_blueprint.route('/editar/<int:id_producto>', methods=['POST'])
def editar_producto(id_producto):
    try:
        nombre = (request.form.get('nombre') or '').strip()
        categoria = (request.form.get('categoria') or '').strip() or CATEGORIA_DEFAULT
        descripcion = (request.form.get('descripcion') or '').strip()

        precio_raw = request.form.get('precio')
        precio_compra_raw = request.form.get('precio_compra')
        stock_raw = request.form.get('stock')

        imagen_actual = request.form.get('imagen_actual')

        if not nombre:
            return jsonify(success=False, message="El nombre es obligatorio."), 400

        try:
            precio = float(precio_raw)
            precio_compra = float(precio_compra_raw)
            stock = int(stock_raw)
        except (TypeError, ValueError):
            return jsonify(success=False, message="Precio, precio de compra y stock deben ser numéricos."), 400

        conn = obtener_conexion()

        if not conn:
            return jsonify(success=False, message="No se pudo conectar a la base de datos."), 500

        try:
            cursor = conn.cursor()

            cursor.execute("SELECT id FROM productos WHERE id = %s", (id_producto,))
            fila = cursor.fetchone()

            codigo_actual = fila[0] if fila else generar_codigo()

            archivo_imagen = request.files.get('imagen_file')
            nombre_imagen = procesar_imagen(
                archivo_imagen,
                codigo_actual,
                imagen_actual
            )

            cursor.execute("""
                UPDATE productos
                SET nombre=%s,
                    categoria=%s,
                    descripcion=%s,
                    precio=%s,
                    precio_compra=%s,
                    stock=%s,
                    imagen=%s,
                    fecha_modificacion=NOW()
                WHERE id=%s
            """, (
                nombre,
                categoria,
                descripcion,
                precio,
                precio_compra,
                stock,
                nombre_imagen,
                id_producto
            ))

            conn.commit()

        except Exception as e:
            conn.rollback()
            return jsonify(success=False, message=f"Error al editar el producto: {e}"), 500

        finally:
            conn.close()

        return jsonify(success=True, message="Producto actualizado correctamente.")

    except Exception as e:
        return jsonify(success=False, message=f"Error inesperado: {e}"), 500


# ---------- ELIMINAR ----------
@productos_blueprint.route('/eliminar/<int:id_producto>', methods=['POST'])
def eliminar_producto(id_producto):
    try:
        conn = obtener_conexion()

        if not conn:
            return jsonify(success=False, message="No se pudo conectar a la base de datos."), 500

        try:
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE productos
                SET estado = FALSE,
                    fecha_modificacion = NOW()
                WHERE id = %s
            """, (id_producto,))

            conn.commit()

        except Exception as e:
            conn.rollback()
            return jsonify(success=False, message=f"Error al eliminar el producto: {e}"), 500

        finally:
            conn.close()

        return jsonify(success=True, message="Producto eliminado correctamente.")

    except Exception as e:
        return jsonify(success=False, message=f"Error inesperado: {e}"), 500