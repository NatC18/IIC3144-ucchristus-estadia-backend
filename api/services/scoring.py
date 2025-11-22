"""
Servicio de scoring: carga modelo/metadata y ejecuta inferencia sobre un DataFrame.
Pensado para llamarse tras la importación de los Excel.
"""

from pathlib import Path
import pickle
import joblib
import pandas as pd

# Ruta base donde se guardan los pickles del modelo.
_MODELS_DIR = Path(__file__).resolve().parent.parent / "modelo"


def load_model(model_name: str = "modelo.pkl"):
    """Carga y devuelve el modelo entrenado."""
    model_path = _MODELS_DIR / model_name
    if not model_path.exists():
        raise FileNotFoundError(f"No se encontró el modelo en {model_path}")
    return joblib.load(model_path)


def load_preprocessing(preproc_name: str = "preprocessing.pkl"):
    """Carga y devuelve el metadata de preprocesamiento."""
    preproc_path = _MODELS_DIR / preproc_name
    if not preproc_path.exists():
        raise FileNotFoundError(f"No se encontró el preprocesamiento en {preproc_path}")
    with open(preproc_path, "rb") as f:
        return pickle.load(f)


def score_dataframe(
    df: pd.DataFrame,
    threshold: float | None = None,
    model_name: str = "modelo.pkl",
    preproc_name: str = "preprocessing.pkl",
):
    """
    Ejecuta inferencia sobre un DataFrame ya preprocesado.
    - Requiere que df tenga todas las columnas en feature_columns.
    - threshold: si no se pasa, se usa el del metadata (o 0.5 por defecto).
    - Devuelve df con columnas adicionales: pred_proba y pred_clase.
    """
    preproc = load_preprocessing(preproc_name)
    feature_cols = preproc.get("feature_columns")
    if not feature_cols:
        raise ValueError("feature_columns no está presente en el preprocessing.")

    missing = [c for c in feature_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Faltan columnas para el modelo: {missing}")

    th = threshold if threshold is not None else preproc.get("threshold", 0.5)

    X = df[feature_cols]
    model = load_model(model_name)
    proba = model.predict_proba(X)[:, 1]
    pred = (proba >= th).astype(int)

    result = df.copy()
    result["pred_proba"] = proba
    result["pred_clase"] = pred
    result.attrs["threshold"] = th
    return result


__all__ = ["load_model", "load_preprocessing", "score_dataframe"]
