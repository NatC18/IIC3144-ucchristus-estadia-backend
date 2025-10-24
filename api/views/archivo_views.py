"""
Vistas para el manejo de carga de archivos Excel
"""

import logging
import threading

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from api.models import ArchivoCarga
from api.serializers.archivo_serializers import (
    ArchivoCargaSerializer,
    CargaArchivoSerializer,
    EstadoProcesamientoSerializer,
)
from api.services import (
    CamaExcelProcessor,
    EpisodioExcelProcessor,
    GestionExcelProcessor,
    PacienteEpisodioExcelProcessor,
    PacienteExcelProcessor,
    UserExcelProcessor,
)

logger = logging.getLogger(__name__)


def obtener_procesador(tipo: str):
    """Factory para obtener el procesador correcto según el tipo"""
    procesadores = {
        "USERS": UserExcelProcessor,
        "PACIENTES": PacienteExcelProcessor,
        "CAMAS": CamaExcelProcessor,
        "EPISODIOS": EpisodioExcelProcessor,
        "GESTIONES": GestionExcelProcessor,
        "NWP": PacienteEpisodioExcelProcessor,  # Para archivos de pacientes y episodios
    }
    return procesadores.get(tipo)


def procesar_archivo_async(archivo_carga_id: int, tipo: str):
    """Función para procesar el archivo en background"""
    archivo_carga = None
    try:
        archivo_carga = ArchivoCarga.objects.get(id=archivo_carga_id)
        logger.info(
            f"Iniciando procesamiento de archivo {archivo_carga_id} tipo {tipo}"
        )

        # Validar que el procesador existe
        procesador_class = obtener_procesador(tipo)
        if not procesador_class:
            archivo_carga.estado = "ERROR"
            archivo_carga.agregar_error(0, f"Tipo de procesador no válido: {tipo}")
            archivo_carga.save()
            logger.error(f"Procesador no encontrado para tipo: {tipo}")
            return

        # Cambiar estado a PROCESANDO antes de comenzar
        archivo_carga.estado = "PROCESANDO"
        archivo_carga.fecha_procesamiento = timezone.now()
        archivo_carga.save(update_fields=["estado", "fecha_procesamiento"])

        # Crear instancia del procesador y procesar
        procesador = procesador_class(archivo_carga)
        resultado = procesador.procesar_archivo()

        logger.info(
            f"Procesamiento completado para archivo {archivo_carga_id}: {resultado}"
        )

    except ArchivoCarga.DoesNotExist:
        logger.error(f"Archivo con ID {archivo_carga_id} no encontrado")
    except Exception as e:
        logger.error(
            f"Error crítico procesando archivo {archivo_carga_id}: {str(e)}",
            exc_info=True,
        )
        # Asegurar que el estado se actualice incluso en errores críticos
        if archivo_carga:
            try:
                archivo_carga.estado = "ERROR"
                archivo_carga.agregar_error(
                    0, f"Error crítico durante procesamiento: {str(e)}"
                )
                archivo_carga.save(update_fields=["estado"])
            except Exception as save_error:
                logger.error(
                    f"Error adicional al guardar estado de error: {save_error}"
                )


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def cargar_archivo(request):
    """
    Endpoint para cargar archivos Excel
    """
    serializer = CargaArchivoSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(
            {"error": "Datos inválidos", "detalles": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    archivo = serializer.validated_data["archivo"]
    tipo = serializer.validated_data["tipo"]

    # Crear registro de archivo
    archivo_carga = ArchivoCarga.objects.create(
        archivo=archivo, tipo=tipo, usuario=request.user, estado="SUBIDO"
    )

    # Procesar en background
    thread = threading.Thread(
        target=procesar_archivo_async, args=(archivo_carga.id, tipo)
    )
    thread.daemon = True
    thread.start()

    return Response(
        {
            "mensaje": "Archivo cargado exitosamente, procesamiento iniciado",
            "archivo_id": archivo_carga.id,
            "estado": archivo_carga.estado,
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def estado_procesamiento(request, archivo_id):
    """
    Consultar el estado de procesamiento de un archivo
    """
    archivo_carga = get_object_or_404(ArchivoCarga, id=archivo_id)

    # Verificar que el usuario puede ver este archivo
    if archivo_carga.usuario != request.user and not request.user.is_staff:
        return Response(
            {"error": "No tienes permisos para ver este archivo"},
            status=status.HTTP_403_FORBIDDEN,
        )

    serializer = EstadoProcesamientoSerializer(
        {
            "id": archivo_carga.id,
            "estado": archivo_carga.estado,
            "porcentaje_completado": archivo_carga.porcentaje_completado,
            "filas_totales": archivo_carga.filas_totales,
            "filas_procesadas": archivo_carga.filas_procesadas,
            "filas_exitosas": archivo_carga.filas_procesadas
            - archivo_carga.filas_errores,
            "filas_errores": archivo_carga.filas_errores,
            "errores": archivo_carga.errores,
            "fecha_carga": archivo_carga.fecha_carga,
            "fecha_procesamiento": archivo_carga.fecha_procesamiento,
        }
    )

    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def lista_archivos(request):
    """
    Listar archivos cargados por el usuario (o todos si es staff)
    """
    if request.user.is_staff:
        archivos = ArchivoCarga.objects.all()
    else:
        archivos = ArchivoCarga.objects.filter(usuario=request.user)

    # Filtros opcionales
    tipo = request.query_params.get("tipo")
    estado = request.query_params.get("estado")

    if tipo:
        archivos = archivos.filter(tipo=tipo)
    if estado:
        archivos = archivos.filter(estado=estado)

    # Ordenar por fecha más reciente
    archivos = archivos.order_by("-fecha_carga")

    serializer = ArchivoCargaSerializer(archivos, many=True)
    return Response(serializer.data)


@api_view(["DELETE"])
@permission_classes([permissions.IsAuthenticated])
def eliminar_archivo(request, archivo_id):
    """
    Eliminar un archivo cargado (solo el propietario o staff)
    """
    archivo_carga = get_object_or_404(ArchivoCarga, id=archivo_id)

    # Verificar permisos
    if archivo_carga.usuario != request.user and not request.user.is_staff:
        return Response(
            {"error": "No tienes permisos para eliminar este archivo"},
            status=status.HTTP_403_FORBIDDEN,
        )

    # No permitir eliminar archivos en procesamiento
    if archivo_carga.estado == "PROCESANDO":
        return Response(
            {"error": "No se puede eliminar un archivo en procesamiento"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    archivo_carga.delete()
    return Response({"mensaje": "Archivo eliminado exitosamente"})


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def plantilla_excel(request, tipo):
    """
    Descargar plantilla Excel con las columnas requeridas para cada tipo
    """
    from io import BytesIO

    import pandas as pd
    from django.http import HttpResponse

    procesador_class = obtener_procesador(tipo.upper())
    if not procesador_class:
        return Response(
            {"error": f"Tipo no válido: {tipo}"}, status=status.HTTP_400_BAD_REQUEST
        )

    # Crear instancia temporal para obtener columnas
    procesador_temp = procesador_class(None)
    columnas_requeridas = procesador_temp.get_columnas_requeridas()
    columnas_opcionales = procesador_temp.get_columnas_opcionales()

    # Crear DataFrame de ejemplo
    todas_columnas = columnas_requeridas + columnas_opcionales
    df_ejemplo = pd.DataFrame(columns=todas_columnas)

    # Agregar fila de ejemplo con comentarios
    ejemplo = {}
    for col in todas_columnas:
        if col in columnas_requeridas:
            ejemplo[col] = f"REQUERIDO - Ejemplo para {col}"
        else:
            ejemplo[col] = f"Opcional - Ejemplo para {col}"

    df_ejemplo.loc[0] = ejemplo

    # Generar archivo Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_ejemplo.to_excel(writer, sheet_name="Plantilla", index=False)

    output.seek(0)

    response = HttpResponse(
        output.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = (
        f'attachment; filename="plantilla_{tipo.lower()}.xlsx"'
    )

    return response
