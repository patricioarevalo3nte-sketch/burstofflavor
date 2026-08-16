# controllers/auth_controller.py
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models.usuario_model import UsuarioModel

auth_blueprint = Blueprint('auth', __name__)

@auth_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    # Si ya tiene sesión activa, mandarlo al home o dashboard
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password').strip()

        usuario = UsuarioModel.buscar_por_username(username)

        if usuario and UsuarioModel.verificar_password(usuario.clave_hash, password):
            # Guardamos la sesión con los datos de tu BD
            session['user_id'] = usuario.id
            session['full_name'] = usuario.nombre
            session['username'] = usuario.usuario
            session['rol'] = usuario.rol_nombre
            
            flash(f'¡Bienvenido {usuario.nombre}! Una Pilsener o qué? 🍻', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Usuario incorrecto, clave errónea o cuenta desactivada. ❌', 'danger')
            return redirect(url_for('auth.login'))

    return render_template('login.html')

@auth_blueprint.route('/logout')
def logout():
    session.clear()
    flash('Sesión cerrada. ¡Buen turno! 👋', 'info')
    return redirect(url_for('auth.login'))