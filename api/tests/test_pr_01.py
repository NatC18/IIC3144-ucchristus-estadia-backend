from rest_framework import status
from django.contrib.auth import get_user_model
from api.tests.base_test import AuthenticatedAPITestCase

User = get_user_model()


class LoginIntegrationTest(AuthenticatedAPITestCase):
    """PR-01 | HU-01 | Test de Integración: Inicio de sesión con credenciales válidas e inválidas"""

    def setUp(self):
        # Crear usuario válido
        self.user = User.objects.create_user(
            email="admin@ucchristus.cl",
            password="admin123",
            nombre="Admin",
            apellido="UC",
            rut="11.111.111-1",
            rol="ADMINISTRADOR",
        )
        self.url = "/api/auth/login/"

    def test_login_valido(self):
        """Debe autenticar correctamente con credenciales válidas"""
        data = {"email": "admin@ucchristus.cl", "password": "admin123"}
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertIn("user", response.data)
        self.assertEqual(response.data["user"]["email"], "admin@ucchristus.cl")

    def test_login_invalido(self):
        """Debe rechazar credenciales inválidas"""
        data = {"email": "admin@ucchristus.cl", "password": "incorrecta"}
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("detail", response.data)
