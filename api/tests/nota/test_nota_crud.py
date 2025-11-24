from datetime import date
from django.utils import timezone
from rest_framework import status
from api.models import Episodio, Gestion, Paciente, Nota
from api.tests.base_test import AuthenticatedAPITestCase

class NotaCRUDIntegrationTest(AuthenticatedAPITestCase):
    """Test de Integración: CRUD de Notas"""

    def setUp(self):
        self.authenticate_admin()

        # Crear datos base: Paciente, Episodio, Gestion
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

        self.gestion = Gestion.objects.create(
            episodio=self.episodio,
            tipo_gestion="GESTION_CLINICA",
            estado_gestion="INICIADA",
            fecha_inicio=timezone.now(),
        )

        self.url = "/api/notas/"

    def test_crear_nota(self):
        """Debe permitir crear una nota asociada a una gestión"""
        data = {
            "gestion": str(self.gestion.id),
            "descripcion": "Nota de prueba",
            "estado": "pendiente"
        }

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # El serializer de creación no retorna ID, verificamos persistencia
        # self.assertIn("id", response.data)
        self.assertEqual(response.data["descripcion"], "Nota de prueba")
        self.assertEqual(response.data["estado"], "pendiente")
        
        # Verificar persistencia
        nota = Nota.objects.filter(gestion=self.gestion, descripcion="Nota de prueba").first()
        self.assertIsNotNone(nota)
        self.assertEqual(nota.gestion.id, self.gestion.id)

    def test_listar_notas(self):
        """Debe listar las notas existentes"""
        # Limpiar notas previas si existen (por si acaso)
        Nota.objects.all().delete()
        
        Nota.objects.create(
            gestion=self.gestion,
            descripcion="Nota 1",
            estado="pendiente"
        )
        Nota.objects.create(
            gestion=self.gestion,
            descripcion="Nota 2",
            estado="lista"
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Manejar paginación
        if "results" in response.data:
            results = response.data["results"]
        else:
            results = response.data

        self.assertEqual(len(results), 2)

    def test_actualizar_nota(self):
        """Debe permitir actualizar una nota (ej. cambiar estado)"""
        nota = Nota.objects.create(
            gestion=self.gestion,
            descripcion="Nota original",
            estado="pendiente"
        )

        url_detalle = f"{self.url}{nota.id}/"
        data = {
            "descripcion": "Nota actualizada",
            "estado": "lista"
        }

        response = self.client.put(url_detalle, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["estado"], "lista")
        self.assertEqual(response.data["descripcion"], "Nota actualizada")

        nota.refresh_from_db()
        self.assertEqual(nota.estado, "lista")
        self.assertEqual(nota.descripcion, "Nota actualizada")

    def test_eliminar_nota(self):
        """Debe permitir eliminar una nota"""
        nota = Nota.objects.create(
            gestion=self.gestion,
            descripcion="Nota a eliminar",
            estado="pendiente"
        )

        url_detalle = f"{self.url}{nota.id}/"
        response = self.client.delete(url_detalle)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Nota.objects.filter(id=nota.id).exists())
