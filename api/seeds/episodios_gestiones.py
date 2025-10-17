"""
Seeds para episodios y gestiones del sistema UCChristus
"""

from datetime import datetime, timedelta

from django.utils import timezone

from api.models import Cama, Episodio, Gestion, Paciente, User


def create_episodios_y_gestiones():
    """Crea episodios y gestiones de prueba para el sistema"""
    print("📋 Creando episodios y gestiones...")

    # Asegurar que existen pacientes, camas y usuarios
    pacientes = list(Paciente.objects.all())
    camas = list(Cama.objects.all())
    medicos = list(User.objects.filter(rol="MEDICO"))

    if not pacientes:
        print("  ⚠️ No hay pacientes disponibles. Ejecuta primero el seed de pacientes.")
        return

    if not camas:
        print("  ⚠️ No hay camas disponibles. Ejecuta primero el seed de camas.")
        return

    if not medicos:
        print("  ⚠️ No hay médicos disponibles. Ejecuta primero el seed de usuarios.")
        return

    # Episodios activos (sin fecha de egreso)
    episodios_activos = [
        {
            "episodio_cmbd": 100001,
            "paciente": pacientes[0] if len(pacientes) > 0 else None,
            "cama": camas[0] if len(camas) > 0 else None,
            "fecha_ingreso": timezone.now() - timedelta(days=5),
            "tipo_actividad": "Hospitalización",
            "especialidad": "Cardiología",
        },
        {
            "episodio_cmbd": 100002,
            "paciente": pacientes[1] if len(pacientes) > 1 else None,
            "cama": camas[1] if len(camas) > 1 else None,
            "fecha_ingreso": timezone.now() - timedelta(days=3),
            "tipo_actividad": "Hospitalización",
            "especialidad": "Medicina General",
        },
    ]

    # Episodios cerrados (con fecha de egreso)
    episodios_cerrados = [
        {
            "episodio_cmbd": 100003,
            "paciente": pacientes[2] if len(pacientes) > 2 else None,
            "cama": camas[2] if len(camas) > 2 else None,
            "fecha_ingreso": timezone.now() - timedelta(days=15),
            "fecha_egreso": timezone.now() - timedelta(days=10),
            "tipo_actividad": "Hospitalización",
            "especialidad": "Cirugía General",
        },
        {
            "episodio_cmbd": 100004,
            "paciente": pacientes[3] if len(pacientes) > 3 else None,
            "cama": camas[3] if len(camas) > 3 else None,
            "fecha_ingreso": timezone.now() - timedelta(days=20),
            "fecha_egreso": timezone.now() - timedelta(days=17),
            "tipo_actividad": "Hospitalización",
            "especialidad": "Traumatología",
        },
    ]

    todos_episodios = episodios_activos + episodios_cerrados
    episodios_creados = []

    for episodio_data in todos_episodios:
        if episodio_data["paciente"] and episodio_data["cama"]:
            episodio, created = Episodio.objects.get_or_create(
                episodio_cmbd=episodio_data["episodio_cmbd"], defaults=episodio_data
            )
            if created:
                episodios_creados.append(episodio)
                estado = "Activo" if not episodio.fecha_egreso else "Cerrado"
                print(
                    f"  ✓ Creado episodio {episodio.episodio_cmbd}: {episodio.especialidad} - {estado}"
                )
            else:
                episodios_creados.append(episodio)
                print(f"  ℹ Ya existe episodio: {episodio.episodio_cmbd}")

    # IMPORTANTE: Volver a consultar episodios desde la base de datos para asegurar que existen
    episodios_guardados = list(Episodio.objects.all())
    medicos_disponibles = list(User.objects.filter(rol="MEDICO"))

    # Crear gestiones solo si tenemos episodios realmente guardados
    if episodios_guardados and medicos_disponibles:
        print(f"  📋 Creando gestiones para {len(episodios_guardados)} episodios...")

        gestiones_data = []

        # Gestion 1: Solo si tenemos al menos 1 episodio y 1 médico
        if len(episodios_guardados) >= 1 and len(medicos_disponibles) >= 1:
            gestiones_data.append(
                {
                    "episodio": episodios_guardados[0],
                    "usuario": medicos_disponibles[0],
                    "tipo_gestion": "HOMECARE_UCCC",
                    "estado_gestion": "EN_PROGRESO",
                    "fecha_inicio": timezone.now() - timedelta(days=2),
                    "informe": "Paciente en seguimiento. Evolución favorable.",
                }
            )

        # Gestion 2: Solo si tenemos al menos 2 episodios y médicos
        if len(episodios_guardados) >= 2 and len(medicos_disponibles) >= 2:
            gestiones_data.append(
                {
                    "episodio": episodios_guardados[1],
                    "usuario": (
                        medicos_disponibles[1]
                        if len(medicos_disponibles) > 1
                        else medicos_disponibles[0]
                    ),
                    "tipo_gestion": "COORDINACION_UCCC",
                    "estado_gestion": "COMPLETADA",
                    "fecha_inicio": timezone.now() - timedelta(days=1),
                    "fecha_fin": timezone.now() - timedelta(hours=2),
                    "informe": "Coordinación realizada con éxito.",
                }
            )

        # Gestion 3: Solo si tenemos al menos 3 episodios
        if len(episodios_guardados) >= 3:
            gestiones_data.append(
                {
                    "episodio": episodios_guardados[2],
                    "usuario": medicos_disponibles[0],
                    "tipo_gestion": "EVALUACION_UCCC",
                    "estado_gestion": "COMPLETADA",
                    "fecha_inicio": timezone.now() - timedelta(days=12),
                    "fecha_fin": timezone.now() - timedelta(days=11),
                    "informe": "Evaluación completada.",
                }
            )

        # Crear gestiones una por una
        for i, gestion_data in enumerate(gestiones_data):
            try:
                # Verificar que el episodio realmente existe antes de crear la gestión
                episodio_existe = Episodio.objects.filter(
                    id=gestion_data["episodio"].id
                ).exists()
                if not episodio_existe:
                    print(
                        f"  ⚠️  Episodio {gestion_data['episodio'].episodio_cmbd} no existe, saltando gestión"
                    )
                    continue

                gestion, created = Gestion.objects.get_or_create(
                    episodio=gestion_data["episodio"],
                    tipo_gestion=gestion_data["tipo_gestion"],
                    defaults={
                        "usuario": gestion_data["usuario"],
                        "estado_gestion": gestion_data["estado_gestion"],
                        "fecha_inicio": gestion_data["fecha_inicio"],
                        "fecha_fin": gestion_data.get("fecha_fin"),
                        "informe": gestion_data["informe"],
                    },
                )
                if created:
                    print(
                        f"  ✓ Creada gestión: {gestion.get_tipo_gestion_display()} - {gestion.get_estado_gestion_display()}"
                    )
                else:
                    print(
                        f"  ℹ Ya existe gestión: {gestion.get_tipo_gestion_display()}"
                    )
            except Exception as e:
                print(f"  ❌ Error creando gestión {i+1}: {e}")
                continue
    else:
        print(
            f"  ⚠️  No se pueden crear gestiones. Episodios: {len(episodios_guardados)}, Médicos: {len(medicos_disponibles)}"
        )

    print(f"  📊 Total episodios en sistema: {Episodio.objects.count()}")
    print(f"  📊 Total gestiones en sistema: {Gestion.objects.count()}")


if __name__ == "__main__":
    # Para ejecutar este archivo directamente
    import os
    import sys

    import django

    # Agregar el directorio raíz al path
    sys.path.append("/app")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    django.setup()

    create_episodios_y_gestiones()
