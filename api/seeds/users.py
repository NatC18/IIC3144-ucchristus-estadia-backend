"""
Seeds para usuarios del sistema UCChristus
"""

import os

from django.utils import timezone

from api.models import User


def create_users():
    """Crea usuarios de prueba para el sistema"""
    print("🧑‍⚕️ Creando usuarios...")

    # Usuario Admin del Sistema
    admin_user, created = User.objects.get_or_create(
        email="admin@ucchristus.cl",
        defaults={
            "rut": "12.345.678-9",
            "nombre": "Admin",
            "apellido": "Sistema",
            "rol": "ADMIN",
            "is_staff": True,
            "is_superuser": True,
        },
    )
    if created:
        admin_user.set_password("admin123")
        admin_user.save()
        print(
            f"  ✓ Creado: {admin_user.nombre} {admin_user.apellido} ({admin_user.rol})"
        )
    else:
        print(f"  ℹ Ya existe: {admin_user.nombre} {admin_user.apellido}")

    # Médicos
    medicos = [
        {
            "email": "dr.martinez@ucchristus.cl",
            "rut": "15.234.567-8",
            "nombre": "Dr. Carlos",
            "apellido": "Martínez",
            "rol": "MEDICO",
        },
        {
            "email": "dra.rodriguez@ucchristus.cl",
            "rut": "16.345.678-9",
            "nombre": "Dra. María",
            "apellido": "Rodríguez",
            "rol": "MEDICO",
        },
        {
            "email": "dr.gonzalez@ucchristus.cl",
            "rut": "17.456.789-0",
            "nombre": "Dr. Juan",
            "apellido": "González",
            "rol": "MEDICO",
        },
    ]

    for medico_data in medicos:
        medico, created = User.objects.get_or_create(
            email=medico_data["email"], defaults=medico_data
        )
        if created:
            medico.set_password("medico123")
            medico.save()
            print(f"  ✓ Creado: {medico.nombre} {medico.apellido} ({medico.rol})")
        else:
            print(f"  ℹ Ya existe: {medico.nombre} {medico.apellido}")

    # Enfermeros
    enfermeros = [
        {
            "email": "enf.silva@ucchristus.cl",
            "rut": "18.567.890-1",
            "nombre": "Carmen",
            "apellido": "Silva",
            "rol": "ENFERMERO",
        },
        {
            "email": "enf.rivera@ucchristus.cl",
            "rut": "18.567.890-3",
            "nombre": "Tiana",
            "apellido": "Rivera",
            "rol": "ENFERMERO",
        },
        {
            "email": "enf.munic@ucchristus.cl",
            "rut": "18.567.890-2",
            "nombre": "Paolo",
            "apellido": "Munic",
            "rol": "ENFERMERO",
        },
        {
            "email": "enf.lopez@ucchristus.cl",
            "rut": "19.678.901-2",
            "nombre": "Patricia",
            "apellido": "López",
            "rol": "ENFERMERO",
        },
    ]

    for enfermero_data in enfermeros:
        enfermero, created = User.objects.get_or_create(
            email=enfermero_data["email"], defaults=enfermero_data
        )
        if created:
            enfermero.set_password("enfermero123")
            enfermero.save()
            print(
                f"  ✓ Creado: {enfermero.nombre} {enfermero.apellido} ({enfermero.rol})"
            )
        else:
            print(f"  ℹ Ya existe: {enfermero.nombre} {enfermero.apellido}")

    # Personal de Recepción
    recepcion = [
        {
            "email": "rec.morales@ucchristus.cl",
            "rut": "20.789.012-3",
            "nombre": "Ana",
            "apellido": "Morales",
            "rol": "RECEPCION",
        }
    ]

    for recep_data in recepcion:
        recep, created = User.objects.get_or_create(
            email=recep_data["email"], defaults=recep_data
        )
        if created:
            recep.set_password("recepcion123")
            recep.save()
            print(f"  ✓ Creado: {recep.nombre} {recep.apellido} ({recep.rol})")
        else:
            print(f"  ℹ Ya existe: {recep.nombre} {recep.apellido}")

    print(f"  📊 Total usuarios en sistema: {User.objects.count()}")


if __name__ == "__main__":
    # Para ejecutar este archivo directamente
    import os
    import sys

    import django

    # Agregar el directorio raíz al path
    sys.path.append("/app")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    django.setup()

    create_users()
