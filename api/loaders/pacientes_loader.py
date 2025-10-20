import pandas as pd

from api.models import Paciente
from api.models.paciente import validar_rut


def cargar_pacientes(file_path):
    df = pd.read_excel(file_path)
    columnas = {"rut", "nombre", "sexo", "fecha_nacimiento"}
    if not columnas.issubset(df.columns):
        raise ValueError(f"Faltan columnas requeridas: {columnas - set(df.columns)}")

    creados, actualizados = 0, 0
    for _, row in df.iterrows():
        rut = str(row["rut"]).strip()
        validar_rut(rut)
        paciente, created = Paciente.objects.update_or_create(
            rut=rut,
            defaults={
                "nombre": row["nombre"],
                "sexo": row["sexo"],
                "fecha_nacimiento": row["fecha_nacimiento"],
                "prevision_1": row.get("prevision_1"),
                "prevision_2": row.get("prevision_2"),
                "convenio": row.get("convenio"),
                "score_social": row.get("score_social"),
            },
        )
        if created:
            creados += 1
        else:
            actualizados += 1

    return {"creados": creados, "actualizados": actualizados}
