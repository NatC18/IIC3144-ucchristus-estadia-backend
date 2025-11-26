"""
Mapeador para transformar datos de pandas a estructuras de modelos Django
"""

import logging
from datetime import date, datetime
from typing import Any, Dict, List, Optional

import pandas as pd
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)


class DataMapper:
    """
    Transforma datos de pandas DataFrames a estructuras compatibles con modelos Django
    """

    def __init__(self):
        self.mapped_data = {
            "pacientes": [],
            "episodios": [],
            "gestiones": [],
            "transferencias": [],
            "camas": [],
        }

    def map_all_data(
        self, clean_data: Dict[str, pd.DataFrame]
    ) -> Dict[str, List[Dict]]:
        """
        Mapea todos los datos a estructuras Django

        Args:
            clean_data: Dict con DataFrames limpios (debe contener 'combined' del ExcelProcessor)

        Returns:
            Dict con listas de diccionarios listos para Django
        """
        try:
            logger.info("Iniciando mapeo de datos a estructuras Django...")

            # Usar datos combinados del ExcelProcessor
            if "combined" in clean_data and not clean_data["combined"].empty:
                combined_df = clean_data["combined"]

                # Mapear cada tipo de datos desde el DataFrame combinado
                self.mapped_data["pacientes"] = self._map_pacientes_from_combined(
                    combined_df
                )
                self.mapped_data["camas"] = self._map_camas_from_combined(combined_df)
                self.mapped_data["episodios"] = self._map_episodios_from_combined(
                    combined_df
                )
                self.mapped_data["gestiones"] = self._map_gestiones_from_combined(
                    combined_df
                )
                self.mapped_data["transferencias"] = (
                    self._map_transferencias_from_combined(combined_df)
                )

            # Estadísticas
            stats = {
                "pacientes": len(self.mapped_data["pacientes"]),
                "episodios": len(self.mapped_data["episodios"]),
                "gestiones": len(self.mapped_data["gestiones"]),
                "transferencias": len(self.mapped_data["transferencias"]),
                "camas": len(self.mapped_data["camas"]),
            }
            logger.info(f"Mapeo completado: {stats}")

            return self.mapped_data

        except Exception as e:
            logger.error(f"Error en mapeo de datos: {str(e)}")
            return {}

    def _map_pacientes_from_combined(self, df: pd.DataFrame) -> List[Dict]:
        """
        Mapea datos de pacientes desde el DataFrame combinado
        """
        pacientes = []
        logger.info(f"Mapeando pacientes desde {len(df)} registros combinados")

        # Crear una columna temporal de RUT normalizada para agrupar
        df_temp = df.copy()
        df_temp["rut_normalizado"] = df_temp.apply(
            lambda row: self._extract_rut_from_row(row), axis=1
        )

        # Filtrar filas sin RUT válido
        df_temp = df_temp.dropna(subset=["rut_normalizado"])

        if len(df_temp) == 0:
            logger.warning("No se encontraron registros con RUT válido")
            return pacientes

        # Agrupar por RUT normalizado para evitar duplicados
        rut_groups = df_temp.groupby("rut_normalizado")

        for rut, group in rut_groups:
            try:
                # Tomar el primer registro del grupo
                row = group.iloc[0]

                # Extraer fecha de nacimiento del Excel2
                fecha_nacimiento = self._parse_date(
                    self._safe_get(row, "Fecha de Nacimiento")
                )

                # Extraer previsiones y truncar a 20 caracteres
                prevision_1_raw = (
                    self._safe_get(row, "Convenio")
                    or self._safe_get(row, "Nombre de la aseguradora")
                    or "OTRO"
                )
                prevision_2_raw = (
                    self._safe_get(row, "Nombre de la aseguradora")
                    if self._safe_get(row, "Convenio")
                    else None
                )

                prevision_1 = str(prevision_1_raw)[:20] if prevision_1_raw else "OTRO"
                prevision_2 = str(prevision_2_raw)[:20] if prevision_2_raw else None

                # Extraer sexo desde Excel1 (columna 'Sexo  (Desc)')
                sexo_desc = self._safe_get(row, "Sexo  (Desc)")
                sexo = self._map_sexo(sexo_desc)

                # Extraer score social desde Excel 4 (columna 'score_social')
                score_social = self._safe_get(row, "score_social")

                paciente_data = {
                    "rut": rut,
                    "nombre": self._extract_nombre_from_row(row),
                    "sexo": sexo,
                    "fecha_nacimiento": fecha_nacimiento,
                    "prevision_1": prevision_1,
                    "prevision_2": prevision_2,
                    "convenio": self._safe_get(row, "Convenio"),
                    "score_social": score_social,
                }

                if paciente_data["rut"] and paciente_data["nombre"]:
                    pacientes.append(paciente_data)
                    logger.debug(
                        f"Paciente mapeado: RUT={paciente_data['rut']}, Nombre={paciente_data['nombre']}, FechaNac={paciente_data['fecha_nacimiento']}"
                    )
                else:
                    logger.warning(
                        f"Paciente sin datos básicos: RUT={paciente_data['rut']}, Nombre={paciente_data['nombre']}"
                    )

            except Exception as e:
                logger.warning(f"Error mapeando paciente con RUT {rut}: {str(e)}")
                continue

        logger.info(f"Mapeados {len(pacientes)} pacientes únicos")
        return pacientes

    def _map_camas_from_combined(self, df: pd.DataFrame) -> List[Dict]:
        """
        Mapea datos de camas desde el DataFrame combinado
        """
        camas = []
        logger.info(f"Mapeando camas desde {len(df)} registros combinados")

        if "CAMA" in df.columns:
            cama_col = "CAMA"

        if "HABITACION" in df.columns:
            habitacion_col = "HABITACION"

        if not cama_col:
            logger.warning("No se encontraron columnas de cama en datos combinados")
            return camas

        # Procesar datos de cama
        camas_unicas = set()

        for idx, row in df.iterrows():
            try:
                codigo_cama = None
                habitacion = None

                if cama_col:
                    codigo_cama = self._safe_get(row, cama_col)
                    if codigo_cama:
                        codigo_cama = str(codigo_cama).strip()

                if habitacion_col:
                    habitacion = self._safe_get(row, habitacion_col)
                    if habitacion:
                        habitacion = str(habitacion).strip()

                # Crear clave única para evitar duplicados
                if codigo_cama and codigo_cama != "nan":
                    cama_key = f"{codigo_cama}|{habitacion or ''}"

                    if cama_key not in camas_unicas:
                        camas_unicas.add(cama_key)

                        # Si no hay habitación, generar una por defecto
                        if (
                            not habitacion
                            or habitacion.strip() == ""
                            or habitacion == "nan"
                        ):
                            habitacion = f"HAB-{codigo_cama}"

                        cama_data = {
                            "codigo_cama": codigo_cama,
                            "habitacion": f"HAB-{habitacion}",
                        }

                        camas.append(cama_data)

            except Exception as e:
                logger.warning(f"Error mapeando cama en fila {idx}: {str(e)}")
                continue

        logger.info(f"Mapeadas {len(camas)} camas únicas")
        return camas

    def _map_episodios_from_combined(self, df: pd.DataFrame) -> List[Dict]:
        """
        Mapea datos de episodios desde el DataFrame combinado
        """
        episodios = []
        logger.info(f"Mapeando episodios desde {len(df)} registros combinados")

        for idx, row in df.iterrows():
            try:
                # Obtener fechas de ingreso y egreso
                fecha_ingreso = self._parse_date_universal(
                    self._safe_get(row, "Fecha Ingreso completa")
                )

                # Para fecha de egreso, priorizar Excel2 (fecha real de alta)
                # Solo usar Excel1 si no hay datos en Excel2
                fecha_egreso_excel2 = self._safe_get(row, "Fecha alta")  # Del Excel2
                if (
                    fecha_egreso_excel2
                    and not pd.isna(fecha_egreso_excel2)
                    and str(fecha_egreso_excel2) != "nan"
                ):
                    # Hay fecha de alta en Excel2, usarla (fechas de gestión)
                    fecha_egreso = self._parse_date_universal(fecha_egreso_excel2)
                else:
                    # No hay fecha de alta en Excel2, el episodio sigue abierto
                    fecha_egreso = None

                servicio_ingreso = self._extract_servicios(row, "Ingreso")
                servicios_traslado = self._extract_servicios_traslado(row)
                servicio_egreso = self._extract_servicios(row, "Egreso")

                episodio_data = {
                    "episodio_cmbd": self._convert_to_int(
                        self._safe_get(row, "CÓDIGO EPISODIO CMBD")
                    ),
                    "rut_paciente": self._extract_rut_from_row(row),
                    "fecha_ingreso": fecha_ingreso,  # Del Excel1 - fechas reales del episodio
                    "fecha_egreso": fecha_egreso,  # Del Excel2 solo si existe, sino None (episodio abierto)
                    "tipo_actividad": self._safe_get(row, "Tipo Actividad"),
                    "inlier_outlier_flag": self._safe_get(
                        row, "Estancia Inlier / Outlier"
                    ),
                    "especialidad": self._safe_get(
                        row, "Especialidad médica de la intervención (des)"
                    ),
                    "estancia_prequirurgica": self._safe_get_float(
                        row, "Estancias Prequirurgicas Int  -Episodio-"
                    ),
                    "estancia_postquirurgica": self._safe_get_float(
                        row, "Estancias Postquirurgicas Int  -Episodio-"
                    ),
                    "estancia_norma_grd": self._safe_get_float(
                        row, "Estancia Norma GRD"
                    ),
                    "codigo_cama": self._extract_codigo_cama_from_row(row),
                    "servicios": [
                        {
                            "codigo": servicio_ingreso,
                            "fecha": fecha_ingreso,
                            "tipo": "INGRESO",
                        },
                        *servicios_traslado,
                        {
                            "codigo": servicio_egreso,
                            "fecha": fecha_egreso,
                            "tipo": "EGRESO",
                        },
                    ],
                }

                if episodio_data["episodio_cmbd"] and episodio_data["rut_paciente"]:
                    episodios.append(episodio_data)
                    logger.debug(
                        f"Episodio mapeado: CMBD={episodio_data['episodio_cmbd']}, RUT={episodio_data['rut_paciente']}, Cama={episodio_data['codigo_cama']}"
                    )
                else:
                    logger.warning(
                        f"Episodio sin datos básicos: CMBD={episodio_data['episodio_cmbd']}, RUT={episodio_data['rut_paciente']}"
                    )

            except Exception as e:
                logger.warning(f"Error mapeando episodio en fila {idx}: {str(e)}")
                continue

        logger.info(f"Mapeados {len(episodios)} episodios")
        return episodios

    def _map_gestiones_from_combined(self, df: pd.DataFrame) -> List[Dict]:
        """
        Mapea datos de gestiones desde el DataFrame combinado
        """
        gestiones = []
        logger.info(f"Mapeando gestiones desde {len(df)} registros combinados")

        gestion_col = "¿Qué gestión se solicito?"
        if gestion_col not in df.columns:
            logger.warning(f"Columna '{gestion_col}' no encontrada")
            return gestiones

        for idx, row in df.iterrows():
            try:
                tipo_gestion_raw = self._safe_get(row, gestion_col)
                if not tipo_gestion_raw or str(tipo_gestion_raw) == "nan":
                    continue

                # Saltear transferencias - se manejan separadamente
                if str(tipo_gestion_raw).lower() == "transferencia":
                    continue

                # Mapear tipos de gestión a los valores del modelo
                tipo_gestion_mapping = {
                    "homecare uccc": "HOMECARE_UCCC",
                    "homecare": "HOMECARE",
                    "traslado": "TRASLADO",
                    "activación beneficio isapre": "ACTIVACION_BENEFICIO_ISAPRE",
                    "autorización procedimiento": "AUTORIZACION_PROCEDIMIENTO",
                    "cobertura": "COBERTURA",
                    "Corte Cuentas": "CORTE_CUENTAS",
                }

                tipo_gestion = tipo_gestion_mapping.get(
                    str(tipo_gestion_raw).lower(), ""
                )

                # Usar fecha de admisión como fecha_inicio
                fecha_inicio = self._parse_date_universal(
                    self._safe_get(row, "Fecha admisión")
                )

                # Si no hay fecha, usar fecha actual
                if not fecha_inicio:
                    from django.utils import timezone

                    fecha_inicio = timezone.now()

                gestion_data = {
                    "episodio_cmbd": self._convert_to_int(
                        self._safe_get(row, "CÓDIGO EPISODIO CMBD")
                    ),
                    "tipo_gestion": tipo_gestion,
                    "estado_gestion": "INICIADA",  # Campo correcto del modelo
                    "fecha_inicio": fecha_inicio,  # Campo obligatorio
                    "informe": self._safe_get(row, "Informe")
                    or f"Gestión de tipo {tipo_gestion_raw}",
                }

                if gestion_data["episodio_cmbd"]:
                    gestiones.append(gestion_data)
                    logger.debug(
                        f"Gestión mapeada: CMBD={gestion_data['episodio_cmbd']}, Tipo={gestion_data['tipo_gestion']}"
                    )

            except Exception as e:
                logger.warning(f"Error mapeando gestión en fila {idx}: {str(e)}")
                continue

        logger.info(f"Mapeadas {len(gestiones)} gestiones")
        return gestiones

    def _map_transferencias_from_combined(self, df: pd.DataFrame) -> List[Dict]:
        """
        Mapea datos de transferencias desde el DataFrame combinado
        """
        transferencias = []
        logger.info(f"Mapeando transferencias desde {len(df)} registros combinados")

        gestion_col = "¿Qué gestión se solicito?"
        if gestion_col not in df.columns:
            logger.warning(f"Columna '{gestion_col}' no encontrada")
            return transferencias

        # Filtrar solo registros de transferencia
        transferencia_df = df[df[gestion_col] == "Transferencia"]

        for idx, row in transferencia_df.iterrows():
            try:
                transferencia_data = {
                    "episodio_cmbd": self._convert_to_int(
                        self._safe_get(row, "CÓDIGO EPISODIO CMBD")
                    ),
                    "estado": self._safe_get(row, "Estado", "PENDIENTE"),
                    "motivo_cancelacion": self._safe_get(row, "Motivo de Cancelación"),
                    "motivo_rechazo": self._safe_get(row, "Motivo de Rechazo"),
                    "tipo_traslado": self._safe_get(row, "Tipo de Traslado"),
                    "motivo_traslado": self._safe_get(row, "Motivo de traslado"),
                    "centro_destinatario": self._safe_get(
                        row, "Centro de Destinatario"
                    ),
                    "fecha_solicitud": self._parse_date_universal(
                        self._safe_get(row, "Fecha admisión")
                    ),
                    "tipo_solicitud": self._safe_get(row, "Tipo de Solicitud"),
                }

                if transferencia_data["episodio_cmbd"]:
                    transferencias.append(transferencia_data)

            except Exception as e:
                logger.warning(f"Error mapeando transferencia en fila {idx}: {str(e)}")
                continue

        logger.info(f"Mapeadas {len(transferencias)} transferencias")
        return transferencias

    # Métodos de utilidad
    def _extract_codigo_cama(self, cama_info: str) -> str:
        """Extrae el código de cama de la información de cama y habitación"""
        if not cama_info or str(cama_info) == "nan":
            return None

        cama_str = str(cama_info).strip()
        # Tomar la primera parte antes del guión si existe
        return cama_str.split("-")[0].strip() if "-" in cama_str else cama_str

    def _extract_rut_from_row(self, row: pd.Series) -> str:
        """Extrae el RUT de una fila, manejando diferentes nombres de columnas"""
        rut_cols = ["RUT", "rut", "RUT_PACIENTE", "rut_paciente"]
        for col in rut_cols:
            if col in row.index:
                rut_value = self._safe_get(row, col)
                if rut_value and str(rut_value) != "nan":
                    return self._clean_rut(str(rut_value))
        return None

    def _extract_nombre_from_row(self, row: pd.Series) -> str:
        """Extrae el nombre de una fila, manejando diferentes nombres de columnas"""
        nombre_cols = [
            "Nombre",
            "nombre",
            "NOMBRE_PACIENTE",
            "nombre_paciente",
            "Nombre del Paciente",
        ]
        for col in nombre_cols:
            if col in row.index:
                nombre_value = self._safe_get(row, col)
                if nombre_value and str(nombre_value) != "nan":
                    return str(nombre_value).strip()
        return None

    def _extract_codigo_cama_from_row(self, row: pd.Series) -> str:
        """Extrae código de cama de una fila, manejando columnas separadas o combinadas"""

        # Buscar en columnas separadas
        cama_cols = ["Cama", "cama", "CAMA"]
        for col in cama_cols:
            if col in row.index:
                cama_info = self._safe_get(row, col)
                if cama_info and str(cama_info) != "nan":
                    return str(cama_info).strip()

        return None

    def _extract_servicios(self, row: pd.Series, tipo: str) -> str:
        """Extrae los códigos de servicios de una fila, filtrando por tipo"""

        if tipo == "Ingreso":
            servicio = self._safe_get(row, "Servicio Ingreso (Código)")
            if servicio and str(servicio) != "nan":
                return str(servicio).strip()

        elif tipo == "Egreso":
            servicio = self._safe_get(row, "Servicio Egreso (Código)_2")
            if servicio and str(servicio) != "nan":
                return str(servicio).strip()

    def _extract_servicios_traslado(self, row: pd.Series) -> List[str]:
        """Extrae los códigos de servicios de traslado de una fila"""
        import re

        servicios_traslado = []
        servicios = []

        servicio_traslados = self._safe_get(row, "Conjunto de Servicios Traslado")
        if servicio_traslados and isinstance(servicio_traslados, str):
            servicios = re.findall(r"\[([^\]]+)\]", servicio_traslados)

        for i, servicio in enumerate(servicios):
            fecha = self._parse_date_universal(
                self._safe_get(row, f"Fecha       (tr{i+1})")
            )
            s = {
                "codigo": servicio,
                "fecha": fecha,
                "tipo": "TRASLADO",
            }
            servicios_traslado.append(s)
        return servicios_traslado

    def _map_episodios(self, df: pd.DataFrame) -> List[Dict]:
        """
        Mapea datos de episodios

        Args:
            df: DataFrame con datos de episodios

        Returns:
            Lista de diccionarios para modelo Episodio
        """
        episodios = []

        logger.info(f"Mapeando {len(df)} registros de episodios")
        logger.info(f"Columnas disponibles: {list(df.columns)}")

        for idx, row in df.iterrows():
            try:
                # Usar los nombres de columna que vienen del ExcelProcessor
                episodio_cmbd = self._safe_get(row, "episodio_cmbd")
                fecha_ingreso = self._parse_date_universal(
                    self._safe_get(row, "fecha_ingreso")
                )

                # Debug para los primeros registros
                if idx < 3:
                    logger.info(
                        f"Registro {idx}: episodio={episodio_cmbd}, fecha_ingreso={fecha_ingreso}"
                    )

                episodio_data = {
                    "episodio_cmbd": self._convert_to_int(
                        episodio_cmbd
                    ),  # Convertir a entero
                    # Agregar información del paciente para la búsqueda
                    "rut_paciente": self._safe_get(
                        row, "rut"
                    ),  # Extraer RUT del paciente de los datos combinados
                    "nombre_paciente": self._safe_get(
                        row, "nombre"
                    ),  # Extraer nombre del paciente
                    "fecha_ingreso": fecha_ingreso,
                    "fecha_egreso": self._parse_date_universal(
                        self._safe_get(row, "fecha_alta")
                    ),  # Cambiado de 'fecha_egreso' a 'fecha_alta'
                    "tipo_actividad": self._safe_get(
                        row, "tipo_actividad", "Hospitalización"
                    ),
                    "especialidad": self._safe_get(
                        row, "servicio"
                    ),  # Cambiado de 'especialidad' a 'servicio'
                    "cama": self._safe_get(
                        row, "cama"
                    ),  # Cambiado de 'cama_codigo' a 'cama'
                    "habitacion": self._safe_get(row, "habitacion"),
                    "diagnostico_principal": self._safe_get(
                        row, "diagnostico_principal"
                    ),
                    "estado": self._safe_get(row, "estado"),
                    "estancia_dias": self._safe_get_int(row, "estancia_dias"),
                    "inlier_outlier_flag": self._safe_get(row, "inlier_outlier_flag"),
                    "estancia_prequirurgica": self._safe_get_float(
                        row, "estancia_prequirurgica"
                    ),
                    "estancia_postquirurgica": self._safe_get_float(
                        row, "estancia_postquirurgica"
                    ),
                    "estancia_norma_grd": self._safe_get_float(
                        row, "estancia_norma_grd"
                    ),
                }

                # Validaciones básicas
                if not episodio_data["episodio_cmbd"]:
                    logger.warning(f"Episodio sin número CMBD")
                    continue

                if not episodio_data["fecha_ingreso"]:
                    logger.warning(
                        f"Episodio {episodio_data['episodio_cmbd']} sin fecha de ingreso"
                    )
                    # Usar fecha actual como fallback
                    episodio_data["fecha_ingreso"] = datetime.now()

                episodios.append(episodio_data)

            except Exception as e:
                logger.error(f"Error mapeando episodio en fila {idx}: {str(e)}")
                continue

        logger.info(f"Episodios mapeados: {len(episodios)}")
        return episodios

    def _map_gestiones(self, df: pd.DataFrame) -> List[Dict]:
        """
        Mapea datos de gestiones

        Args:
            df: DataFrame con datos de gestiones

        Returns:
            Lista de diccionarios para modelo Gestion
        """
        gestiones = []

        logger.info(f"Mapeando {len(df)} registros de gestiones")
        logger.info(f"Columnas disponibles: {list(df.columns)}")

        for idx, row in df.iterrows():
            try:
                # Usar los nombres de columna que vienen del ExcelProcessor
                episodio_cmbd = self._safe_get(row, "episodio_cmbd")
                tipo_gestion = self._map_tipo_gestion(
                    self._safe_get(row, "tipo_gestion")
                )

                # Debug para los primeros registros
                if idx < 3:
                    logger.info(
                        f"Registro {idx}: episodio={episodio_cmbd}, tipo={tipo_gestion}"
                    )

                gestion_data = {
                    "episodio_cmbd": self._convert_to_int(
                        episodio_cmbd
                    ),  # Convertir a entero
                    "tipo_gestion": tipo_gestion,
                    "estado_gestion": self._map_estado_gestion(
                        self._safe_get(row, "estado_gestion")
                    ),
                    "fecha_inicio": self._parse_date_universal(
                        self._safe_get(row, "fecha_inicio")
                    ),  # Cambiado de 'fecha_inicio_gestion'
                    "fecha_fin": self._parse_date_universal(
                        self._safe_get(row, "fecha_fin")
                    ),  # Cambiado de 'fecha_fin_gestion'
                    "informe": self._safe_get(
                        row, "observaciones"
                    ),  # Cambiado de 'informe_gestion' a 'observaciones'
                    "usuario_email": self._safe_get(
                        row, "usuario_responsable"
                    ),  # Cambiado de 'usuario_gestion'
                    "valor_gestion": self._safe_get_float(row, "valor_gestion"),
                }

                # Validaciones básicas
                if not gestion_data["episodio_cmbd"]:
                    continue

                if not gestion_data["tipo_gestion"]:
                    logger.warning(
                        f"Gestión sin tipo para episodio {gestion_data['episodio_cmbd']}"
                    )
                    continue

                gestiones.append(gestion_data)

            except Exception as e:
                logger.error(f"Error mapeando gestión en fila {idx}: {str(e)}")
                continue

        logger.info(f"Gestiones mapeadas: {len(gestiones)}")
        return gestiones
        return gestiones

    def _safe_get(self, row: pd.Series, column: str, default: Any = None) -> Any:
        """Obtiene valor de forma segura"""
        try:
            if column in row.index:
                value = row[column]
                if pd.isna(value):
                    return default
                return value
            return default
        except:
            return default

    def _safe_get_int(
        self, row: pd.Series, column: str, default: Optional[int] = None
    ) -> Optional[int]:
        """Obtiene entero de forma segura"""
        value = self._safe_get(row, column)
        if value is None:
            return default
        try:
            return int(float(value))
        except:
            return default

    def _convert_to_int(
        self, value: Any, default: Optional[int] = None
    ) -> Optional[int]:
        """Convierte cualquier valor a entero de forma segura"""
        if value is None or pd.isna(value):
            return default
        try:
            return int(float(value))
        except:
            return default

    def _safe_get_float(
        self, row: pd.Series, column: str, default: Optional[float] = None
    ) -> Optional[float]:
        """Obtiene float de forma segura"""
        value = self._safe_get(row, column)
        if value is None:
            return default
        try:
            return float(value)
        except:
            return default

    def _clean_rut(self, rut: str) -> Optional[str]:
        """Limpia y valida formato de RUT"""
        if not rut:
            return None

        try:
            # Convertir a string y limpiar
            rut_str = str(rut).strip()

            # Si ya tiene formato correcto, retornar
            if self._validate_rut_format(rut_str):
                return rut_str

            # Intentar formatear RUT sin formato
            import re

            # Remover todo excepto números, k, K
            clean = re.sub(r"[^0-9kK]", "", rut_str)

            if len(clean) >= 8:
                # Separar cuerpo y dígito verificador
                cuerpo = clean[:-1]
                dv = clean[-1]

                # Formatear
                if len(cuerpo) >= 7:
                    formatted = f"{cuerpo[:-6]}.{cuerpo[-6:-3]}.{cuerpo[-3:]}-{dv}"
                    return formatted

            return rut_str  # Retornar original si no se puede formatear

        except Exception as e:
            logger.warning(f"Error limpiando RUT {rut}: {str(e)}")
            return str(rut) if rut else None

    def _validate_rut_format(self, rut: str) -> bool:
        """Valida formato de RUT chileno"""
        import re

        pattern = r"^\d{1,2}\.\d{3}\.\d{3}-[\dkK]$"
        return bool(re.match(pattern, rut))

    def _map_sexo(self, sexo: str) -> str:
        """
        Mapea valores de sexo desde diferentes formatos a códigos del modelo

        Args:
            sexo: Valor del sexo ('F', 'M', 'Femenino', 'Masculino', etc.)

        Returns:
            Código de sexo ('F', 'M', 'O')
        """
        if not sexo:
            return "O"  # Otro por defecto

        sexo_str = str(sexo).lower().strip()

        # Mapeo más completo incluyendo todas las variantes encontradas
        if sexo_str in ["m", "masculino", "hombre", "male"]:
            return "M"
        elif sexo_str in ["f", "femenino", "mujer", "female"]:
            return "F"
        else:
            return "O"

    def _parse_date(self, date_value: Any) -> Optional[date]:
        """Parsea fecha a objeto date"""
        if pd.isna(date_value) or date_value is None:
            return None

        try:
            # Si ya es date
            if isinstance(date_value, date):
                return date_value

            # Si es datetime
            if isinstance(date_value, datetime):
                return date_value.date()

            # Si es string
            if isinstance(date_value, str):
                return self._parse_date_universal(date_value)

            # Si es timestamp de pandas
            if hasattr(date_value, "date"):
                return date_value.date()

            return None

        except Exception as e:
            logger.warning(f"Error parseando fecha {date_value}: {str(e)}")
            return None

    def _parse_date_universal(self, date_value: Any) -> Optional[datetime]:
        """
        Función universal para parsear fechas en cualquier formato
        Reemplaza a _parse_date_string y _parse_datetime
        """
        if pd.isna(date_value) or date_value is None:
            return None

        try:
            # Si ya es datetime, retornarlo
            if isinstance(date_value, datetime):
                return date_value

            # Si es date, convertir a datetime
            if isinstance(date_value, date):
                return datetime.combine(date_value, datetime.min.time())

            # Si es timestamp de pandas
            if pd.api.types.is_datetime64_any_dtype(type(date_value)):
                return pd.to_datetime(date_value).to_pydatetime()

            # Si es string, parsear con múltiples formatos
            if isinstance(date_value, str):
                date_value = date_value.strip()
                if not date_value:
                    return None

                # Formatos ordenados por prioridad (más específicos primero)
                formats = [
                    "%Y-%m-%d %H:%M:%S",  # 2024-10-26 15:30:00
                    "%Y-%m-%d",  # 2024-10-26
                    "%d/%m/%Y %H:%M:%S",  # 26/10/2024 15:30:00
                    "%d/%m/%Y %H:%M",  # 26/10/2024 15:30
                    "%d/%m/%Y",  # 26/10/2024
                    "%m/%d/%Y %H:%M:%S",  # 10/26/2024 15:30:00
                    "%m/%d/%Y %H:%M",  # 10/26/2024 15:30
                    "%m/%d/%Y",  # 10/26/2024
                    "%d-%m-%Y %H:%M:%S",  # 26-10-2024 15:30:00
                    "%d-%m-%Y",  # 26-10-2024
                    "%m-%d-%Y %H:%M:%S",  # 10-26-2024 15:30:00
                    "%m-%d-%Y",  # 10-26-2024
                    "%Y/%m/%d",  # 2024/10/26
                    "%d.%m.%Y",  # 26.10.2024
                    "%Y.%m.%d",  # 2024.10.26
                    "%d/%m/%y %H:%M",  # 26/10/24 15:30
                    "%d/%m/%y",  # 26/10/24
                    "%m/%d/%y %H:%M",  # 10/26/24 15:30
                    "%m/%d/%y",  # 10/26/24
                    "%m-%d-%y %H:%M",  # 10-26-24 15:30
                    "%m-%d-%y",  # 10-26-24
                    "%d-%m-%y",  # 26-10-24
                ]

                for fmt in formats:
                    try:
                        return datetime.strptime(date_value, fmt)
                    except ValueError:
                        continue

                # Último intento con pandas
                try:
                    return pd.to_datetime(date_value).to_pydatetime()
                except:
                    pass

        except Exception as e:
            logger.warning(f"No se pudo parsear la fecha {date_value}: {e}")

        return None

        return None

    def _map_tipo_gestion(self, tipo: str) -> str:
        """Mapea tipos de gestión a valores válidos del modelo"""
        if not tipo:
            return "GESTION_CLINICA"  # Valor por defecto

        tipo_str = str(tipo).upper().strip()

        # Mapeo de valores comunes
        mapping = {
            "HOMECARE": "HOMECARE",
            "TRASLADO": "TRASLADO",
            "AUTORIZACION": "AUTORIZACION_PROCEDIMIENTO",
            "COBERTURA": "COBERTURA",
            "GESTION_CLINICA": "GESTION_CLINICA",
            "CLINICA": "GESTION_CLINICA",
        }

        # Buscar coincidencia exacta
        if tipo_str in mapping:
            return mapping[tipo_str]

        # Buscar coincidencia parcial
        for key, value in mapping.items():
            if key in tipo_str:
                return value

        return "GESTION_CLINICA"  # Fallback

    def _map_estado_gestion(self, estado: str) -> str:
        """Mapea estados de gestión a valores válidos del modelo"""
        if not estado:
            return "INICIADA"  # Valor por defecto

        estado_str = str(estado).upper().strip()

        # Mapeo de valores
        mapping = {
            "INICIADA": "INICIADA",
            "EN_PROGRESO": "EN_PROGRESO",
            "PROGRESO": "EN_PROGRESO",
            "COMPLETADA": "COMPLETADA",
            "COMPLETA": "COMPLETADA",
            "CANCELADA": "CANCELADA",
            "CANCEL": "CANCELADA",
        }

        if estado_str in mapping:
            return mapping[estado_str]

        # Buscar coincidencia parcial
        for key, value in mapping.items():
            if key in estado_str:
                return value

    def map_processed_data(
        self, processed_data: Dict[str, pd.DataFrame]
    ) -> Dict[str, List[Dict]]:
        """
        Mapea datos ya procesados (equivalente a map_all_data)
        Método alternativo para compatibilidad con diferentes flujos

        Args:
            processed_data: Dict con DataFrames procesados y limpios

        Returns:
            Dict con listas de diccionarios listos para Django
        """
        return self.map_all_data(processed_data)
