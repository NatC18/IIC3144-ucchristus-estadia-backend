from .paciente import PacienteViewSet
from .auth import login, register, logout, profile

__all__ = ['PacienteViewSet', 'login', 'register', 'logout', 'profile']