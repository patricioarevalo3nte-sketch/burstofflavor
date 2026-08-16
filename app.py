from flask import Flask, render_template, redirect, url_for, session
from database.conexion import obtener_conexion
from datetime import date

from controllers.auth_controller import auth_blueprint
from controllers.usuarios_controller import usuarios_blueprint
from controllers.ventas_controller import ventas_blueprint
from controllers.productos_controller import productos_blueprint
from controllers.gastos_controller import gastos_blueprint
from datetime import date, timedelta

# Crear la aplicación
app = Flask(__name__)
app.secret_key = "llave_secreta_bar_pos_ecuador_2026"

# Registrar Blueprints
app.register_blueprint(auth_blueprint, url_prefix="/auth")
app.register_blueprint(usuarios_blueprint)
app.register_blueprint(ventas_blueprint)
app.register_blueprint(productos_blueprint)
app.register_blueprint(gastos_blueprint)


@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("auth.login"))



def obtener_resumen_financiero():
    """Calcula inversión (inventario + gastos del mes) y ventas del mes."""
    resumen = {"inversion": 0.0, "ventas": 0.0, "diferencia": 0.0}

    hoy = date.today()
    inicio_mes = hoy.replace(day=1)
    manana = hoy + timedelta(days=1)  # límite superior exclusivo, cubre TODO el día de hoy

    conn = obtener_conexion()
    if not conn:
        return resumen

    cursor = conn.cursor()

    cursor.execute("""
        SELECT COALESCE(SUM(precio_compra ), 0)
        FROM productos
        WHERE estado = TRUE
    """)
    valor_inventario = float(cursor.fetchone()[0])

    cursor.execute("""
        SELECT COALESCE(SUM(valor), 0)
        FROM gastos
        WHERE estado = TRUE
          AND fecha_gasto >= %s AND fecha_gasto < %s
    """, (inicio_mes, manana))
    total_gastos = float(cursor.fetchone()[0])

    cursor.execute("""
        SELECT COALESCE(SUM(total), 0)
        FROM ventas
        WHERE fecha >= %s AND fecha < %s
    """, (inicio_mes, manana))
    total_ventas = float(cursor.fetchone()[0])

    cursor.close()
    conn.close()

    inversion = valor_inventario + total_gastos
    resumen["inversion"] = round(inversion, 2)
    resumen["ventas"] = round(total_ventas, 2)
    resumen["diferencia"] = round(total_ventas - inversion, 2)

    return resumen
@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    productos = []

    conn = obtener_conexion()

    if conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                id,
                nombre,
                categoria,
                descripcion,
                precio,
                stock,
                imagen
            FROM productos
            WHERE estado = TRUE
            ORDER BY nombre
        """)

        rows = cursor.fetchall()

        for r in rows:
            productos.append({
                "id": r[0],
                "nombre": r[1],
                "categoria": r[2],
                "descripcion": r[3],
                "precio": float(r[4]),
                "stock": r[5],
                "imagen": r[6]
            })

        cursor.close()
        conn.close()

    resumen = obtener_resumen_financiero()

    return render_template(
        "dashboard.html",
        usuario=session.get("full_name"),
        rol=session.get("rol"),
        productos=productos,
        resumen=resumen
    )


if __name__ == "__main__":
    import os

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)