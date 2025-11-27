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

    # Buscar pacientes específicos por RUT para tener control exacto
    maria = Paciente.objects.get(
        rut="11.111.111-1"
    )  # María González - sin score_social
    carlos = Paciente.objects.get(rut="22.222.222-2")  # Carlos Martínez - score 9
    ana = Paciente.objects.get(rut="33.333.333-3")  # Ana López - score 12 (para alerta)

    # Episodios activos (sin fecha de egreso)
    episodios_activos = [
        {
            "episodio_cmbd": 100001,
            "paciente": maria,
            "cama": camas[0] if len(camas) > 0 else None,
            "fecha_ingreso": timezone.now() - timedelta(days=5),
            "tipo_actividad": "Hospitalización",
            "especialidad": "Cardiología",
            "estancia_norma_grd": 3,  # Este debería aparecer como extensión crítica
            "prediccion_extension": 1,  # Predicción positiva de estadía larga
        },
        {
            "episodio_cmbd": 100002,
            "paciente": carlos,
            "cama": camas[1] if len(camas) > 1 else None,
            "fecha_ingreso": timezone.now() - timedelta(days=3),
            "tipo_actividad": "Hospitalización",
            "especialidad": "Medicina General",
            "estancia_norma_grd": 7,  # Este NO debería aparecer como extensión crítica
            "prediccion_extension": 0,  # Predicción negativa
        },
        {
            "episodio_cmbd": 100005,
            "paciente": ana,  # Ana López con score_social=12 para alerta
            "cama": camas[2] if len(camas) > 2 else None,
            "fecha_ingreso": timezone.now() - timedelta(days=10),
            "tipo_actividad": "Hospitalización",
            "especialidad": "Neurología",
            "estancia_norma_grd": 6,  # Este debería aparecer como extensión crítica
            "prediccion_extension": 0,  # Sin predicción positiva
        },
        {
            "episodio_cmbd": 100006,
            "paciente": carlos,  # Carlos Martínez con score_social=9
            "cama": camas[3] if len(camas) > 3 else None,
            "fecha_ingreso": timezone.now() - timedelta(days=4),  # 4 días de estadía
            "tipo_actividad": "Hospitalización",
            "especialidad": "Oncología",
            "estancia_norma_grd": 8,  # Norma es 8 días, límite crítico = 10.66 días
            "prediccion_extension": 1,  # ✅ Predicción positiva - modelo predice que se extenderá
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
            "estancia_norma_grd": 7.0,
            "inlier_outlier_flag": "Outlier",
            "estancia_postquirurgica": 32,
            "prediccion_extension": 0,  # Episodio cerrado
        },
        {
            "episodio_cmbd": 100004,
            "paciente": pacientes[3] if len(pacientes) > 3 else None,
            "cama": camas[3] if len(camas) > 3 else None,
            "fecha_ingreso": timezone.now() - timedelta(days=20),
            "fecha_egreso": timezone.now() - timedelta(days=17),
            "tipo_actividad": "Hospitalización",
            "especialidad": "Traumatología",
            "estancia_norma_grd": 4.0,
            "inlier_outlier_flag": "Inlier",
            "estancia_postquirurgica": 23,
            "prediccion_extension": 0,  # Episodio cerrado
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

    # Crear un índice por CMBD para evitar depender del orden
    epis_by_cmbd = {e.episodio_cmbd: e for e in episodios_guardados}
    medico_default = medicos_disponibles[0] if medicos_disponibles else None

    # Crear gestiones solo si tenemos episodios realmente guardados
    if episodios_guardados and medicos_disponibles:
        print(f"  📋 Creando gestiones para {len(episodios_guardados)} episodios...")

        gestiones_data = []

        # 100001 → HOMECARE_UCCC (EN_PROGRESO)
        if epis_by_cmbd.get(100001):
            gestiones_data.append(
                {
                    "episodio": epis_by_cmbd[100001],
                    "usuario": medico_default,
                    "tipo_gestion": "HOMECARE_UCCC",
                    "estado_gestion": "EN_PROGRESO",
                    "fecha_inicio": timezone.now() - timedelta(days=2),
                    "informe": "Paciente en seguimiento. Evolución favorable.",
                }
            )

        # 100002 → COORDINACION_UCCC (COMPLETADA)
        if epis_by_cmbd.get(100002):
            gestiones_data.append(
                {
                    "episodio": epis_by_cmbd[100002],
                    "usuario": medico_default,
                    "tipo_gestion": "COORDINACION_UCCC",
                    "estado_gestion": "COMPLETADA",
                    "fecha_inicio": timezone.now() - timedelta(days=1),
                    "fecha_fin": timezone.now() - timedelta(hours=2),
                    "informe": "Coordinación realizada con éxito.",
                }
            )

        # 100005 → TRASLADO (EN_PROGRESO) - Tipo de gestión distinto
        if epis_by_cmbd.get(100005):
            gestiones_data.append(
                {
                    "episodio": epis_by_cmbd[100005],
                    "usuario": medico_default,
                    "tipo_gestion": "TRASLADO",
                    "estado_gestion": "EN_PROGRESO",
                    "fecha_inicio": timezone.now() - timedelta(days=4),
                    "informe": "Traslado solicitado por equipo médico.",
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
