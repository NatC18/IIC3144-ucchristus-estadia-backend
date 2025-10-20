import logging
import threading

from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView

from api.models.archivo_carga import ArchivoCarga
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


class ArchivoUploadView(APIView):
    """
    Vista completa para subir y procesar archivos Excel desde el frontend
    POST: Solo accesible para usuarios admin
    GET: Accesible para usuarios autenticados (ven sus propios archivos)
    """
    
    def get_permissions(self):
        """
        Permisos diferenciados por método HTTP
        """
        if self.request.method == 'POST':
            return [IsAdminUser()]
        else:
            return [permissions.IsAuthenticated()]

    def post(self, request):
        """
        Subir archivo Excel y comenzar procesamiento automático
        """
        try:
            # Validar permisos de admin
            if not (request.user.is_admin or request.user.is_staff):
                return Response({
                    'error': 'Acceso denegado', 
                    'message': 'Solo los administradores pueden cargar archivos Excel'
                }, status=status.HTTP_403_FORBIDDEN)

            # Obtener archivo y tipo del request
            file = request.FILES.get("file") or request.FILES.get("archivo")
            tipo = request.data.get("tipo")

            # Validaciones básicas
            if not file:
                return Response({
                    "error": "Archivo requerido",
                    "message": "Debes seleccionar un archivo Excel para subir"
                }, status=status.HTTP_400_BAD_REQUEST)

            if not tipo:
                return Response({
                    "error": "Tipo requerido",
                    "message": "Debes especificar el tipo de datos (USERS, PACIENTES, CAMAS, etc.)"
                }, status=status.HTTP_400_BAD_REQUEST)

            # Validar formato de archivo
            if not file.name.lower().endswith(('.xlsx', '.xls')):
                return Response({
                    'error': 'Formato de archivo inválido',
                    'message': 'Solo se permiten archivos Excel (.xlsx, .xls)'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Validar tipo de datos
            tipos_validos = ['USERS', 'PACIENTES', 'CAMAS', 'EPISODIOS', 'GESTIONES', 'NWP']
            if tipo.upper() not in tipos_validos:
                return Response({
                    'error': 'Tipo inválido',
                    'message': f'El tipo debe ser uno de: {", ".join(tipos_validos)}'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Crear registro de archivo con campos actualizados
            archivo = ArchivoCarga.objects.create(
                nombre=file.name,
                archivo=file,
                tipo=tipo.upper(),
                usuario=request.user,
                estado='SUBIDO'
            )

            logger.info(f"Usuario {request.user.email} subió archivo {file.name} de tipo {tipo}")

            # Iniciar procesamiento en background
            thread = threading.Thread(
                target=procesar_archivo_async,
                args=(archivo.id, tipo.upper())
            )
            thread.daemon = True
            thread.start()

            # Respuesta exitosa para el frontend
            return Response({
                'success': True,
                'message': 'Archivo cargado exitosamente. El procesamiento ha comenzado.',
                'archivo_id': str(archivo.id),
                'estado': archivo.estado,
                'nombre_archivo': archivo.nombre,
                'tipo': archivo.tipo,
                'fecha_carga': archivo.fecha_carga,
                'usuario': request.user.email
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error en ArchivoUploadView: {str(e)}")
            return Response({
                'error': 'Error interno del servidor',
                'message': 'Ocurrió un error al procesar el archivo. Intente nuevamente.',
                'details': str(e) if request.user.is_staff else None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request):
        """
        Obtener lista de archivos subidos por el usuario actual
        Solo admin puede subir archivos, pero cualquier usuario autenticado puede ver los que existan
        """
        try:
            # Verificar que el usuario esté autenticado
            if not request.user.is_authenticated:
                return Response({
                    'error': 'No autenticado',
                    'message': 'Debe estar autenticado para ver los archivos'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Admin ve todos, usuarios regulares ven los suyos
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
                    'usuario': archivo.usuario.email if archivo.usuario else None,
                    'tiene_errores': len(archivo.errores or []) > 0
                })

            return Response({
                'success': True,
                'archivos': archivos_data,
                'total': len(archivos_data)
            })

        except Exception as e:
            logger.error(f"Error en GET ArchivoUploadView: {str(e)}")
            return Response({
                'error': 'Error interno del servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_archivo_status(request, archivo_id):
    """
    Obtener el estado detallado de procesamiento de un archivo específico
    Usuarios autenticados pueden ver sus propios archivos, admin ve todos
    """
    try:
        archivo = get_object_or_404(ArchivoCarga, id=archivo_id)
        
        # Verificar permisos (admin puede ver todos, otros solo los suyos)
        if not (request.user.is_admin or request.user.is_staff) and archivo.usuario != request.user:
            return Response({
                'error': 'Acceso denegado',
                'message': 'No tiene permisos para ver este archivo'
            }, status=status.HTTP_403_FORBIDDEN)

        # Calcular filas exitosas correctamente
        filas_exitosas = max(0, archivo.filas_procesadas - archivo.filas_errores)

        return Response({
            'success': True,
            'archivo': {
                'id': str(archivo.id),
                'nombre': archivo.nombre,
                'tipo': archivo.tipo,
                'estado': archivo.estado,
                'porcentaje_completado': archivo.porcentaje_completado,
                'filas_totales': archivo.filas_totales,
                'filas_procesadas': archivo.filas_procesadas,
                'filas_exitosas': filas_exitosas,
                'filas_errores': archivo.filas_errores,
                'errores': archivo.errores or [],
                'fecha_carga': archivo.fecha_carga,
                'fecha_procesamiento': archivo.fecha_procesamiento,
                'usuario': archivo.usuario.email if archivo.usuario else None,
            }
        })

    except Exception as e:
        logger.error(f"Error en get_archivo_status: {str(e)}")
        return Response({
            'error': 'Error interno del servidor',
            'message': 'No se pudo obtener el estado del archivo'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
