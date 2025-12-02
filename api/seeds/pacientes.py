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
            # score_social: NULL
        },
        {
            "rut": "22.222.222-2",
            "nombre": "Carlos Martínez Silva",
            "fecha_nacimiento": date(1975, 8, 22),
            "sexo": "M",
            "prevision_1": "ISAPRE",
            "prevision_2": None,
            "score_social": 9,
        },
        {
            "rut": "33.333.333-3",
            "nombre": "Ana López Rivera",
            "fecha_nacimiento": date(1990, 12, 3),
            "sexo": "F",
            "prevision_1": "FONASA",
            "prevision_2": None,
            "score_social": 12,  # Score social alto para alerta
        },
        {
            "rut": "44.444.444-4",
            "nombre": "Pedro Rodríguez Castro",
            "fecha_nacimiento": date(1965, 3, 18),
            "sexo": "M",
            "prevision_1": "FONASA",
            "prevision_2": "PARTICULAR",
            "score_social": 15,
        },
        {
            "rut": "55.555.555-5",
            "nombre": "Carmen Hernández Torres",
            "fecha_nacimiento": date(1958, 11, 7),
            "sexo": "F",
            "prevision_1": "ISAPRE",
            "prevision_2": None,
            "score_social": 7,
        },
        {
            "rut": "66.666.666-6",
            "nombre": "Luis Vargas Morales",
            "fecha_nacimiento": date(1992, 6, 25),
            "sexo": "M",
            "prevision_1": "FONASA",
            "prevision_2": None,
            # score_social: NULL
        },
    ]

    for paciente_data in pacientes_data:
        score = paciente_data.pop("score_social", None)
        paciente, created = Paciente.objects.get_or_create(
            rut=paciente_data["rut"], defaults=paciente_data
        )
        if created:
            print(f"  ✓ Creado: {paciente.nombre} ({paciente.rut})")
        else:
            print(f"  ℹ Ya existe: {paciente.nombre} ({paciente.rut})")

        # Siempre setear score_social según el seed (permite resetear el estado)
        if score is not None:
            paciente.score_social = score
            paciente.save(update_fields=["score_social"])
            print(f"    ↳ score_social establecido en {score} para {paciente.nombre}")
        else:
            paciente.score_social = None
            paciente.save(update_fields=["score_social"])
            print(f"    ↳ score_social dejado en NULL para {paciente.nombre}")

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
