from datetime import date
from django.utils import timezone
from rest_framework import status
from api.models import Episodio, Gestion, Paciente
from api.tests.base_test import AuthenticatedAPITestCase

class GestionTrasladoIntegrationTest(AuthenticatedAPITestCase):
    """Test de Integración: Gestión de Traslados (Nuevos campos en Gestion)"""

    def setUp(self):
        self.authenticate_admin()

        self.paciente = Paciente.objects.create(
            rut="12.345.678-9",
            nombre="Juan Pérez",
            sexo="M",
            fecha_nacimiento=date(1990, 6, 15),
        )

        self.episodio = Episodio.objects.create(
            paciente=self.paciente,
            episodio_cmbd=1001,
            fecha_ingreso=timezone.now(),
        )

        self.url = "/api/gestiones/"

    def test_crear_gestion_traslado_completa(self):
        """Debe permitir crear una gestión de tipo TRASLADO con todos sus campos"""
        data = {
            "episodio": str(self.episodio.id),
            "tipo_gestion": "TRASLADO",
            "estado_gestion": "INICIADA",
            "fecha_inicio": timezone.now().isoformat(),
            "descripcion": "Solicitud de traslado",
            # Campos específicos de traslado
            "estado_traslado": "PENDIENTE",
            "tipo_traslado": "URGENCIA",
            "motivo_traslado": "Requiere mayor complejidad",
            "centro_destinatario": "Hospital Central",
            "tipo_solicitud_traslado": "TRASLADO_SALIDA",
            "nivel_atencion_traslado": "CUIDADOS_INTENSIVOS"
        }

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", response.data)
        
        gestion = Gestion.objects.get(id=response.data["id"])
        self.assertEqual(gestion.tipo_gestion, "TRASLADO")
        self.assertEqual(gestion.estado_traslado, "PENDIENTE")
        self.assertEqual(gestion.tipo_traslado, "URGENCIA")
        self.assertEqual(gestion.motivo_traslado, "Requiere mayor complejidad")
        self.assertEqual(gestion.centro_destinatario, "Hospital Central")
        self.assertEqual(gestion.tipo_solicitud_traslado, "TRASLADO_SALIDA")
        self.assertEqual(gestion.nivel_atencion_traslado, "CUIDADOS_INTENSIVOS")

    def test_actualizar_gestion_traslado(self):
        """Debe permitir actualizar los campos de traslado"""
        gestion = Gestion.objects.create(
            episodio=self.episodio,
            tipo_gestion="TRASLADO",
            estado_gestion="INICIADA",
            fecha_inicio=timezone.now(),
            estado_traslado="PENDIENTE"
        )

        url_detalle = f"{self.url}{gestion.id}/"
        data = {
            "estado_traslado": "COMPLETADO",
            "motivo_rechazo_traslado": None, # Limpiar si hubiera
            "fecha_finalizacion_traslado": timezone.now().isoformat()
        }

        response = self.client.patch(url_detalle, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        gestion.refresh_from_db()
        self.assertEqual(gestion.estado_traslado, "COMPLETADO")
        self.assertIsNotNone(gestion.fecha_finalizacion_traslado)

    def test_rechazar_traslado(self):
        """Debe permitir registrar el rechazo de un traslado"""
        gestion = Gestion.objects.create(
            episodio=self.episodio,
            tipo_gestion="TRASLADO",
            estado_gestion="INICIADA",
            fecha_inicio=timezone.now(),
            estado_traslado="PENDIENTE"
        )

        url_detalle = f"{self.url}{gestion.id}/"
        data = {
            "estado_traslado": "RECHAZADO",
            "motivo_rechazo_traslado": "No hay camas disponibles"
        }

        response = self.client.patch(url_detalle, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        gestion.refresh_from_db()
        self.assertEqual(gestion.estado_traslado, "RECHAZADO")
        self.assertEqual(gestion.motivo_rechazo_traslado, "No hay camas disponibles")
