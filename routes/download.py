"""
Rutas para descarga de documentos y comprobantes
Sistema de Rendiciones - Primar
"""

from flask import Blueprint, send_file, abort, flash, redirect, url_for
from flask_login import login_required, current_user
from models import db, Rendicion, ItemRendicion
from utils.decorators import admin_required
import os
from pathlib import Path
from werkzeug.utils import secure_filename
from utils.decorators import role_required

download_bp = Blueprint('download', __name__, url_prefix='/download')

# Directorio base de uploads
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads', 'comprobantes')


@download_bp.route('/comprobante/<int:item_id>', methods=['GET'])
@login_required
def descargar_comprobante(item_id):
    """
    Descarga el comprobante de un item de rendición
    
    Args:
        item_id: ID del item de rendición
    
    Returns:
        Archivo del comprobante o error 404
    """
    # Buscar el item
    item = ItemRendicion.query.get_or_404(item_id)
    
    # Verificar permisos
    # Usuario: solo sus propias rendiciones
    # Aprobador/Admin: todas las rendiciones
    if current_user.rol == 'usuario':
        if item.rendicion.usuario_id != current_user.id:
            flash('No tienes permiso para descargar este archivo', 'danger')
            abort(403)
    
    # Verificar que el item tiene comprobante
    if not item.comprobante_path:
        flash('Este item no tiene comprobante adjunto', 'warning')
        return redirect(url_for('rendiciones.ver_rendicion', id=item.rendicion_id))
    
    # Construir ruta completa del archivo
    archivo_path = os.path.join(UPLOAD_FOLDER, item.comprobante_path)
    
    # Verificar que el archivo existe
    if not os.path.exists(archivo_path):
        flash('El archivo no se encuentra en el servidor', 'danger')
        return redirect(url_for('rendiciones.ver_rendicion', id=item.rendicion_id))
    
    # Obtener nombre original del archivo
    nombre_archivo = os.path.basename(item.comprobante_path)
    
    try:
        # Enviar archivo
        return send_file(
            archivo_path,
            as_attachment=True,
            download_name=nombre_archivo,
            mimetype=get_mimetype(archivo_path)
        )
    except Exception as e:
        flash(f'Error al descargar el archivo: {str(e)}', 'danger')
        return redirect(url_for('rendiciones.ver_rendicion', id=item.rendicion_id))


@download_bp.route('/rendicion/<int:rendicion_id>/todos', methods=['GET'])
@login_required
def descargar_todos_comprobantes(rendicion_id):
    """
    Descarga todos los comprobantes de una rendición en un archivo ZIP
    
    Args:
        rendicion_id: ID de la rendición
    
    Returns:
        Archivo ZIP con todos los comprobantes
    """
    import zipfile
    from io import BytesIO
    from datetime import datetime
    
    # Buscar la rendición
    rendicion = Rendicion.query.get_or_404(rendicion_id)
    
    # Verificar permisos
    if current_user.rol == 'usuario':
        if rendicion.usuario_id != current_user.id:
            flash('No tienes permiso para descargar estos archivos', 'danger')
            abort(403)
    
    # Verificar que la rendición tiene items con comprobantes
    items_con_comprobantes = [item for item in rendicion.items if item.comprobante_path]
    
    if not items_con_comprobantes:
        flash('Esta rendición no tiene comprobantes adjuntos', 'warning')
        return redirect(url_for('rendiciones.ver_rendicion', id=rendicion_id))
    
    # Crear archivo ZIP en memoria
    memoria = BytesIO()
    
    try:
        with zipfile.ZipFile(memoria, 'w', zipfile.ZIP_DEFLATED) as zf:
            for idx, item in enumerate(items_con_comprobantes, 1):
                archivo_path = os.path.join(UPLOAD_FOLDER, item.comprobante_path)
                
                if os.path.exists(archivo_path):
                    # Nombre del archivo en el ZIP
                    extension = os.path.splitext(item.comprobante_path)[1]
                    nombre_en_zip = f"{idx:02d}_{secure_filename(item.descripcion[:50])}{extension}"
                    
                    # Agregar archivo al ZIP
                    zf.write(archivo_path, nombre_en_zip)
        
        # Posicionar al inicio del buffer
        memoria.seek(0)
        
        # Nombre del archivo ZIP
        fecha = datetime.now().strftime('%Y%m%d')
        nombre_zip = f"Rendicion_{rendicion.numero_rendicion}_{fecha}.zip"
        
        return send_file(
            memoria,
            mimetype='application/zip',
            as_attachment=True,
            download_name=nombre_zip
        )
        
    except Exception as e:
        flash(f'Error al crear el archivo ZIP: {str(e)}', 'danger')
        return redirect(url_for('rendiciones.ver_rendicion', id=rendicion_id))

@download_bp.route('/reporte/<tipo>/<formato>', methods=['GET'])
@login_required
@role_required(['admin', 'aprobador']) 
def descargar_reporte(tipo, formato):


    """
    Descarga reportes generados (Excel, PDF, etc.)
    
    Args:
        tipo: Tipo de reporte (rendiciones, usuarios, etc.)
        formato: Formato del archivo (xlsx, pdf, csv)
    
    Returns:
        Archivo del reporte generado
    """
    from flask import request
    
    # Obtener parámetros de filtro de la query string
    fecha_desde = request.args.get('fecha_desde')
    fecha_hasta = request.args.get('fecha_hasta')
    estado = request.args.get('estado')
    usuario_id = request.args.get('usuario_id')
    
    # Validar formato
    formatos_validos = ['xlsx', 'pdf', 'csv']
    if formato not in formatos_validos:
        flash('Formato de archivo no válido', 'danger')
        return redirect(url_for('reportes.index'))
    
    # Validar tipo de reporte
    tipos_validos = ['rendiciones', 'usuarios', 'aprobaciones', 'gastos']
    if tipo not in tipos_validos:
        flash('Tipo de reporte no válido', 'danger')
        return redirect(url_for('reportes.index'))
    
    try:
        # Generar el reporte según el tipo
        if tipo == 'rendiciones':
            from utils.reportes import generar_reporte_rendiciones
            archivo_path, nombre_archivo = generar_reporte_rendiciones(
                formato=formato,
                fecha_desde=fecha_desde,
                fecha_hasta=fecha_hasta,
                estado=estado,
                usuario_id=usuario_id
            )
        
        elif tipo == 'usuarios':
            from utils.reportes import generar_reporte_usuarios
            archivo_path, nombre_archivo = generar_reporte_usuarios(formato=formato)
        
        elif tipo == 'aprobaciones':
            from utils.reportes import generar_reporte_aprobaciones
            archivo_path, nombre_archivo = generar_reporte_aprobaciones(
                formato=formato,
                fecha_desde=fecha_desde,
                fecha_hasta=fecha_hasta
            )
        
        elif tipo == 'gastos':
            from utils.reportes import generar_reporte_gastos
            archivo_path, nombre_archivo = generar_reporte_gastos(
                formato=formato,
                fecha_desde=fecha_desde,
                fecha_hasta=fecha_hasta,
                usuario_id=usuario_id
            )
        
        # Verificar que el archivo se generó
        if not os.path.exists(archivo_path):
            flash('Error al generar el reporte', 'danger')
            return redirect(url_for('reportes.index'))
        
        # Enviar archivo y eliminarlo después
        return send_file(
            archivo_path,
            as_attachment=True,
            download_name=nombre_archivo,
            mimetype=get_mimetype(archivo_path)
        )
        
    except Exception as e:
        flash(f'Error al generar el reporte: {str(e)}', 'danger')
        return redirect(url_for('reportes.index'))
    finally:
        # Limpiar archivo temporal si existe
        if 'archivo_path' in locals() and os.path.exists(archivo_path):
            try:
                os.remove(archivo_path)
            except:
                pass


def get_mimetype(filename):
    """
    Obtiene el mimetype basado en la extensión del archivo
    
    Args:
        filename: Nombre del archivo
    
    Returns:
        String con el mimetype
    """
    extensiones = {
        '.pdf': 'application/pdf',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        '.xls': 'application/vnd.ms-excel',
        '.csv': 'text/csv',
        '.zip': 'application/zip',
        '.doc': 'application/msword',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    }
    
    ext = os.path.splitext(filename)[1].lower()
    return extensiones.get(ext, 'application/octet-stream')


@download_bp.route('/plantilla/<tipo>', methods=['GET'])
@login_required
def descargar_plantilla(tipo):
    """
    Descarga plantillas para carga masiva
    
    Args:
        tipo: Tipo de plantilla (rendiciones, items, usuarios)
    
    Returns:
        Archivo de plantilla
    """
    plantillas = {
        'rendiciones': 'plantilla_rendiciones.xlsx',
        'items': 'plantilla_items.xlsx',
        'usuarios': 'plantilla_usuarios.xlsx'
    }
    
    if tipo not in plantillas:
        flash('Plantilla no encontrada', 'danger')
        return redirect(url_for('dashboard.index'))
    
    # Directorio de plantillas
    plantillas_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'plantillas')
    archivo_path = os.path.join(plantillas_dir, plantillas[tipo])
    
    if not os.path.exists(archivo_path):
        flash('El archivo de plantilla no existe', 'danger')
        return redirect(url_for('dashboard.index'))
    
    return send_file(
        archivo_path,
        as_attachment=True,
        download_name=plantillas[tipo],
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )


# Función de ayuda para logging
def log_descarga(usuario_id, tipo_archivo, archivo_nombre):
    """
    Registra las descargas en el log del sistema
    
    Args:
        usuario_id: ID del usuario que descarga
        tipo_archivo: Tipo de archivo descargado
        archivo_nombre: Nombre del archivo
    """
    from datetime import datetime
    import logging
    
    logger = logging.getLogger('descargas')
    logger.info(f"Usuario {usuario_id} descargó {tipo_archivo}: {archivo_nombre} - {datetime.now()}")