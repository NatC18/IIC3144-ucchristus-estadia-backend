from datetime import timedelta, date
from django.test import TestCase
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from api.models import Episodio, Paciente, User, Gestion
from api.serializers.gestion import GestionUpdateSerializer


class GestionUpdateSerializerValidateTest(TestCase):
    """Tests unitarios para el método validate() de GestionUpdateSerializer"""

    def setUp(self):
        # Crear paciente y usuario base
        self.paciente = Paciente.objects.create(
            rut="12.345.678-9",
            nombre="María Gómez",
            sexo="F",
            fecha_nacimiento=date(1985, 4, 15),
            prevision_1="FONASA",
        )

        self.usuario = User.objects.create(
            nombre="Sofía",
            apellido="Pérez",
            email="sofia.perez@test.cl",
        )

        self.episodio = Episodio.objects.create(
            paciente=self.paciente,
            episodio_cmbd=1,
            fecha_ingreso=timezone.now() - timedelta(days=5),
        )

        # Gestión inicial (a actualizar)
        self.gestion = Gestion.objects.create(
            episodio=self.episodio,
            usuario=self.usuario,
            tipo_gestion="TRASLADO",
            estado_gestion="INICIADA",
            fecha_inicio=timezone.now() - timedelta(days=2),
            fecha_fin=None,
            informe="Gestión inicial en proceso.",
        )

    def test_no_permite_fecha_fin_antes_de_inicio(self):
        """Debe lanzar error si la fecha_fin es anterior a la fecha_inicio"""
        data = {
            "fecha_inicio": self.gestion.fecha_inicio,
            "fecha_fin": self.gestion.fecha_inicio - timedelta(days=1),
            "estado_gestion": "COMPLETADA",
        }

        serializer = GestionUpdateSerializer(instance=self.gestion, data=data, partial=True)
        self.assertFalse(serializer.is_valid())
        self.assertIn("fecha_fin", serializer.errors)
        self.assertEqual(
            serializer.errors["fecha_fin"][0],
            "La fecha de fin debe ser posterior a la fecha de inicio",
        )

    def test_estado_completada_requiere_fecha_fin(self):
        """Debe lanzar error si se marca COMPLETADA sin fecha_fin"""
        data = {
            "estado_gestion": "COMPLETADA",
            "fecha_fin": None,
        }

        serializer = GestionUpdateSerializer(instance=self.gestion, data=data, partial=True)
        self.assertFalse(serializer.is_valid())
        self.assertIn("fecha_fin", serializer.errors)
        self.assertEqual(
            serializer.errors["fecha_fin"][0],
            "Una gestión completada debe tener fecha de fin",
        )

    def test_validacion_exitosa(self):
        """Debe validar correctamente una actualización válida"""
        data = {
            "estado_gestion": "COMPLETADA",
            "fecha_fin": timezone.now(),
            "informe": "Traslado completado correctamente.",
        }

        serializer = GestionUpdateSerializer(instance=self.gestion, data=data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        gestion_actualizada = serializer.save()
        self.assertEqual(gestion_actualizada.estado_gestion, "COMPLETADA")
        self.assertIsNotNone(gestion_actualizada.fecha_fin)
        self.assertIn("Traslado completado", gestion_actualizada.informe)
