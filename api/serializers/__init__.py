from .auth import (
    ChangePasswordSerializer,
    CustomTokenObtainPairSerializer,
    UserListSerializer,
    UserProfileSerializer,
    UserRegistrationSerializer,
)
from .cama import CamaSerializer
from .episodio import (
    EpisodioCreateSerializer,
    EpisodioListSerializer,
    EpisodioSerializer,
    EpisodioUpdateSerializer,
)
from .episodioServicio import EpisodioServicioSerializer
from .gestion import (
    GestionCreateSerializer,
    GestionListSerializer,
    GestionSerializer,
    GestionUpdateSerializer,
)
from .nota import (
    NotaCreateSerializer,
    NotaListSerializer,
    NotaSerializer,
    NotaUpdateSerializer,
)
from .paciente import (
    PacienteCreateSerializer,
    PacienteListSerializer,
    PacienteSerializer,
)
from .servicio import ServicioSerializer

__all__ = [
    "PacienteSerializer",
    "PacienteCreateSerializer",
    "PacienteListSerializer",
    "CustomTokenObtainPairSerializer",
    "UserRegistrationSerializer",
    "UserProfileSerializer",
    "ChangePasswordSerializer",
    "UserListSerializer",
    "GestionSerializer",
    "GestionCreateSerializer",
    "GestionListSerializer",
    "GestionUpdateSerializer",
    "NotaSerializer",
    "NotaCreateSerializer",
    "NotaListSerializer",
    "NotaUpdateSerializer",
    "CamaSerializer",
    "EpisodioServicioSerializer",
    "EpisodioSerializer",
    "EpisodioCreateSerializer",
    "EpisodioListSerializer",
    "EpisodioUpdateSerializer",
    "ServicioSerializer",
]
