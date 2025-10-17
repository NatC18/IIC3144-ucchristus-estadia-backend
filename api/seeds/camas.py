"""
Seeds para camas del sistema UCChristus
"""

from api.models import Cama


def create_camas():
    """Crea camas de prueba para el sistema"""
    print("🛏️ Creando camas...")

    # Camas UCI
    camas_uci = [
        {"codigo_cama": "101", "habitacion": "UCI-A1"},
        {"codigo_cama": "102", "habitacion": "UCI-A2"},
        {"codigo_cama": "103", "habitacion": "UCI-A3"},
        {"codigo_cama": "104", "habitacion": "UCI-B1"},
        {"codigo_cama": "105", "habitacion": "UCI-B2"},
    ]

    for cama_data in camas_uci:
        cama, created = Cama.objects.get_or_create(
            codigo_cama=cama_data["codigo_cama"], defaults=cama_data
        )
        if created:
            print(f"  ✓ Creada: Cama {cama.codigo_cama} - {cama.habitacion}")
        else:
            print(f"  ℹ Ya existe: Cama {cama.codigo_cama} - {cama.habitacion}")

    # Camas Cardiología
    camas_cardio = [
        {"codigo_cama": "201", "habitacion": "CARDIO-101"},
        {"codigo_cama": "202", "habitacion": "CARDIO-102"},
        {"codigo_cama": "203", "habitacion": "CARDIO-103"},
    ]

    for cama_data in camas_cardio:
        cama, created = Cama.objects.get_or_create(
            codigo_cama=cama_data["codigo_cama"], defaults=cama_data
        )
        if created:
            print(f"  ✓ Creada: Cama {cama.codigo_cama} - {cama.habitacion}")
        else:
            print(f"  ℹ Ya existe: Cama {cama.codigo_cama} - {cama.habitacion}")

    # Camas Medicina General
    camas_medicina = [
        {"codigo_cama": "301", "habitacion": "MED-201"},
        {"codigo_cama": "302", "habitacion": "MED-202"},
        {"codigo_cama": "303", "habitacion": "MED-203"},
        {"codigo_cama": "304", "habitacion": "MED-204"},
    ]

    for cama_data in camas_medicina:
        cama, created = Cama.objects.get_or_create(
            codigo_cama=cama_data["codigo_cama"], defaults=cama_data
        )
        if created:
            print(f"  ✓ Creada: Cama {cama.codigo_cama} - {cama.habitacion}")
        else:
            print(f"  ℹ Ya existe: Cama {cama.codigo_cama} - {cama.habitacion}")

    print(f"  📊 Total camas en sistema: {Cama.objects.count()}")


if __name__ == "__main__":
    # Para ejecutar este archivo directamente
    import os
    import sys

    import django

    # Agregar el directorio raíz al path
    sys.path.append("/app")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    django.setup()

    create_camas()
