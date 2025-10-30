from datetime import date, timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from api.models import Episodio, Gestion, Paciente, User
from api.tests.base_test import AuthenticatedAPITestCase


class GestionActionsIntegrationTest(AuthenticatedAPITestCase):
    """Tests de integración para acciones personalizadas del ViewSet de Gestiones"""

    def setUp(self):
        self.authenticate_admin()

        # Crear paciente y usuario
        self.paciente = Paciente.objects.create(
            rut="12.345.678-9",
            nombre="Juan Pérez",
            sexo="M",
            fecha_nacimiento=date(1980, 1, 1),
        )
        self.usuario = User.objects.create(
            nombre="Felipe", apellido="Abarca", email="gestor@test.cl"
        )

        # Crear episodios
        self.episodio1 = Episodio.objects.create(
            paciente=self.paciente,
            episodio_cmbd=1,
            fecha_ingreso=timezone.now() - timedelta(days=5)
        )
        self.episodio2 = Episodio.objects.create(
            paciente=self.paciente,
            episodio_cmbd=2,
            fecha_ingreso=timezone.now() - timedelta(days=2)
        )

        # Crear gestiones con distintos estados y tipos
        self.gestion_iniciada = Gestion.objects.create(
            episodio=self.episodio1,
            usuario=self.usuario,
            tipo_gestion="GESTION_CLINICA",
            estado_gestion="INICIADA",
            fecha_inicio=timezone.now() - timedelta(days=4)
        )
        self.gestion_progreso = Gestion.objects.create(
            episodio=self.episodio1,
            usuario=self.usuario,
            tipo_gestion="TRASLADO",
            estado_gestion="EN_PROGRESO",
            fecha_inicio=timezone.now() - timedelta(days=3)
        )
        self.gestion_completada = Gestion.objects.create(
            episodio=self.episodio2,
            usuario=self.usuario,
            tipo_gestion="GESTION_CLINICA",
            estado_gestion="COMPLETADA",
            fecha_inicio=timezone.now() - timedelta(days=2),
            fecha_fin=timezone.now() - timedelta(days=1)
        )

    def test_pendientes(self):
        """GET /api/gestiones/pendientes/ devuelve solo INICIADA y EN_PROGRESO"""
        url = reverse("gestion-pendientes")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        for g in response.data:
            self.assertIn(g["estado_gestion"], {"INICIADA", "EN_PROGRESO"})
            
        self.assertEqual(len(response.data), 2)

    def test_estadisticas(self):
        """GET /api/gestiones/estadisticas/ devuelve totales y por tipo/estado"""
        url = reverse("gestion-estadisticas")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data
        self.assertIn("total_gestiones", data)
        self.assertIn("por_estado", data)
        self.assertIn("por_tipo", data)
        self.assertIn("por_tipo_gestion", data)

        self.assertEqual(data["total_gestiones"], 3)

        # Verificar que los contadores por estado sean correctos
        estado_map = {item["estado_gestion"]: item["cantidad"] for item in data["por_estado"]}
        self.assertEqual(estado_map.get("INICIADA", 0), 1)
        self.assertEqual(estado_map.get("EN_PROGRESO", 0), 1)
        self.assertEqual(estado_map.get("COMPLETADA", 0), 1)

    def test_tareas_pendientes(self):
        """GET /api/gestiones/tareas_pendientes/ devuelve solo INICIADA y EN_PROGRESO con formato esperado"""
        url = reverse("gestion-tareas-pendientes")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Solo las gestiones pendientes
        self.assertEqual(len(response.data), 2)

        for item in response.data:
            self.assertIn("id", item)
            self.assertIn("episodio", item)
            self.assertIn("tipo_gestion", item)
            self.assertIn("descripcion", item)
            self.assertIn("estado", item)
            self.assertIn("fecha_inicio", item)
            self.assertIn(item["estado"], ["Abierta", "En proceso"])
