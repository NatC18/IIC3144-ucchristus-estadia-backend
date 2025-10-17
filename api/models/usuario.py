"""
Modelo de usuario personalizado para UC Christus
Optimizado para autenticación JWT
"""

import re
import uuid

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.exceptions import ValidationError
from django.db import models


def validar_rut_chileno(rut):
    """
    Validación básica de RUT chileno
    """
    if not rut:
        raise ValidationError("RUT es requerido")

    # Formato básico: XX.XXX.XXX-X o XXXXXXXX-X
    if not re.match(r"^\d{1,2}\.?\d{3}\.?\d{3}-[\dkK]$", rut):
        raise ValidationError("Formato de RUT inválido. Use: XX.XXX.XXX-X")


class UserManager(BaseUserManager):
    """
    Manager personalizado para el modelo User
    """

    def create_user(self, email, password=None, **extra_fields):
        """
        Crear usuario regular
        """
        if not email:
            raise ValueError("El email es requerido")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Crear superusuario
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("rol", "ADMIN")

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Modelo de usuario personalizado para UC Christus
    Optimizado para JWT authentication
    """

    # Choices para roles
    ROL_CHOICES = [
        ("ADMIN", "Administrador"),
        ("MEDICO", "Médico"),
        ("ENFERMERO", "Enfermero/a"),
        ("RECEPCION", "Recepción"),
        ("OTRO", "Otro"),
    ]

    # Campos principales - usando UUID como primary key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, verbose_name="Correo electrónico")
    rut = models.CharField(
        max_length=12,
        unique=True,
        validators=[validar_rut_chileno],
        help_text="Formato: XX.XXX.XXX-X",
    )

    # Información personal
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    apellido = models.CharField(max_length=100, verbose_name="Apellido")
    rol = models.CharField(max_length=20, choices=ROL_CHOICES, default="OTRO")

    # Campos de Django auth
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    # Timestamps
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)

    # Manager personalizado
    objects = UserManager()

    # Configuración de autenticación
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["nombre", "apellido", "rut"]

    class Meta:
        db_table = "usuarios"
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        ordering = ["apellido", "nombre"]

    def __str__(self):
        return f"{self.nombre} {self.apellido} ({self.email})"

    @property
    def nombre_completo(self):
        """Retorna el nombre completo del usuario"""
        return f"{self.nombre} {self.apellido}"

    def get_full_name(self):
        """Método requerido por Django"""
        return self.nombre_completo

    def get_short_name(self):
        """Método requerido por Django"""
        return self.nombre

    @property
    def is_admin(self):
        """Verifica si el usuario es administrador"""
        return self.rol == "ADMIN" or self.is_superuser

    @property
    def is_medical_staff(self):
        """Verifica si el usuario es personal médico"""
        return self.rol in ["MEDICO", "ENFERMERO"]
