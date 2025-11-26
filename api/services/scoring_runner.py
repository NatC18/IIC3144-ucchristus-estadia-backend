"""
Construye las features del modelo a partir del Excel GRD (excel1) y ejecuta
scoring usando el modelo/metadata guardados en api/modelo.
"""

import re
import numpy as np
import pandas as pd

from .scoring import score_dataframe, load_preprocessing
from api.models import Episodio


def _to_float(series: pd.Series) -> pd.Series:
    return (
        series.astype(str)
        .str.replace(",", ".", regex=False)
        .replace(["nan", "None", ""], np.nan)
        .astype(float)
    )


def _map_ir(text: str) -> float:
    if text is None or (isinstance(text, float) and np.isnan(text)):
        return np.nan
    t = str(text).strip().upper()
    mapping = {
        "SIN GRAVEDAD": 0,
        "SIN GRAVEDAD.": 0,
        "SIN GRAVEDAD ": 0,
        "SIN DATO": np.nan,
        "MENOR": 1,
        "MODERADA": 2,
        "MAYOR": 3,
    }
    return mapping.get(t, np.nan)


def _map_ir_tipo(text: str) -> float:
    if text is None or (isinstance(text, float) and np.isnan(text)):
        return -1
    t = str(text).strip().upper()
    mapping = {"M": 0, "N": 1, "O": 2, "Q": 3, "X": 4}
    return mapping.get(t, -1)


def _apply_encoders(features: pd.DataFrame, preproc: dict) -> pd.DataFrame:
    """Aplica LabelEncoders guardados en preprocessing. Valores no vistos -> -1."""
    encoders = preproc.get("encoders") or {}
    if not encoders:
        return features

    feats = features.copy()
    for col, le in encoders.items():
        if col not in feats.columns:
            continue
        vals = feats[col].astype(str)
        known = set(le.classes_)
        mapped = []
        for v in vals:
            if v in known:
                mapped.append(le.transform([v])[0])
            else:
                mapped.append(-1)
        feats[col] = mapped
        feats[col] = feats[col].astype(int)
    return feats


def build_features_from_grd(df_grd: pd.DataFrame) -> pd.DataFrame:
    """
    A partir del Excel GRD (excel1), construye las 17 columnas del modelo.
    Columnas origen esperadas (tal cual en el GRD):
      - Edad en años, Sexo  (Desc), Tipo Ingreso (Descripción), Prevision (Cód),
        Servicio Ingreso (Código), Diagnóstico   Principal, Conjunto Dx,
        Proced 01 Principal    (cod), Conjunto Procedimientos Secundarios,
        Conjunto de Servicios Traslado, Estancia Norma GRD, Peso GRD Medio (Todos),
        IR Gravedad  (desc), IR Mortalidad  (desc), IR Tipo GRD, IR GRD (Código)
    """
    out = pd.DataFrame()

    edad_col = next((c for c in ["Edad en años", "Edad en Años", "edad", "Edad"] if c in df_grd.columns), None)
    if not edad_col:
        raise ValueError("Falta columna de edad en el GRD")
    out["edad"] = _to_float(df_grd[edad_col])

    # Normalizar sexo: femenino=0, masculino=1
    sexo_norm = (
        df_grd["Sexo  (Desc)"]
        .astype(str)
        .str.strip()
        .str.upper()
        .replace({"NAN": None, "": None, "NONE": None})
    )
    sexo_map = {
        "MUJER": 0,
        "FEMENINO": 0,
        "F": 0,
        "HOMBRE": 1,
        "MASCULINO": 1,
        "M": 1,
    }
    out["sexo"] = sexo_norm.map(sexo_map)

    tipo_map = {"Obstétrica": 0, "Programado": 1, "Urgente": 2}
    out["tipo_ingreso"] = df_grd["Tipo Ingreso (Descripción)"].map(tipo_map)

    out["prevision"] = df_grd["Prevision (Cód)"].astype(str)
    out["serv_ingreso"] = df_grd["Servicio Ingreso (Código)"].astype(str)
    out["diagnostico_principal"] = df_grd["Diagnóstico   Principal"].astype(str)

    # Conteos
    out["n_diagnosticos"] = (
        df_grd["Conjunto Dx"]
        .fillna("")
        .apply(lambda x: len(re.findall(r"\[(.*?)\]", str(x))))
    )

    out["procedimiento_principal"] = (
        df_grd["Proced 01 Principal    (cod)"].fillna(-1).astype(int)
    )

    out["n_procedimientos_sec"] = (
        df_grd["Conjunto Procedimientos Secundarios"]
        .fillna("")
        .apply(lambda x: len(re.findall(r"\[(.*?)\]", str(x))))
    )

    out["n_servicios"] = (
        df_grd["Conjunto de Servicios Traslado"]
        .fillna("")
        .apply(lambda x: len(re.findall(r"\[(.*?)\]", str(x))))
    )

    out["estancia_norma_grd"] = _to_float(df_grd["Estancia Norma GRD"])
    out["peso_grd_medio"] = _to_float(df_grd["Peso GRD Medio (Todos)"])

    out["ir_gravedad"] = df_grd["IR Gravedad  (desc)"].apply(_map_ir)
    out["ir_mortalidad"] = df_grd["IR Mortalidad  (desc)"].apply(_map_ir)
    out["ir_tipo_grd"] = df_grd["IR Tipo GRD"].apply(_map_ir_tipo)

    out["ir_grd_codigo"] = df_grd["IR GRD (Código)"].astype(str)

    return out


def run_scoring_from_grd(df_grd: pd.DataFrame, threshold: float | None = None):
    """
    Construye features desde el GRD y ejecuta scoring con el modelo guardado.
    Devuelve un DataFrame con pred_proba y pred_clase.
    """
    features_raw = build_features_from_grd(df_grd)

    # Validación de columnas vs metadata
    preproc = load_preprocessing()
    feature_cols = preproc.get("feature_columns", [])
    missing = [c for c in feature_cols if c not in features_raw.columns]
    extra = [c for c in features_raw.columns if c not in feature_cols]

    print(f"✅ Validación columnas: faltan={missing}, extra={extra}")
    print("🔍 Ejemplo de fila de entrada:", features_raw.head(1).to_dict(orient="records"))

    # Aplicar encoders guardados (categóricas -> numéricas)
    features = _apply_encoders(features_raw, preproc)

    scored = score_dataframe(features, threshold=threshold)
    return scored


def persist_scores_to_episodios(df_grd: pd.DataFrame, threshold: float | None = None) -> int:
    """
    Ejecuta scoring desde el GRD y actualiza Episodio.prediccion_extension.
    Devuelve la cantidad de episodios actualizados.
    """
    episodio_variants = [
        "Episodio CMBD",
        "CÓDIGO EPISODIO CMBD",
        "episodio_cmbd",
        "Episodio",
        "EPISODIO",
    ]
    epi_col = next((c for c in episodio_variants if c in df_grd.columns), None)
    if not epi_col:
        raise ValueError("Falta columna de episodio en excel1 para mapear episodios.")
    df_grd = df_grd.rename(columns={epi_col: "episodio_cmbd"})

    print("🔮 Calculando predicción de extensión...")

    scored = run_scoring_from_grd(df_grd, threshold=threshold)
    episodio_ids = df_grd["episodio_cmbd"].astype(str).tolist()

    preds = dict(zip(episodio_ids, scored["pred_clase"].tolist()))
    probas = dict(zip(episodio_ids, scored["pred_proba"].tolist()))

    episodios = Episodio.objects.filter(episodio_cmbd__in=episodio_ids)
    updated = 0
    positivos = []
    for ep in episodios:
        key = str(ep.episodio_cmbd)
        if key in preds:
            ep.prediccion_extension = int(preds[key])
            proba = probas.get(key, None)
            print(f"   → Episodio {key}: pred={ep.prediccion_extension}, proba={proba}")
            if ep.prediccion_extension == 1:
                positivos.append((key, proba))
            updated += 1
    if updated:
        Episodio.objects.bulk_update(episodios, ["prediccion_extension"])
        print(f"✅ Predicción de extensión actualizada para {updated} episodios")
        if positivos:
            print("⚠️  Episodios con prediccion_extension=1:")
            for key, proba in positivos:
                print(f"   • Episodio {key}: proba={proba}")
        else:
            print("ℹ️  No hay episodios con prediccion_extension=1 en esta corrida.")
    return updated


__all__ = ["build_features_from_grd", "run_scoring_from_grd", "persist_scores_to_episodios"]