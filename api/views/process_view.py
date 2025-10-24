# api/views/process_view.py
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from api.loaders import pacientes_loader
from api.models.archivo_carga import ArchivoCarga


class ProcesarArchivoView(APIView):
    """
    Procesa un archivo Excel previamente subido, según su tipo.
    """

    def post(self, request, archivo_id):
        try:
            archivo = ArchivoCarga.objects.get(id=archivo_id)
        except ArchivoCarga.DoesNotExist:
            return Response(
                {"error": "Archivo no encontrado."}, status=status.HTTP_404_NOT_FOUND
            )

        if archivo.procesado:
            return Response(
                {"error": "El archivo ya fue procesado."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            if archivo.tipo == "pacientes":
                resultado = pacientes_loader.cargar_pacientes(archivo.archivo.path)
            else:
                return Response(
                    {"error": f"Tipo de archivo '{archivo.tipo}' no reconocido."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            archivo.procesado = True
            archivo.save()

            return Response(
                {"mensaje": "Archivo procesado correctamente.", "resultado": resultado}
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
