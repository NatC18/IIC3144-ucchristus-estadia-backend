"""
Seeds para pacientes del sistema UCChristus
"""

from datetime import date

from api.models import Paciente


def create_pacientes():
    """Crea pacientes de prueba para el sistema"""
    print("🧑‍🦽 Creando pacientes...")

    pacientes_data = [
        {
            "rut": "11.111.111-1",
            "nombre": "María González Pérez",
            "fecha_nacimiento": date(1980, 5, 15),
            "sexo": "F",
            "prevision_1": "FONASA",
            "prevision_2": "ISAPRE",
        },
        {
            "rut": "22.222.222-2",
            "nombre": "Carlos Martínez Silva",
            "fecha_nacimiento": date(1975, 8, 22),
            "sexo": "M",
            "prevision_1": "ISAPRE",
            "prevision_2": None,
        },
        {
            "rut": "33.333.333-3",
            "nombre": "Ana López Rivera",
            "fecha_nacimiento": date(1990, 12, 3),
            "sexo": "F",
            "prevision_1": "FONASA",
            "prevision_2": None,
        },
        {
            "rut": "44.444.444-4",
            "nombre": "Pedro Rodríguez Castro",
            "fecha_nacimiento": date(1965, 3, 18),
            "sexo": "M",
            "prevision_1": "FONASA",
            "prevision_2": "PARTICULAR",
        },
        {
            "rut": "55.555.555-5",
            "nombre": "Carmen Hernández Torres",
            "fecha_nacimiento": date(1958, 11, 7),
            "sexo": "F",
            "prevision_1": "ISAPRE",
            "prevision_2": None,
        },
        {
            "rut": "66.666.666-6",
            "nombre": "Luis Vargas Morales",
            "fecha_nacimiento": date(1992, 6, 25),
            "sexo": "M",
            "prevision_1": "FONASA",
            "prevision_2": None,
        },
    ]

    for paciente_data in pacientes_data:
        paciente, created = Paciente.objects.get_or_create(
            rut=paciente_data["rut"], defaults=paciente_data
        )
        if created:
            print(f"  ✓ Creado: {paciente.nombre} ({paciente.rut})")
        else:
            print(f"  ℹ Ya existe: {paciente.nombre} ({paciente.rut})")

    print(f"  📊 Total pacientes en sistema: {Paciente.objects.count()}")


if __name__ == "__main__":
    # Para ejecutar este archivo directamente
    import os
    import sys

    import django

    # Agregar el directorio raíz al path
    sys.path.append("/app")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    django.setup()

    create_pacientes()
