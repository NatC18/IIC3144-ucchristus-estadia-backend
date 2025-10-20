"""
Vista específica para subida de archivos Excel desde el frontend
"""

import logging
import threading
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from api.models import ArchivoCarga
from api.serializers.archivo_serializers import CargaArchivoSerializer
from api.views.archivo_views import procesar_archivo_async

logger = logging.getLogger(__name__)


class IsAdminUser(permissions.BasePermission):
    """
    Permiso personalizado que solo permite acceso a usuarios admin
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            (request.user.is_admin or request.user.is_staff)
        )


@api_view(['POST'])
@permission_classes([IsAdminUser])
def upload_excel_frontend(request):
    """
    Endpoint específico para subida de archivos Excel desde el frontend
    Solo accesible para usuarios admin
    """
    try:
        # Validar que el usuario es admin
        if not (request.user.is_admin or request.user.is_staff):
            return Response({
                'error': 'Acceso denegado', 
                'message': 'Solo los administradores pueden cargar archivos Excel'
            }, status=status.HTTP_403_FORBIDDEN)

        # Validar datos del request
        serializer = CargaArchivoSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'error': 'Datos inválidos', 
                'detalles': serializer.errors,
                'message': 'Verifique que el archivo y tipo sean correctos'
            }, status=status.HTTP_400_BAD_REQUEST)

        archivo = serializer.validated_data['archivo']
        tipo = serializer.validated_data['tipo']

        # Validar tipo de archivo
        if not archivo.name.lower().endswith(('.xlsx', '.xls')):
            return Response({
                'error': 'Formato de archivo inválido',
                'message': 'Solo se permiten archivos Excel (.xlsx, .xls)'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Crear registro de archivo
        archivo_carga = ArchivoCarga.objects.create(
            archivo=archivo,
            tipo=tipo,
            usuario=request.user,
            estado='SUBIDO'
        )

        logger.info(f"Usuario {request.user.email} subió archivo {archivo.name} de tipo {tipo}")

        # Procesar en background
        thread = threading.Thread(
            target=procesar_archivo_async,
            args=(archivo_carga.id, tipo)
        )
        thread.daemon = True
        thread.start()

        # Respuesta exitosa para el frontend
        return Response({
            'success': True,
            'message': 'Archivo cargado exitosamente. El procesamiento ha comenzado.',
            'archivo_id': str(archivo_carga.id),
            'estado': archivo_carga.estado,
            'nombre_archivo': archivo.name,
            'tipo': tipo,
            'fecha_carga': archivo_carga.fecha_carga
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Error en upload_excel_frontend: {str(e)}")
        return Response({
            'error': 'Error interno del servidor',
            'message': 'Ocurrió un error al procesar el archivo. Intente nuevamente.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_upload_status(request, archivo_id):
    """
    Obtener el estado de procesamiento de un archivo subido desde el frontend
    """
    try:
        archivo_carga = ArchivoCarga.objects.get(id=archivo_id)
        
        # Verificar permisos (admin puede ver todos, otros solo los suyos)
        if not (request.user.is_admin or request.user.is_staff) and archivo_carga.usuario != request.user:
            return Response({
                'error': 'Acceso denegado',
                'message': 'No tiene permisos para ver este archivo'
            }, status=status.HTTP_403_FORBIDDEN)

        # Calcular filas exitosas correctamente
        filas_exitosas = max(0, archivo_carga.filas_procesadas - archivo_carga.filas_errores)

        return Response({
            'id': str(archivo_carga.id),
            'estado': archivo_carga.estado,
            'porcentaje_completado': archivo_carga.porcentaje_completado,
            'filas_totales': archivo_carga.filas_totales,
            'filas_procesadas': archivo_carga.filas_procesadas,
            'filas_exitosas': filas_exitosas,
            'filas_errores': archivo_carga.filas_errores,
            'errores': archivo_carga.errores,
            'fecha_carga': archivo_carga.fecha_carga,
            'fecha_procesamiento': archivo_carga.fecha_procesamiento,
            'nombre_archivo': archivo_carga.nombre,
            'tipo': archivo_carga.tipo,
            'usuario': archivo_carga.usuario.email,
        })

    except ArchivoCarga.DoesNotExist:
        return Response({
            'error': 'Archivo no encontrado',
            'message': 'El archivo solicitado no existe'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error en get_upload_status: {str(e)}")
        return Response({
            'error': 'Error interno del servidor'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def list_user_uploads(request):
    """
    Listar archivos subidos por el usuario actual (o todos si es admin)
    """
    try:
        if request.user.is_admin or request.user.is_staff:
            archivos = ArchivoCarga.objects.all().order_by('-fecha_carga')
        else:
            archivos = ArchivoCarga.objects.filter(usuario=request.user).order_by('-fecha_carga')

        archivos_data = []
        for archivo in archivos:
            filas_exitosas = max(0, archivo.filas_procesadas - archivo.filas_errores)
            
            archivos_data.append({
                'id': str(archivo.id),
                'nombre': archivo.nombre,
                'tipo': archivo.tipo,
                'estado': archivo.estado,
                'porcentaje_completado': archivo.porcentaje_completado,
                'filas_totales': archivo.filas_totales,
                'filas_procesadas': archivo.filas_procesadas,
                'filas_exitosas': filas_exitosas,
                'filas_errores': archivo.filas_errores,
                'fecha_carga': archivo.fecha_carga,
                'fecha_procesamiento': archivo.fecha_procesamiento,
                'usuario': archivo.usuario.email,
                'tiene_errores': len(archivo.errores) > 0
            })

        return Response({
            'archivos': archivos_data,
            'total': len(archivos_data)
        })

    except Exception as e:
        logger.error(f"Error en list_user_uploads: {str(e)}")
        return Response({
            'error': 'Error interno del servidor'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)