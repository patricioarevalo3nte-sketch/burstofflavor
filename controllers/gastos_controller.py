from flask import Blueprint, render_template, request, redirect, url_for, session, abort
from database.conexion import obtener_conexion

gastos_blueprint = Blueprint(
    "gastos",
    __name__,
    url_prefix="/gastos"
)


@gastos_blueprint.route("/")
def listar_gastos():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    gastos = []
    conn = obtener_conexion()

    if conn:
        cursor = conn.cursor()

        # JOIN con usuarios para obtener el nombre de quien registró el gasto
        cursor.execute("""
            SELECT
                g.id_gasto,
                g.nombre,
                g.descripcion,
                g.valor,
                g.fecha_gasto,
                g.created_at AT TIME ZONE 'America/Guayaquil' AS fecha_registro,
                g.user_id,
                COALESCE(u.nombre, 'Sistema') AS usuario_registro
            FROM gastos g
            LEFT JOIN usuarios u ON g.user_id = u.id
            WHERE g.estado = TRUE
            ORDER BY g.fecha_gasto DESC, g.id_gasto DESC
        """)

        rows = cursor.fetchall()

        for r in rows:
            gastos.append({
                "id_gasto": r[0],
                "nombre": r[1],
                "descripcion": r[2],
                "valor": float(r[3]),
                "fecha_gasto": r[4],
                "fecha_registro": r[5],
                "user_id": r[6],
                "usuario_registro": r[7]
            })

        cursor.close()
        conn.close()

    return render_template(
        "gastos.html",
        usuario=session.get("full_name"),
        usuario_actual_id=session.get("user_id"),
        rol=session.get("rol"),
        gastos=gastos
    )


@gastos_blueprint.route("/guardar", methods=["POST"])
def guardar_gasto():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    nombre = request.form["nombre"].strip()
    descripcion = request.form["descripcion"].strip()
    valor = float(request.form["valor"])
    fecha_gasto = request.form["fecha_gasto"]
    user_id = session.get("user_id")

    conn = obtener_conexion()

    if conn:
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO gastos
            (
                nombre,
                descripcion,
                valor,
                fecha_gasto,
                user_id
            )
            VALUES (%s, %s, %s, %s, %s)
        """, (
            nombre,
            descripcion,
            valor,
            fecha_gasto,
            user_id
        ))

        conn.commit()
        cursor.close()
        conn.close()

    return redirect(url_for("gastos.listar_gastos"))


@gastos_blueprint.route("/editar", methods=["POST"])
def editar_gasto():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    id_gasto = request.form["id_gasto"]
    nombre = request.form["nombre"].strip()
    descripcion = request.form["descripcion"].strip()
    valor = float(request.form["valor"])
    fecha_gasto = request.form["fecha_gasto"]

    user_id_actual = session.get("user_id")
    rol_actual = session.get("rol")

    conn = obtener_conexion()

    if conn:
        cursor = conn.cursor()

        # Validar pertenencia del gasto
        cursor.execute("SELECT user_id FROM gastos WHERE id_gasto = %s", (id_gasto,))
        gasto = cursor.fetchone()

        if not gasto:
            cursor.close()
            conn.close()
            return redirect(url_for("gastos.listar_gastos"))

        # Solo el Administrador o el creador del registro pueden modificarlo
        if rol_actual != 'Administrador' and gasto[0] != user_id_actual:
            cursor.close()
            conn.close()
            return "No tienes permisos para modificar este gasto", 403

        cursor.execute("""
            UPDATE gastos
            SET
                nombre=%s,
                descripcion=%s,
                valor=%s,
                fecha_gasto=%s,
                updated_at=NOW()
            WHERE id_gasto=%s
        """, (
            nombre,
            descripcion,
            valor,
            fecha_gasto,
            id_gasto
        ))

        conn.commit()
        cursor.close()
        conn.close()

    return redirect(url_for("gastos.listar_gastos"))


@gastos_blueprint.route("/eliminar/<int:id_gasto>")
def eliminar_gasto(id_gasto):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user_id_actual = session.get("user_id")
    rol_actual = session.get("rol")

    conn = obtener_conexion()

    if conn:
        cursor = conn.cursor()

        # Validar pertenencia del gasto
        cursor.execute("SELECT user_id FROM gastos WHERE id_gasto = %s", (id_gasto,))
        gasto = cursor.fetchone()

        if not gasto:
            cursor.close()
            conn.close()
            return redirect(url_for("gastos.listar_gastos"))

        # Solo el Administrador o el creador del registro pueden eliminarlo
        if rol_actual != 'Administrador' and gasto[0] != user_id_actual:
            cursor.close()
            conn.close()
            return "No tienes permisos para eliminar este gasto", 403

        cursor.execute("""
            UPDATE gastos
            SET
                estado=FALSE,
                updated_at=NOW()
            WHERE id_gasto=%s
        """, (id_gasto,))

        conn.commit()
        cursor.close()
        conn.close()

    return redirect(url_for("gastos.listar_gastos"))