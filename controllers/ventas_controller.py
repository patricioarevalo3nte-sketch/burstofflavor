# controllers/ventas_controller.py

from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for
from database.conexion import obtener_conexion

ventas_blueprint = Blueprint("ventas", __name__, url_prefix="/ventas")


@ventas_blueprint.route("/registrar", methods=["POST"])
@ventas_blueprint.route("/registrar", methods=["POST"])
def registrar_venta():

    if "user_id" not in session:
        return jsonify({
            "success": False,
            "message": "Sesión expirada o no válida"
        }), 401

    datos = request.get_json()

    cliente = datos.get("cliente", "CONSUMIDOR FINAL")
    metodo_pago = datos.get("metodo_pago", "Efectivo")
    carrito = datos.get("carrito", [])
    id_usuario = session["user_id"]

    if metodo_pago not in ("Efectivo", "Transferencia"):
        metodo_pago = "Efectivo"

    if not carrito:
        return jsonify({
            "success": False,
            "message": "El carrito está vacío"
        }), 400

    conn = obtener_conexion()

    if conn is None:
        return jsonify({
            "success": False,
            "message": "Error de conexión"
        }), 500

    cursor = conn.cursor()

    try:

        total_venta = sum(
            float(item["precio"]) * int(item["cantidad"])
            for item in carrito
        )

        subtotal_venta = total_venta

        # ===========================
        # CABECERA DE VENTA
        # ===========================

        query_venta = """
            INSERT INTO ventas
            (
                cliente,
                fecha,
                subtotal,
                descuento,
                total,
                id_usuario,
                metodo_pago
            )
            VALUES
            (
                %s,
                NOW(),
                %s,
                0,
                %s,
                %s,
                %s
            )
            RETURNING id;
        """

        cursor.execute(
            query_venta,
            (
                cliente,
                subtotal_venta,
                total_venta,
                id_usuario,
                metodo_pago
            )
        )

        id_venta = cursor.fetchone()[0]

        print(f"Venta creada: {id_venta}")

        # ===========================
        # DETALLE
        # ===========================

        for item in carrito:

            id_producto = item["id"]
            cantidad = int(item["cantidad"])

            cursor.execute(
                """
                SELECT
                    precio,
                    stock
                FROM productos
                WHERE id=%s
                """,
                (id_producto,)
            )

            producto = cursor.fetchone()

            if producto is None:
                raise Exception(
                    f"No existe el producto {id_producto}"
                )

            precio_unitario = float(producto[0])
            stock_actual = int(producto[1])

            if stock_actual < cantidad:
                raise Exception(
                    f"Stock insuficiente del producto {id_producto}"
                )

            total_linea = precio_unitario * cantidad

            cursor.execute(
                """
                INSERT INTO detalle_venta
                (
                    id_venta,
                    id_producto,
                    cantidad,
                    precio_unitario,
                    total
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    id_venta,
                    id_producto,
                    cantidad,
                    precio_unitario,
                    total_linea
                )
            )

            cursor.execute(
                """
                UPDATE productos
                SET stock = stock - %s
                WHERE id = %s
                """,
                (
                    cantidad,
                    id_producto
                )
            )

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Venta registrada correctamente."
        })

    except Exception as e:

        conn.rollback()

        print(e)

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:

        cursor.close()
        conn.close()

# ===========================================================
# LISTADO DE VENTAS
#   - Administrador: ve las ventas de TODOS los usuarios
#     y puede filtrar por vendedor específico.
#   - Cualquier otro rol: solo ve sus propias ventas.
#   - Ambos pueden filtrar por rango de fechas.
#   - Cada venta se puede expandir para ver el detalle
#     de productos vendidos (tabla detalle_venta).
# ===========================================================
@ventas_blueprint.route("/", methods=["GET"])
def listar_ventas():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    es_admin = session.get("rol") == "Administrador"
    id_usuario_sesion = session["user_id"]

    fecha_inicio = request.args.get("fecha_inicio", "").strip()
    fecha_fin = request.args.get("fecha_fin", "").strip()
    id_usuario_filtro = request.args.get("id_usuario", "").strip()

    ventas = []
    usuarios_lista = []
    total_general = 0.0

    conn = obtener_conexion()

    if conn:
        cursor = conn.cursor()

        # Lista de vendedores para el filtro (solo la necesita el admin)
        if es_admin:
            cursor.execute("SELECT id, nombre FROM usuarios ORDER BY nombre")
            usuarios_lista = [{"id": r[0], "nombre": r[1]} for r in cursor.fetchall()]

        condiciones = []
        parametros = []

        if not es_admin:
            condiciones.append("v.id_usuario = %s")
            parametros.append(id_usuario_sesion)
        elif id_usuario_filtro:
            condiciones.append("v.id_usuario = %s")
            parametros.append(id_usuario_filtro)

        if fecha_inicio:
            condiciones.append("v.fecha >= %s")
            parametros.append(fecha_inicio)

        if fecha_fin:
            condiciones.append("v.fecha < (%s::date + INTERVAL '1 day')")
            parametros.append(fecha_fin)

        where_sql = ("WHERE " + " AND ".join(condiciones)) if condiciones else ""

        query_ventas = f"""
            SELECT v.id, v.cliente, v.fecha, v.subtotal, v.descuento, v.total, u.nombre
            FROM ventas v
            JOIN usuarios u ON u.id = v.id_usuario
            {where_sql}
            ORDER BY v.fecha DESC
        """

        cursor.execute(query_ventas, parametros)
        filas_ventas = cursor.fetchall()

        ids_ventas = [f[0] for f in filas_ventas]

        detalle_por_venta = {}
        if ids_ventas:
            cursor.execute(
                """
                SELECT dv.id_venta, p.nombre, dv.cantidad, dv.precio_unitario, dv.total
                FROM detalle_venta dv
                JOIN productos p ON p.id = dv.id_producto
                WHERE dv.id_venta = ANY(%s)
                ORDER BY dv.id
                """,
                (ids_ventas,)
            )
            for fila in cursor.fetchall():
                detalle_por_venta.setdefault(fila[0], []).append({
                    "producto": fila[1],
                    "cantidad": fila[2],
                    "precio_unitario": float(fila[3]),
                    "total": float(fila[4])
                })

        for f in filas_ventas:
            total_linea = float(f[5])
            total_general += total_linea
            ventas.append({
                "id": f[0],
                "cliente": f[1],
                "fecha": f[2],
                "subtotal": float(f[3]),
                "descuento": float(f[4]),
                "total": total_linea,
                "usuario": f[6],
                "detalle": detalle_por_venta.get(f[0], [])
            })

        cursor.close()
        conn.close()

    return render_template(
        "ventas/ventas.html",
        usuario=session.get("full_name"),
        rol=session.get("rol"),
        ventas=ventas,
        usuarios_lista=usuarios_lista,
        es_admin=es_admin,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        id_usuario_filtro=id_usuario_filtro,
        total_general=total_general
    )