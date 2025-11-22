"""
Vista para manejar la importación de archivos Excel desde el frontend
"""

import json
import logging
import os
import shutil
import tempfile
import pandas as pd

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.management import call_command
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

logger = logging.getLogger(__name__)
from api.services.scoring_runner import persist_scores_to_episodios


@csrf_exempt
@require_http_methods(["POST"])
def upload_excel_files(request):
    """
    Endpoint para recibir los 3 archivos Excel y procesarlos
    """
    try:
        # Verificar que se hayan subido los 3 archivos
        required_files = ["excel1", "excel2", "excel3"]
        uploaded_files = {}

        for file_key in required_files:
            if file_key not in request.FILES:
                return JsonResponse(
                    {
                        "success": False,
                        "error": f"Falta el archivo {file_key}",
                        "message": f"Debe subir el archivo {file_key}.xlsx",
                    },
                    status=400,
                )

            uploaded_files[file_key] = request.FILES[file_key]

        # Validar que son archivos Excel
        for file_key, file_obj in uploaded_files.items():
            if not (file_obj.name.endswith(".xlsx") or file_obj.name.endswith(".xls")):
                return JsonResponse(
                    {
                        "success": False,
                        "error": f"Formato inválido para {file_key}",
                        "message": f"El archivo {file_key} debe ser un archivo Excel (.xlsx o .xls)",
                    },
                    status=400,
                )

        # Crear directorio temporal para los archivos
        temp_dir = tempfile.mkdtemp()
        temp_files = {}

        try:
            # Guardar archivos temporalmente
            for file_key, file_obj in uploaded_files.items():
                temp_file_path = os.path.join(temp_dir, f"{file_key}.xlsx")
                with open(temp_file_path, "wb") as temp_file:
                    for chunk in file_obj.chunks():
                        temp_file.write(chunk)
                temp_files[file_key] = temp_file_path

            # Ejecutar el comando de importación
            try:
                # Llamar al comando de Django directamente
                call_command("importar_excel_local", folder=temp_dir, verbosity=2)

                # Ejecutar scoring y persistir predicciones
                try:
                    updated = persist_scores_to_episodios(
                        df_grd=pd.read_excel(os.path.join(temp_dir, "excel1.xlsx"))
                    )
                    logger.info(f"Scoring ejecutado. Episodios actualizados: {updated}")
                except Exception as score_err:
                    logger.error(f"Error en scoring: {score_err}")

                return JsonResponse(
                    {
                        "success": True,
                        "message": "Archivos procesados exitosamente",
                        "data": {
                            "files_processed": list(uploaded_files.keys()),
                            "temp_dir": temp_dir,  # Para debugging, remover en producción
                        },
                    }
                )

            except Exception as e:
                logger.error(f"Error ejecutando comando de importación: {str(e)}")
                return JsonResponse(
                    {
                        "success": False,
                        "error": "Error en el procesamiento",
                        "message": f"Error al procesar los archivos: {str(e)}",
                    },
                    status=500,
                )

        finally:
            # Limpiar archivos temporales
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                logger.warning(
                    f"No se pudo limpiar directorio temporal {temp_dir}: {str(e)}"
                )

    except Exception as e:
        logger.error(f"Error general en upload_excel_files: {str(e)}")
        return JsonResponse(
            {
                "success": False,
                "error": "Error interno del servidor",
                "message": f"Error inesperado: {str(e)}",
            },
            status=500,
        )


@require_http_methods(["GET"])
def import_status(request):
    """
    Endpoint para obtener estadísticas de la última importación
    """
    try:
        from api.models import Episodio, Gestion, Paciente

        stats = {
            "pacientes": Paciente.objects.count(),
            "episodios": Episodio.objects.count(),
            "gestiones": Gestion.objects.count(),
        }

        return JsonResponse({"success": True, "data": stats})

    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {str(e)}")
        return JsonResponse(
            {
                "success": False,
                "error": "Error obteniendo estadísticas",
                "message": str(e),
            },
            status=500,
        )
