"""
Seeds para servicios del sistema UCChristus
"""

from datetime import date

from api.models import Servicio


def create_servicios():
    """Crea servicios en el sistema"""
    print("🧑‍🔧 Creando servicios...")

    servicios_data = [
        ("UEUNICOR", "Unidad Coronaria"),
        ("UEINAD", "Unidad Paciente Crítico"),
        ("UERECUP6", "Intensivo Cardiovascular"),
        ("UEINAD4", "Unidad Paciente Crítico"),
        ("UEMULTI2", "Médico Quirúrgico"),
        ("UEMEQX4A", "Médico Quirúrgico"),
        ("UEPENMAT", "Maternidad"),
        ("UEMEQX4B", "Médico Quirúrgico"),
        ("UEMEQ2ED", "Médico Quirúrgico"),
        ("UEMEQX4C", "Médico Quirúrgico"),
        ("UEMEQ4DE", "Médico Quirúrgico"),
        ("UEONCCLI", "Oncología"),
        ("UEMEQCLI", "Médico Quirúrgico"),
        ("UEOCLI10", "Oncología"),
        ("UEMECLI5", "Médico Quirúrgico"),
        ("UEMECLI7", "Oncología"),
        ("UEONCLI8", "Oncología"),
        ("UEMECLI4", "Médico Quirúrgico"),
        ("UETRAMEN", "Intermedio Médico Neurológico"),
        ("UEINT8", "Intermedio 8Vo"),
        ("UEINTCLI", "Intermedio Clínica"),
        ("UETRAME2", "Intermedio Médico Neurológico"),
        ("UEINTM5B", "Intermedio 5B"),
        ("UEINTM5C", "Intermedio Médico Neurológico"),
        ("UENEONAT", "Neonatología"),
        ("UEINMPED", "Intermedio Pediátrico"),
        ("UEPEDIAT", "Pediatría"),
        ("UEINSPED", "Intensivo Pediátrico"),
        ("UEONCPED", "Oncología Pediátrica"),
        ("UEPEDCLI", "Oncología Pediátrica"),
        ("UEMEQX5A", "Médico Quirúrgico"),
        ("UEMEQX5B", "Médico Quirúrgico"),
        ("UEMEQX5C", "Médico Quirúrgico"),
        ("UEMECLI3", "Médico Quirúrgico"),
        ("UEMECLI6", "Médico Quirúrgico"),
    ]


    for servicio_data in servicios_data:
        servicio, created = Servicio.objects.get_or_create(
            codigo=servicio_data[0], defaults={"descripcion": servicio_data[1]}
        )
        if created:
            print(f"  ✓ Creado: {servicio.codigo} ({servicio.descripcion})")
        else:
            print(f"  ℹ Ya existe: {servicio.codigo} ({servicio.descripcion})")

    print(f"  📊 Total servicios en sistema: {Servicio.objects.count()}")


if __name__ == "__main__":
    # Para ejecutar este archivo directamente
    import os
    import sys

    import django

    # Agregar el directorio raíz al path
    sys.path.append("/app")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    django.setup()

    create_servicios()
