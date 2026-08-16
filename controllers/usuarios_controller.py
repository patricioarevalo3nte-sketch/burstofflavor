# controllers/usuarios_controller.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.usuario_model import UsuarioModel

usuarios_blueprint = Blueprint('usuarios', __name__, url_prefix='/usuarios')

# Middleware rápido para proteger el CRUD: Solo entran admins logueados
def es_admin():
    return session.get('rol') == 'Administrador'

@usuarios_blueprint.route('/')
def listar():
    if not es_admin():
        flash('No tienes permisos para ver esta sección ❌', 'danger')
        return redirect(url_for('dashboard'))
    
    lista = UsuarioModel.obtener_todos()
    return render_template('usuarios/index.html', usuarios=lista)

@usuarios_blueprint.route('/crear', methods=['POST'])
def crear():
    if not es_admin(): return redirect(url_for('dashboard'))
    
    nombre = request.form.get('nombre')
    usuario = request.form.get('usuario')
    clave = request.form.get('clave')
    id_rol = request.form.get('id_rol') # 1 = Admin, 2 = Vendedor

    if UsuarioModel.crear(nombre, usuario, clave, id_rol):
        flash('¡Usuario registrado con éxito! 🍻', 'success')
    else:
        flash('El nombre de usuario ya existe o hubo un error. ❌', 'danger')
        
    return redirect(url_for('usuarios.listar'))

@usuarios_blueprint.route('/editar/<int:id>', methods=['POST'])
def editar(id):
    if not es_admin(): return redirect(url_for('dashboard'))
    
    nombre = request.form.get('nombre')
    usuario = request.form.get('usuario')
    id_rol = request.form.get('id_rol')
    clave = request.form.get('clave') # Opcional

    if UsuarioModel.actualizar(id, nombre, usuario, id_rol, clave if clave else None):
        flash('Usuario actualizado correctamente.', 'success')
    else:
        flash('Error al actualizar el usuario.', 'danger')
        
    return redirect(url_for('usuarios.listar'))

@usuarios_blueprint.route('/eliminar/<int:id>')
def eliminar(id):
    if not es_admin(): return redirect(url_for('dashboard'))
    
    if UsuarioModel.eliminar_logico(id):
        flash('Usuario removido del sistema.', 'info')
    else:
        flash('No se pudo eliminar al usuario.', 'danger')
        
    return redirect(url_for('usuarios.listar'))