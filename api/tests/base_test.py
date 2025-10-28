from rest_framework.test import APITestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

class AuthenticatedAPITestCase(APITestCase):
    """Clase base para tests autenticados con el usuario admin base"""

    def authenticate_admin(self):
        """Crea (si no existe) y autentica al usuario admin base"""
        # Crear usuario admin en la BD de test
        if not User.objects.filter(email="admin@ucchristus.cl").exists():
            User.objects.create_user(
                email="admin@ucchristus.cl",
                password="admin123",
                nombre="Admin",
                apellido="UC",
                rut="11.111.111-1",
                rol="ADMIN",
                is_staff=True,
                is_active=True,
            )

        # Autenticación JWT
        login_url = reverse("token_obtain_pair")
        credentials = {"email": "admin@ucchristus.cl", "password": "admin123"}
        response = self.client.post(login_url, credentials, format="json")

        assert response.status_code == 200, f"Error autenticando admin: {response.data}"

        token = response.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
