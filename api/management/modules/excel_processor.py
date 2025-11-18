"""
Procesador para leer y combinar archivos Excel con pandas
"""

import logging
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

logger = logging.getLogger(__name__)


class ExcelProcessor:
    """
    Procesador para leer archivos Excel y combinar datos por episodio_cmbd
    Compatible con archivos de OneDrive y locales
    """

    def __init__(self):
        self.excel1_df = None
        self.excel2_df = None
        self.excel3_df = None
        self.excel4_df = None
        self.combined_df = None

    def load_excel_files(self, file_paths: Dict[str, Path]) -> bool:
        """
        Carga los cuatro archivos Excel en DataFrames

        Args:
            file_paths: Dict con nombres de archivo -> rutas locales

        Returns:
            bool: True si todos los archivos se cargaron correctamente
        """
        try:
            # Definir archivos esperados
            expected_files = ["excel1", "excel2", "excel3", "excel4"]

            # Verificar que tenemos todos los archivos
            missing_files = [f for f in expected_files if f not in file_paths]
            if missing_files:
                logger.error(f"Faltan archivos: {missing_files}")
                return False

            # Cargar cada archivo
            logger.info("Cargando archivos Excel...")

            # Excel 1
            self.excel1_df = self._load_single_excel(file_paths["excel1"], "excel1")
            if self.excel1_df is None:
                return False

            # Excel 2
            self.excel2_df = self._load_single_excel(file_paths["excel2"], "excel2")
            if self.excel2_df is None:
                return False

            # Excel 3
            self.excel3_df = self._load_single_excel(file_paths["excel3"], "excel3")
            if self.excel3_df is None:
                return False
            
            # Excel 4
            self.excel4_df = self._load_single_excel(file_paths["excel4"], "excel4")
            if self.excel4_df is None:
                return False

            logger.info("Todos los archivos Excel cargados exitosamente")
            return True

        except Exception as e:
            logger.error(f"Error cargando archivos Excel: {str(e)}")
            return False

    def _load_single_excel(
        self, file_path: Path, file_name: str
    ) -> Optional[pd.DataFrame]:
        """
        Carga un archivo Excel individual

        Args:
            file_path: Ruta al archivo
            file_name: Nombre para logging

        Returns:
            DataFrame o None si hay error
        """
        try:
            # Intentar cargar con openpyxl primero
            try:
                df = pd.read_excel(file_path, engine="openpyxl")
            except:
                # Intentar con xlrd como fallback
                df = pd.read_excel(file_path, engine="xlrd")

            # NO limpiar nombres de columnas - mantener originales para mapeo específico
            df.columns = df.columns.str.strip()

            # Buscar columna de episodio en cada archivo según su estructura
            episodio_col = None
            if file_name == "excel1":
                # En Excel 1, buscar columnas que contengan 'episodio'
                possible_cols = [col for col in df.columns if "episodio" in col.lower()]
                episodio_col = possible_cols[0] if possible_cols else None
            elif file_name == "excel2":
                # En Excel 2, buscar 'Episodio:'
                if "Episodio:" in df.columns:
                    episodio_col = "Episodio:"
            elif file_name == "excel3":
                # En Excel 3, buscar columnas que contengan 'episodio'
                possible_cols = [col for col in df.columns if "episodio" in col.lower()]
                episodio_col = possible_cols[0] if possible_cols else None

            elif file_name == "excel4":
                
                if "CÓDIGO EPISODIO CMBD" in df.columns:
                    episodio_col = "CÓDIGO EPISODIO CMBD"
                else:
                    
                    for c in df.columns:
                        if "episodio" in c.lower():
                            episodio_col = c
                            break

            if episodio_col:
                logger.info(
                    f"Encontrada columna de episodio '{episodio_col}' en {file_name}"
                )
                # Crear columna estándar para el cruce
                df["episodio_cmbd"] = df[episodio_col]
            else:
                logger.warning(f"No se encontró columna de episodio en {file_name}")
                # Buscar cualquier columna que contenga 'episodio'
                possible_cols = [col for col in df.columns if "episodio" in col.lower()]
                if possible_cols:
                    logger.info(
                        f"Usando columna {possible_cols[0]} como episodio_cmbd en {file_name}"
                    )
                    df["episodio_cmbd"] = df[possible_cols[0]]
                else:
                    logger.error(
                        f"{file_name} no tiene columna de episodio identificable"
                    )
                    return None

            # Limpiar valores nulos en episodio_cmbd
            initial_count = len(df)
            df = df.dropna(subset=["episodio_cmbd"])
            final_count = len(df)

            if initial_count != final_count:
                logger.warning(
                    f"{file_name}: Eliminadas {initial_count - final_count} filas sin episodio_cmbd"
                )

            # Convertir episodio_cmbd a string para asegurar consistencia
            df["episodio_cmbd"] = df["episodio_cmbd"].astype(str)

            logger.info(
                f"{file_name} cargado: {len(df)} filas, {len(df.columns)} columnas"
            )
            return df

        except Exception as e:
            logger.error(f"Error cargando {file_name}: {str(e)}")
            return None

    def combine_data(self) -> bool:
        """
        Combina datos de los cuatro archivos Excel usando episodio_cmbd como clave
        Con mapeos específicos para cada modelo

        Returns:
            bool: True si la combinación fue exitosa
        """
        try:
            if not all(
                [
                    self.excel1_df is not None,
                    self.excel2_df is not None,
                    self.excel3_df is not None,
                    self.excel4_df is not None,
                ]
            ):
                logger.error("No todos los archivos están cargados")
                return False

            logger.info("Iniciando combinación de datos con mapeos específicos...")

            # Limpiar y normalizar episodios en cada archivo
            excel1_clean = self._clean_episodio_data(self.excel1_df.copy(), "excel1")
            excel2_clean = self._clean_episodio_data(self.excel2_df.copy(), "excel2")
            excel3_clean = self._clean_episodio_data(self.excel3_df.copy(), "excel3")
            excel4_clean = self._clean_episodio_data(self.excel4_df.copy(), "excel4")

            # Verificar que todos tengan la columna episodio_cmbd
            if not all(
                "episodio_cmbd" in df.columns
                for df in [excel1_clean, excel2_clean, excel3_clean, excel4_clean]
            ):
                logger.error(
                    "No se pudo encontrar columna de episodio en todos los archivos"
                )
                return False

            # Combinar datos por episodio
            # Usar excel2 como base ya que tiene datos principales de gestión
            combined = excel2_clean.copy()

            # Agregar datos de excel1 (estadísticas del episodio)
            excel1_cols = ["episodio_cmbd"]
            # Buscar columnas específicas que pueden tener nombres ligeramente diferentes
            possible_excel1_cols = {
                "Tipo Actividad": [
                    "Tipo Actividad",
                    "tipo_actividad",
                    "Tipo de Actividad",
                ],
                "Estancia Inlier / Outlier": [
                    "Estancia Inlier / Outlier",
                    "estancia_inlier_outlier",
                    "Inlier/Outlier",
                ],
                "Especialidad médica de la intervención (des)": [
                    "Especialidad médica de la intervención (des)",
                    "especialidad_medica",
                    "Especialidad",
                ],
                "Estancias Prequirurgicas Int  -Episodio-": [
                    "Estancias Prequirurgicas Int  -Episodio-",
                    "estancia_prequirurgica",
                    "Prequirurgica",
                ],
                "Estancias Postquirurgicas Int  -Episodio-": [
                    "Estancias Postquirurgicas Int  -Episodio-",
                    "estancia_postquirurgica",
                    "Postquirurgica",
                ],
                "Estancia Norma GRD": [
                    "Estancia Norma GRD",
                    "estancia_norma_grd",
                    "Norma GRD",
                ],
            }

            for target_col, possible_names in possible_excel1_cols.items():
                for possible_name in possible_names:
                    if possible_name in excel1_clean.columns:
                        excel1_cols.append(possible_name)
                        break

            excel1_mapped = excel1_clean[excel1_cols].copy()
            combined = pd.merge(
                combined,
                excel1_mapped,
                on="episodio_cmbd",
                how="left",
                suffixes=("", "_excel1"),
            )

            # Agregar datos de excel3 (información de camas)
            excel3_cols = ["episodio_cmbd"]
            if "CAMA" in excel3_clean.columns:
                excel3_cols.append("CAMA")

            if "HABITACION" in excel3_clean.columns:
                excel3_cols.append("HABITACION")

            excel3_mapped = excel3_clean[excel3_cols].copy()
            combined = pd.merge(
                combined,
                excel3_mapped,
                on="episodio_cmbd",
                how="left",
                suffixes=("", "_excel3"),
            )

            # Agregar datos de excel4 (información de score social)
            excel4_cols = ["episodio_cmbd"]

            if "Puntaje" in excel4_clean.columns:
                excel4_cols.append("Puntaje")

            excel4_mapped = excel4_clean[excel4_cols].copy()
            combined = pd.merge(
                combined,
                excel4_mapped,
                on="episodio_cmbd",
                how="left",
                suffixes=("", "_excel4"),
            )

            self.combined_df = combined

            # Estadísticas de combinación
            total_episodios = len(combined)
            episodios_con_excel1 = len(
                combined.dropna(
                    subset=[col for col in combined.columns if col.endswith("_excel1")]
                )
            )
            episodios_con_excel3 = len(
                combined.dropna(
                    subset=[col for col in combined.columns if col.endswith("_excel3")]
                )
            )
            episodios_con_excel4 = len(
                combined.dropna(
                    subset=[col for col in combined.columns if col.endswith("_excel4")]
                )
            )

            logger.info(f"Combinación completada:")
            logger.info(f"  - Total episodios: {total_episodios}")
            logger.info(f"  - Con datos de excel1: {episodios_con_excel1}")
            logger.info(f"  - Con datos de excel3: {episodios_con_excel3}")
            logger.info(f"  - Con datos de excel4: {episodios_con_excel4}")

            return True

        except Exception as e:
            logger.error(f"Error combinando datos: {str(e)}")
            return False

    def _clean_episodio_data(self, df: pd.DataFrame, source: str) -> pd.DataFrame:
        """
        Limpia y normaliza los datos de episodio

        Args:
            df: DataFrame a limpiar
            source: Fuente del archivo

        Returns:
            DataFrame limpio con episodio_cmbd normalizado
        """
        # Ya debería tener episodio_cmbd desde _load_single_excel
        if "episodio_cmbd" not in df.columns:
            logger.error(f"No se encontró columna episodio_cmbd en {source}")
            return df

        # Limpiar valores de episodio
        df["episodio_cmbd"] = df["episodio_cmbd"].astype(str).str.strip()

        # Remover filas con episodios vacíos
        original_count = len(df)
        df = df[df["episodio_cmbd"].notna()]
        df = df[df["episodio_cmbd"] != "nan"]
        df = df[df["episodio_cmbd"] != ""]
        df = df[df["episodio_cmbd"] != "None"]

        clean_count = len(df)
        logger.info(f"Limpieza {source}: {original_count} -> {clean_count} registros")

        return df

    def _normalize_episodio_column(self, df: pd.DataFrame, source: str) -> pd.DataFrame:
        """
        Normaliza la columna de episodio CMBD a 'episodio_cmbd'

        Args:
            df: DataFrame a normalizar
            source: Fuente del archivo (para logging)

        Returns:
            DataFrame con columna episodio_cmbd normalizada
        """
        # Posibles nombres de columna para episodio
        episodio_variants = [
            "Episodio CMBD",
            "episodio_cmbd",
            "Episodio:",
            "episodio:",
            "EPISODIO",
            "episodio",
            "Episodio",
            "cmbd",
            "CMBD",
            "Episodio / Estadía",
        ]

        episodio_col = None
        for variant in episodio_variants:
            if variant in df.columns:
                episodio_col = variant
                break

        if episodio_col is None:
            logger.error(f"No se encontró columna de episodio en {source}")
            logger.info(f"Columnas disponibles en {source}: {list(df.columns)}")
            return df

        # Renombrar la columna a episodio_cmbd si no lo es ya
        if episodio_col != "episodio_cmbd":
            df = df.rename(columns={episodio_col: "episodio_cmbd"})
            logger.info(f"Renombrado '{episodio_col}' -> 'episodio_cmbd' en {source}")

        # Limpiar valores de episodio (remover espacios, convertir a string)
        df["episodio_cmbd"] = df["episodio_cmbd"].astype(str).str.strip()

        # Remover filas con episodios vacíos o 'nan'
        df = df[df["episodio_cmbd"].notna()]
        df = df[df["episodio_cmbd"] != "nan"]
        df = df[df["episodio_cmbd"] != ""]

        logger.info(f"Normalizado {source}: {len(df)} registros con episodios válidos")
        return df

    def _rename_columns_with_suffix(
        self, df: pd.DataFrame, suffix: str
    ) -> pd.DataFrame:
        """
        Renombra columnas agregando sufijo, excepto episodio_cmbd

        Args:
            df: DataFrame a renombrar
            suffix: Sufijo a agregar

        Returns:
            DataFrame con columnas renombradas
        """
        df_copy = df.copy()

        # Crear diccionario de renombrado
        rename_dict = {}
        for col in df_copy.columns:
            # No renombrar la columna de episodio que es la clave de unión
            if col != "episodio_cmbd":
                rename_dict[col] = f"{col}{suffix}"

        return df_copy.rename(columns=rename_dict)

    def get_combined_data(self) -> Optional[pd.DataFrame]:
        """
        Retorna los datos combinados

        Returns:
            DataFrame combinado o None si no está disponible
        """
        return self.combined_df

    def get_data_summary(self) -> Dict:
        """
        Genera resumen de los datos cargados y combinados

        Returns:
            Dict con estadísticas de los datos
        """
        summary = {
            "files_loaded": {
                "excel1": self.excel1_df is not None,
                "excel2": self.excel2_df is not None,
                "excel3": self.excel3_df is not None,
                "excel4": self.excel4_df is not None,
            },
            "row_counts": {},
            "column_counts": {},
            "combined_stats": {},
        }

        # Estadísticas individuales
        for name, df in [
            ("excel1", self.excel1_df),
            ("excel2", self.excel2_df),
            ("excel3", self.excel3_df),
            ("excel4", self.excel4_df),
        ]:
            if df is not None:
                summary["row_counts"][name] = len(df)
                summary["column_counts"][name] = len(df.columns)

        # Estadísticas combinadas
        if self.combined_df is not None:
            summary["combined_stats"] = {
                "total_rows": len(self.combined_df),
                "total_columns": len(self.combined_df.columns),
                "unique_episodios": self.combined_df["episodio_cmbd"].nunique(),
            }

        return summary

    def export_combined_data(self, output_path: Path) -> bool:
        """
        Exporta datos combinados a Excel para revisión

        Args:
            output_path: Ruta donde guardar el archivo

        Returns:
            bool: True si se exportó correctamente
        """
        try:
            if self.combined_df is None:
                logger.error("No hay datos combinados para exportar")
                return False

            self.combined_df.to_excel(output_path, index=False)
            logger.info(f"Datos combinados exportados a: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Error exportando datos: {str(e)}")
            return False

    def clean_data_for_models(self) -> Dict[str, pd.DataFrame]:
        """
        Limpia y prepara datos para inserción en modelos Django

        Returns:
            Dict con DataFrames listos para cada modelo
        """
        if self.combined_df is None:
            logger.error("No hay datos combinados disponibles")
            return {}

        try:
            logger.info("Preparando datos para modelos Django...")

            # Datos para Pacientes
            pacientes_df = self._prepare_pacientes_data()

            # Datos para Episodios
            episodios_df = self._prepare_episodios_data()

            # Datos para Gestiones
            gestiones_df = self._prepare_gestiones_data()

            return {
                "pacientes": pacientes_df,
                "episodios": episodios_df,
                "gestiones": gestiones_df,
            }

        except Exception as e:
            logger.error(f"Error preparando datos para modelos: {str(e)}")
            return {}

    def _prepare_pacientes_data(self) -> pd.DataFrame:
        """Prepara datos para el modelo Paciente extrayendo del DataFrame combinado"""

        if self.combined_df is None or len(self.combined_df) == 0:
            logger.warning("No hay datos combinados para procesar pacientes")
            return pd.DataFrame()

        pacientes_data = []

        # Iterar por cada fila del DataFrame combinado
        for idx, row in self.combined_df.iterrows():
            episodio_cmbd = row.get("episodio_cmbd")

            if pd.isna(episodio_cmbd) or str(episodio_cmbd).strip() == "":
                continue

            # Extraer datos del paciente de diferentes columnas
            rut = self._extract_rut(row)
            nombre = self._extract_nombre(row)

            # Solo agregar si tenemos al menos RUT o nombre
            if rut or nombre:
                paciente_data = {
                    "episodio_cmbd": str(episodio_cmbd).strip(),
                    "rut": rut,
                    "nombre": nombre,
                    "sexo": self._extract_sexo(row),
                    "edad": self._extract_edad(row),
                    "fecha_nacimiento": self._extract_fecha_nacimiento(row),
                    "prevision": self._extract_prevision(row),
                    "score_social": self._extract_puntaje(row)
                }
                pacientes_data.append(paciente_data)

        if not pacientes_data:
            logger.warning("No se encontraron datos de pacientes válidos")
            return pd.DataFrame()

        # Convertir a DataFrame y eliminar duplicados por episodio
        pacientes_df = pd.DataFrame(pacientes_data)
        pacientes_df = pacientes_df.drop_duplicates(
            subset=["episodio_cmbd"], keep="first"
        )

        logger.info(f"Datos de pacientes preparados: {len(pacientes_df)} registros")
        return pacientes_df

    def _extract_rut(self, row) -> str:
        """Extrae RUT de diferentes columnas posibles, incluyendo columnas con sufijos"""
        rut_columns = [
            "RUT",
            "rut",
            "RUT_PACIENTE",
            "rut_paciente",
            "RUT_excel2",
            "rut_excel2",
            "RUT_PACIENTE_excel3",
            "rut_paciente_excel3",
        ]
        for col in rut_columns:
            if col in row and not pd.isna(row[col]) and str(row[col]).strip() != "":
                rut_val = str(row[col]).strip()
                if rut_val.lower() != "nan":
                    return rut_val
        return ""

    def _extract_nombre(self, row) -> str:
        """Extrae nombre completo de diferentes columnas posibles, incluyendo columnas con sufijos"""
        nombre_columns = [
            "Nombre",
            "nombre",
            "NOMBRE_PACIENTE",
            "nombre_paciente",
            "Nombre_excel2",
            "nombre_excel2",
            "NOMBRE_PACIENTE_excel3",
            "nombre_paciente_excel3",
        ]
        for col in nombre_columns:
            if col in row and not pd.isna(row[col]) and str(row[col]).strip() != "":
                nombre_val = str(row[col]).strip()
                if nombre_val.lower() != "nan":
                    return nombre_val
        return ""

    def _extract_sexo(self, row) -> str:
        """Extrae sexo de diferentes columnas posibles, incluyendo columnas con sufijos"""
        sexo_columns = [
            "Sexo  (Desc)",
            "sexo",
            "Sexo",
            "sexo_desc",
            "Sexo  (Desc)_excel2",
            "sexo_excel2",
            "Sexo_excel3",
        ]
        for col in sexo_columns:
            if col in row and not pd.isna(row[col]) and str(row[col]).strip() != "":
                sexo_val = str(row[col]).strip().upper()
                if sexo_val.lower() != "nan":
                    if sexo_val in ["MASCULINO", "M", "HOMBRE"]:
                        return "M"
                    elif sexo_val in ["FEMENINO", "F", "MUJER"]:
                        return "F"
        return ""

    def _extract_edad(self, row) -> int:
        """Extrae edad de diferentes columnas posibles, incluyendo columnas con sufijos"""
        edad_columns = [
            "Edad en años",
            "edad",
            "Edad",
            "edad_anos",
            "Edad en años_excel2",
            "edad_excel2",
            "Edad_excel3",
        ]
        for col in edad_columns:
            if col in row and not pd.isna(row[col]) and str(row[col]).strip() != "":
                try:
                    edad_val = str(row[col]).strip()
                    if edad_val.lower() != "nan":
                        return int(float(edad_val))
                except (ValueError, TypeError):
                    continue
        return 0

    def _extract_prevision(self, row) -> str:
        """Extrae previsión de diferentes columnas posibles, incluyendo columnas con sufijos"""
        prevision_columns = [
            "Prevision (Desc)",
            "prevision",
            "Convenio",
            "Nombre de la aseguradora",
            "Prevision (Desc)_excel2",
            "prevision_excel2",
            "Convenio_excel2",
            "Nombre de la aseguradora_excel2",
        ]
        for col in prevision_columns:
            if col in row and not pd.isna(row[col]) and str(row[col]).strip() != "":
                prev_val = str(row[col]).strip()
                if prev_val.lower() != "nan":
                    return prev_val
        return ""

    def _extract_fecha_nacimiento(self, row) -> str:
        """Extrae fecha de nacimiento de diferentes columnas posibles, principalmente del excel2"""
        fecha_nacimiento_columns = [
            "Fecha de Nacimiento",
            "fecha_nacimiento",
            "fecha_nac",
            "Fecha de Nacimiento_excel2",
            "fecha_nacimiento_excel2",
        ]
        for col in fecha_nacimiento_columns:
            if col in row and not pd.isna(row[col]) and str(row[col]).strip() != "":
                fecha_val = str(row[col]).strip()
                if fecha_val.lower() not in ["nan", "", "null"]:
                    try:
                        # Intentar parsear diferentes formatos de fecha
                        from datetime import datetime

                        # Intentar formato YYYY-MM-DD
                        if len(fecha_val) >= 10:
                            parsed_date = datetime.strptime(fecha_val[:10], "%Y-%m-%d")
                            return parsed_date.strftime("%Y-%m-%d")
                    except ValueError:
                        try:
                            # Intentar formato DD/MM/YYYY
                            parsed_date = datetime.strptime(fecha_val, "%m/%d/%Y")
                            return parsed_date.strftime("%Y-%m-%d")
                        except ValueError:
                            continue
        return ""
    
    def _extract_puntaje(self, row) -> float:
        """Extrae puntaje de diferentes columnas posibles, incluyendo columnas con sufijos"""
        puntaje_columns = [
            "Puntaje",
            "puntaje",
            "Score Social",
            "score_social",
            "Puntaje_excel4",
            "puntaje_excel4",
        ]
        for col in puntaje_columns:
            if col in row and not pd.isna(row[col]) and str(row[col]).strip() != "":
                try:
                    puntaje_val = str(row[col]).strip()
                    if puntaje_val.lower() != "nan":
                        return float(puntaje_val)
                except (ValueError, TypeError):
                    continue
        return 0.0

    def _prepare_episodios_data(self) -> pd.DataFrame:
        """Prepara datos para el modelo Episodio extrayendo del DataFrame combinado"""

        if self.combined_df is None or len(self.combined_df) == 0:
            logger.warning("No hay datos combinados para procesar episodios")
            return pd.DataFrame()

        episodios_data = []

        # Iterar por cada fila del DataFrame combinado
        for idx, row in self.combined_df.iterrows():
            episodio_cmbd = row.get("episodio_cmbd")

            if pd.isna(episodio_cmbd) or str(episodio_cmbd).strip() == "":
                continue

            # Extraer datos del episodio de diferentes columnas
            episodio_data = {
                "episodio_cmbd": str(episodio_cmbd).strip(),
                "fecha_ingreso": self._extract_fecha_ingreso(row),
                "fecha_alta": self._extract_fecha_alta(row),
                "servicio": self._extract_servicio(row),
                "cama": self._extract_cama(row),
                "diagnostico_principal": self._extract_diagnostico(row),
                "tipo_actividad": self._extract_tipo_actividad(row),
                "estado": self._extract_estado_episodio(row),
                "estancia_dias": self._extract_estancia(row),
            }

            episodios_data.append(episodio_data)

        if not episodios_data:
            logger.warning("No se encontraron datos de episodios")
            return pd.DataFrame()

        # Convertir a DataFrame y eliminar duplicados por episodio
        episodios_df = pd.DataFrame(episodios_data)
        episodios_df = episodios_df.drop_duplicates(
            subset=["episodio_cmbd"], keep="first"
        )

        logger.info(f"Datos de episodios preparados: {len(episodios_df)} registros")
        return episodios_df

    def _extract_fecha_ingreso(self, row) -> str:
        """Extrae fecha de ingreso de diferentes columnas posibles, incluyendo columnas con sufijos"""
        fecha_columns = [
            "fecha ingreso completa",
            "fecha_ingreso",
            "fecha admisión",
            "fecha_admision",
            "fecha inicio:",
            "fecha admisión_excel2",
            "fecha_admision_excel2",
            "fecha inicio:_excel2",
            "fecha_admision_excel3",
            "fecha_carga_excel3",
        ]
        for col in fecha_columns:
            if col in row and not pd.isna(row[col]) and str(row[col]).strip() != "":
                fecha_str = str(row[col]).strip()
                if fecha_str.lower() != "nan":
                    try:
                        if " " in fecha_str:  # Tiene hora
                            fecha_dt = pd.to_datetime(fecha_str)
                        else:  # Solo fecha
                            fecha_dt = pd.to_datetime(fecha_str)
                        return fecha_dt.strftime("%Y-%m-%d")
                    except:
                        continue
        return ""

    def _extract_fecha_alta(self, row) -> str:
        """Extrae fecha de alta de diferentes columnas posibles, incluyendo columnas con sufijos"""
        fecha_columns = [
            "fecha completa",
            "fecha_alta",
            "fecha alta",
            "fecha_egreso",
            "fecha alta_excel2",
            "fecha_alta_excel2",
            "fecha_egreso_excel2",
        ]
        for col in fecha_columns:
            if col in row and not pd.isna(row[col]) and str(row[col]).strip() != "":
                fecha_str = str(row[col]).strip()
                if fecha_str.lower() != "nan":
                    try:
                        if " " in fecha_str:  # Tiene hora
                            fecha_dt = pd.to_datetime(fecha_str)
                        else:  # Solo fecha
                            fecha_dt = pd.to_datetime(fecha_str)
                        return fecha_dt.strftime("%Y-%m-%d")
                    except:
                        continue
        return ""

    def _extract_servicio(self, row) -> str:
        """Extrae servicio de diferentes columnas posibles, incluyendo columnas con sufijos"""
        servicio_columns = [
            "servicio ingreso (descripción)",
            "servicio",
            "servicio (especialidad)",
            "especialidad",
            "servicio ingreso (descripción)_excel2",
            "servicio (especialidad)_excel2",
        ]
        for col in servicio_columns:
            if col in row and not pd.isna(row[col]) and str(row[col]).strip() != "":
                serv_val = str(row[col]).strip()
                if serv_val.lower() != "nan":
                    return serv_val
        return ""

    def _extract_cama(self, row) -> str:
        """Extrae cama de diferentes columnas posibles, incluyendo columnas con sufijos"""
        cama_columns = ["cama", "cama_codigo", "cama_excel2", "cama_excel3"]
        for col in cama_columns:
            if col in row and not pd.isna(row[col]) and str(row[col]).strip() != "":
                cama_val = str(row[col]).strip()
                if cama_val.lower() != "nan":
                    return cama_val
        return ""

    def _extract_diagnostico(self, row) -> str:
        """Extrae diagnóstico principal de diferentes columnas posibles"""
        diag_columns = [
            "Diagnóstico   Principal",
            "diagnostico_principal",
            "Texto libre diagnóstico admisión",
        ]
        for col in diag_columns:
            if col in row and not pd.isna(row[col]):
                return str(row[col]).strip()
        return ""

    def _extract_tipo_actividad(self, row) -> str:
        """Extrae tipo de actividad de diferentes columnas posibles"""
        tipo_columns = ["Tipo Actividad", "tipo_actividad", "CATEGORIA_TRATAMIENTO"]
        for col in tipo_columns:
            if col in row and not pd.isna(row[col]):
                return str(row[col]).strip()
        return ""

    def _extract_estado_episodio(self, row) -> str:
        """Extrae estado del episodio de diferentes columnas posibles"""
        estado_columns = ["Estado", "estado", "Status", "estado_episodio"]
        for col in estado_columns:
            if col in row and not pd.isna(row[col]):
                return str(row[col]).strip()
        return ""

    def _extract_estancia(self, row) -> int:
        """Extrae días de estancia de diferentes columnas posibles"""
        estancia_columns = [
            "Estancia del Episodio",
            "estancia_dias",
            "Días Hospitalización",
            "dias_estancia",
        ]
        for col in estancia_columns:
            if col in row and not pd.isna(row[col]):
                try:
                    return int(float(row[col]))
                except (ValueError, TypeError):
                    continue
        return 0

    def _prepare_gestiones_data(self) -> pd.DataFrame:
        """Prepara datos para el modelo Gestion extrayendo del DataFrame combinado"""

        if self.combined_df is None or len(self.combined_df) == 0:
            logger.warning("No hay datos combinados para procesar gestiones")
            return pd.DataFrame()

        gestiones_data = []

        # Iterar por cada fila del DataFrame combinado
        for idx, row in self.combined_df.iterrows():
            episodio_cmbd = row.get("episodio_cmbd")

            if pd.isna(episodio_cmbd) or str(episodio_cmbd).strip() == "":
                continue

            # Extraer datos de gestión de diferentes columnas
            tipo_gestion = self._extract_tipo_gestion(row)
            estado_gestion = self._extract_estado_gestion(row)
            valor_gestion = self._extract_valor_gestion(row)

            # Solo agregar si hay información de gestión relevante
            if tipo_gestion or estado_gestion or valor_gestion > 0:
                gestion_data = {
                    "episodio_cmbd": str(episodio_cmbd).strip(),
                    "tipo_gestion": tipo_gestion,
                    "estado_gestion": estado_gestion,
                    "fecha_inicio": self._extract_fecha_inicio_gestion(row),
                    "fecha_fin": self._extract_fecha_fin_gestion(row),
                    "valor_gestion": valor_gestion,
                    "observaciones": self._extract_observaciones_gestion(row),
                    "usuario_responsable": self._extract_usuario_responsable(row),
                }
                gestiones_data.append(gestion_data)

        if not gestiones_data:
            logger.warning("No se encontraron datos de gestiones")
            return pd.DataFrame()

        # Convertir a DataFrame
        gestiones_df = pd.DataFrame(gestiones_data)

        logger.info(f"Datos de gestiones preparados: {len(gestiones_df)} registros")
        return gestiones_df

    def _extract_tipo_gestion(self, row) -> str:
        """Extrae tipo de gestión de diferentes columnas posibles"""
        tipo_columns = [
            "¿Qué gestión se solicito?",
            "tipo_gestion",
            "Tipo de Solicitud",
            "TIPO_MOVIMIENTO",
        ]
        for col in tipo_columns:
            if col in row and not pd.isna(row[col]):
                return str(row[col]).strip()
        return ""

    def _extract_estado_gestion(self, row) -> str:
        """Extrae estado de gestión de diferentes columnas posibles"""
        estado_columns = ["Status", "Estado", "estado_gestion", "concretado"]
        for col in estado_columns:
            if col in row and not pd.isna(row[col]):
                return str(row[col]).strip()
        return ""

    def _extract_fecha_inicio_gestion(self, row) -> str:
        """Extrae fecha de inicio de gestión de diferentes columnas posibles"""
        fecha_columns = [
            "Fecha Inicio:",
            "fecha_inicio_gestion",
            "Fecha admisión",
            "FECHA_CARGA",
        ]
        for col in fecha_columns:
            if col in row and not pd.isna(row[col]):
                fecha_str = str(row[col]).strip()
                try:
                    if " " in fecha_str:  # Tiene hora
                        fecha_dt = pd.to_datetime(fecha_str)
                    else:  # Solo fecha
                        fecha_dt = pd.to_datetime(fecha_str)
                    return fecha_dt.strftime("%Y-%m-%d")
                except:
                    continue
        return ""

    def _extract_fecha_fin_gestion(self, row) -> str:
        """Extrae fecha de fin de gestión de diferentes columnas posibles"""
        fecha_columns = [
            "Fecha de Finalización",
            "fecha_fin_gestion",
            "Última Modificación",
        ]
        for col in fecha_columns:
            if col in row and not pd.isna(row[col]):
                fecha_str = str(row[col]).strip()
                try:
                    if " " in fecha_str:  # Tiene hora
                        fecha_dt = pd.to_datetime(fecha_str)
                    else:  # Solo fecha
                        fecha_dt = pd.to_datetime(fecha_str)
                    return fecha_dt.strftime("%Y-%m-%d")
                except:
                    continue
        return ""

    def _extract_valor_gestion(self, row) -> float:
        """Extrae valor monetario de gestión de diferentes columnas posibles"""
        valor_columns = [" Valor parcial ", "valor_gestion", "monto_total", "valor"]
        for col in valor_columns:
            if col in row and not pd.isna(row[col]):
                try:
                    # Limpiar el valor (quitar símbolos de moneda, comas, etc.)
                    valor_str = str(row[col]).strip()
                    valor_str = (
                        valor_str.replace("$", "").replace(",", "").replace(".", "")
                    )
                    return float(valor_str)
                except (ValueError, TypeError):
                    continue
        return 0.0

    def _extract_observaciones_gestion(self, row) -> str:
        """Extrae observaciones de gestión de diferentes columnas posibles"""
        obs_columns = [
            "Informe",
            "observaciones",
            "Motivo de Cancelación",
            "Causa Devolución/Rechazo",
        ]
        for col in obs_columns:
            if col in row and not pd.isna(row[col]):
                obs_val = str(row[col]).strip()
                if obs_val and obs_val.lower() != "nan":
                    return obs_val
        return ""

    def _extract_usuario_responsable(self, row) -> str:
        """Extrae usuario responsable de diferentes columnas posibles"""
        usuario_columns = ["MEDICO_TRATANTE", "medico_responsable", "DESC_ENFERMERIA"]
        for col in usuario_columns:
            if col in row and not pd.isna(row[col]):
                return str(row[col]).strip()
        return ""

    def process_local_files(
        self, file_paths: Dict[str, str]
    ) -> Dict[str, pd.DataFrame]:
        """
        Procesa archivos Excel desde el sistema de archivos local

        Args:
            file_paths: Dict con nombres de archivo -> rutas locales
            Ejemplo: {'excel1': '/path/to/excel1.xlsx', 'excel2': '/path/to/excel2.xlsx', 'excel3': '/path/to/excel3.xlsx', 'excel4': '/path/to/excel4.xlsx'}

        Returns:
            Dict[str, pd.DataFrame]: DataFrames individuales para el DataMapper
        """
        logger.info("Iniciando procesamiento de archivos Excel locales")

        # Convertir paths a Path objects para compatibilidad
        path_objects = {name: Path(path) for name, path in file_paths.items()}

        # Usar el método existente de carga
        if not self.load_excel_files(path_objects):
            raise ValueError("Error al cargar archivos Excel")

        logger.info(
            f"Procesamiento completado: Excel1={len(self.excel1_df)}, Excel2={len(self.excel2_df)}, Excel3={len(self.excel3_df)}, Excel4={len(self.excel4_df)} registros"
        )

        # Retornar DataFrames individuales en lugar de combinar
        # Esto permite al DataMapper hacer la combinación correcta manteniendo todas las columnas
        result = {}

        if self.excel1_df is not None and not self.excel1_df.empty:
            result["excel1"] = self.excel1_df

        if self.excel2_df is not None and not self.excel2_df.empty:
            result["excel2"] = self.excel2_df

        if self.excel3_df is not None and not self.excel3_df.empty:
            result["excel3"] = self.excel3_df

        if self.excel4_df is not None and not self.excel4_df.empty:
            result["excel4"] = self.excel4_df

        # Crear la combinación completa incluyendo Excel3
        if "excel1" in result and "excel2" in result:
            # Comenzar con Excel1 y Excel2 por RUT
            combined_df = pd.merge(
                result["excel1"],
                result["excel2"],
                on="RUT",
                how="outer",
                suffixes=("", "_excel2"),
            )

            # Agregar Excel3 por episodio si existe
            if "excel3" in result:
                # Primero necesitamos obtener la columna de episodio de cada DataFrame
                excel1_episodio_col = None
                for col in [
                    "CÓDIGO EPISODIO CMBD",
                    "episodio_cmbd",
                    "CMBD",
                    "Episodio",
                ]:
                    if col in combined_df.columns:
                        excel1_episodio_col = col
                        break

                excel3_episodio_col = None
                for col in ["EPISODIO", "episodio_cmbd", "CMBD", "Codigo Episodio"]:
                    if col in result["excel3"].columns:
                        excel3_episodio_col = col
                        break

                print(f"[DEBUG] Excel1 episodio col: {excel1_episodio_col}")
                print(f"[DEBUG] Excel3 episodio col: {excel3_episodio_col}")

                if excel1_episodio_col and excel3_episodio_col:
                    # Renombrar columnas para el merge
                    excel3_for_merge = result["excel3"].rename(
                        columns={excel3_episodio_col: excel1_episodio_col}
                    )
                    print(f"[DEBUG] Excel3 columnas: {list(excel3_for_merge.columns)}")

                    # Hacer el merge por episodio
                    combined_df = pd.merge(
                        combined_df,
                        excel3_for_merge,
                        on=excel1_episodio_col,
                        how="left",
                        suffixes=("", "_excel3"),
                    )
                    print(
                        f"[DEBUG] Combined después de Excel3: {list(combined_df.columns)}"
                    )

            # Agregar score social desde Excel4 por episodio si existe
            if "excel4" in result:
                df4 = result["excel4"]

                episodio_col_4 = "Episodio / Estadía"
                puntaje_col = "Puntaje"

                # 1. Normalizar tipos a string para evitar errores de merge
                combined_df["CÓDIGO EPISODIO CMBD"] = combined_df["CÓDIGO EPISODIO CMBD"].astype(str)
                df4[episodio_col_4] = df4[episodio_col_4].astype(str)

                # 2. Reducir Excel4 solo a episodio + puntaje
                df4_reduced = df4[[episodio_col_4, puntaje_col]].copy()
                df4_reduced = df4_reduced.rename(columns={
                    episodio_col_4: "CÓDIGO EPISODIO CMBD",
                    puntaje_col: "score_social"  
                })

                print(df4_reduced.head())

                # 3. Merge LEFT para agregar score_social
                combined_df = pd.merge(
                    combined_df,
                    df4_reduced,
                    on="CÓDIGO EPISODIO CMBD",
                    how="left"
                )

            result["combined"] = combined_df

        return result
