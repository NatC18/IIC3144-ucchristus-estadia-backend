"""
Procesadores específicos para cada modelo del sistema
"""

import re
from datetime import date, datetime
from typing import Dict, List, Optional

import pandas as pd
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from django.utils import timezone

from api.models import Cama, Episodio, Gestion, Paciente, Servicio, User

from .excel_processor import ExcelProcessor


class UserExcelProcessor(ExcelProcessor):
    """Procesador para archivos Excel de usuarios"""

    def get_columnas_requeridas(self) -> List[str]:
        return ["email", "nombre", "apellido", "rol"]

    def get_columnas_opcionales(self) -> List[str]:
        return ["rut", "telefono", "is_staff", "is_active", "password"]

    def _validar_estructura(self) -> bool:
        """Valida que tenga las columnas necesarias para usuarios"""
        columnas_df = set(self.df.columns)
        columnas_requeridas = set(self.get_columnas_requeridas())

        if not columnas_requeridas.issubset(columnas_df):
            faltantes = columnas_requeridas - columnas_df
            self._agregar_error(
                1, f"Faltan columnas requeridas: {', '.join(faltantes)}"
            )
            return False

        return True

    def _validar_fila(self, datos: Dict, numero_fila: int) -> Optional[Dict]:
        """Valida los datos específicos de un usuario"""
        errores_fila = []

        # Email requerido y válido
        if not datos.get("email"):
            errores_fila.append("Email es requerido")
        elif not re.match(
            r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", datos["email"]
        ):
            errores_fila.append("Email no tiene formato válido")
        elif User.objects.filter(email=datos["email"]).exists():
            errores_fila.append(f"Ya existe usuario con email {datos['email']}")

        # Nombre y apellido requeridos
        if not datos.get("nombre"):
            errores_fila.append("Nombre es requerido")
        if not datos.get("apellido"):
            errores_fila.append("Apellido es requerido")

        # Rol válido
        roles_validos = ["ADMIN", "MEDICO", "ENFERMERO", "RECEPCION", "OTRO"]
        if not datos.get("rol"):
            errores_fila.append("Rol es requerido")
        elif datos["rol"].upper() not in roles_validos:
            errores_fila.append(f"Rol debe ser uno de: {', '.join(roles_validos)}")

        # RUT válido (si se proporciona)
        if datos.get("rut"):
            if not self._validar_rut(datos["rut"]):
                errores_fila.append("RUT no tiene formato válido")

        if errores_fila:
            self._agregar_error(numero_fila, "; ".join(errores_fila))
            return None

        return datos

    def _procesar_fila_modelo(self, datos: Dict, numero_fila: int):
        """Crea un nuevo usuario con los datos validados"""
        user_data = {
            "email": datos["email"],
            "nombre": datos["nombre"],
            "apellido": datos["apellido"],
            "rol": datos["rol"].upper(),
            "rut": datos.get("rut", ""),
            "is_staff": datos.get("is_staff", False),
            "is_active": datos.get("is_active", True),
        }

        # Generar password si no se proporciona
        password = datos.get("password", "temp123")
        user_data["password"] = make_password(password)

        # Crear usuario
        User.objects.create(**user_data)


class PacienteExcelProcessor(ExcelProcessor):
    """Procesador para archivos Excel de pacientes"""

    def get_columnas_requeridas(self) -> List[str]:
        return ["rut", "nombre", "sexo", "fecha_nacimiento", "prevision"]

    def get_columnas_opcionales(self) -> List[str]:
        return ["convenio", "score_social"]

    def _validar_estructura(self) -> bool:
        """Valida que tenga las columnas necesarias para pacientes"""
        columnas_df = set(self.df.columns)
        columnas_requeridas = set(self.get_columnas_requeridas())

        if not columnas_requeridas.issubset(columnas_df):
            faltantes = columnas_requeridas - columnas_df
            self._agregar_error(
                1, f"Faltan columnas requeridas: {', '.join(faltantes)}"
            )
            return False

        return True

    def _validar_fila(self, datos: Dict, numero_fila: int) -> Optional[Dict]:
        """Valida los datos específicos de un paciente"""
        errores_fila = []

        # RUT requerido y único
        if not datos.get("rut"):
            errores_fila.append("RUT es requerido")
        elif not self._validar_rut(datos["rut"]):
            errores_fila.append("RUT no tiene formato válido")
        elif Paciente.objects.filter(rut=datos["rut"]).exists():
            errores_fila.append(f"Ya existe paciente con RUT {datos['rut']}")

        # Nombre requerido
        if not datos.get("nombre"):
            errores_fila.append("Nombre es requerido")

        # Sexo válido
        sexos_validos = ["M", "F", "O"]
        if not datos.get("sexo"):
            errores_fila.append("Sexo es requerido")
        elif datos["sexo"].upper() not in sexos_validos:
            errores_fila.append(f"Sexo debe ser uno de: {', '.join(sexos_validos)}")

        # Fecha de nacimiento válida
        if not datos.get("fecha_nacimiento"):
            errores_fila.append("Fecha de nacimiento es requerida")
        else:
            try:
                fecha_nac = self._convertir_fecha(datos["fecha_nacimiento"])
                if fecha_nac > date.today():
                    errores_fila.append("Fecha de nacimiento no puede ser futura")
            except:
                errores_fila.append("Fecha de nacimiento no tiene formato válido")

        # Previsión válida (opcional)
        previsiones_validas = ["FONASA", "ISAPRE", "PARTICULAR", "OTRO"]
        if (
            datos.get("prevision")
            and datos["prevision"].upper() not in previsiones_validas
        ):
            errores_fila.append(
                f"Previsión debe ser una de: {', '.join(previsiones_validas)}"
            )

        if errores_fila:
            self._agregar_error(numero_fila, "; ".join(errores_fila))
            return None

        return datos

    def _procesar_fila_modelo(self, datos: Dict, numero_fila: int):
        """Crea un nuevo paciente con los datos validados"""
        fecha_nacimiento = self._convertir_fecha(datos["fecha_nacimiento"])

        paciente_data = {
            "rut": datos["rut"],
            "nombre": datos["nombre"],
            "sexo": datos["sexo"].upper(),
            "fecha_nacimiento": fecha_nacimiento,
            "prevision_1": (
                datos.get("prevision", "").upper() if datos.get("prevision") else None
            ),
            "convenio": datos.get("convenio", ""),
            "score_social": datos.get("score_social"),
        }

        Paciente.objects.create(**paciente_data)


class CamaExcelProcessor(ExcelProcessor):
    """Procesador para archivos Excel de camas"""

    def get_columnas_requeridas(self) -> List[str]:
        return ["numero", "ubicacion", "tipo", "estado"]

    def get_columnas_opcionales(self) -> List[str]:
        return ["servicio", "observaciones"]

    def _validar_estructura(self) -> bool:
        """Valida que tenga las columnas necesarias para camas"""
        columnas_df = set(self.df.columns)
        columnas_requeridas = set(self.get_columnas_requeridas())

        if not columnas_requeridas.issubset(columnas_df):
            faltantes = columnas_requeridas - columnas_df
            self._agregar_error(
                1, f"Faltan columnas requeridas: {', '.join(faltantes)}"
            )
            return False

        return True

    def _validar_fila(self, datos: Dict, numero_fila: int) -> Optional[Dict]:
        """Valida los datos específicos de una cama"""
        errores_fila = []

        # Número de cama requerido y único
        if not datos.get("numero"):
            errores_fila.append("Número de cama es requerido")
        elif Cama.objects.filter(numero=datos["numero"]).exists():
            errores_fila.append(f"Ya existe cama con número {datos['numero']}")

        # Ubicación requerida
        if not datos.get("ubicacion"):
            errores_fila.append("Ubicación es requerida")

        # Tipo válido
        tipos_validos = ["INDIVIDUAL", "DOBLE", "UCI", "INTERMEDIO", "OTRO"]
        if not datos.get("tipo"):
            errores_fila.append("Tipo es requerido")
        elif datos["tipo"].upper() not in tipos_validos:
            errores_fila.append(f"Tipo debe ser uno de: {', '.join(tipos_validos)}")

        # Estado válido
        estados_validos = ["DISPONIBLE", "OCUPADA", "MANTENIMIENTO", "FUERA_SERVICIO"]
        if not datos.get("estado"):
            errores_fila.append("Estado es requerido")
        elif datos["estado"].upper() not in estados_validos:
            errores_fila.append(f"Estado debe ser uno de: {', '.join(estados_validos)}")

        if errores_fila:
            self._agregar_error(numero_fila, "; ".join(errores_fila))
            return None

        return datos

    def _procesar_fila_modelo(self, datos: Dict, numero_fila: int):
        """Crea una nueva cama con los datos validados"""
        cama_data = {
            "numero": datos["numero"],
            "ubicacion": datos["ubicacion"],
            "tipo": datos["tipo"].upper(),
            "estado": datos["estado"].upper(),
            "observaciones": datos.get("observaciones", ""),
        }

        Cama.objects.create(**cama_data)


class EpisodioExcelProcessor(ExcelProcessor):
    """Procesador para archivos Excel de episodios"""

    def get_columnas_requeridas(self) -> List[str]:
        return ["paciente_rut", "cama_numero", "fecha_ingreso", "tipo_episodio"]

    def get_columnas_opcionales(self) -> List[str]:
        return ["fecha_egreso", "diagnostico", "observaciones"]

    def _validar_estructura(self) -> bool:
        """Valida que tenga las columnas necesarias para episodios"""
        columnas_df = set(self.df.columns)
        columnas_requeridas = set(self.get_columnas_requeridas())

        if not columnas_requeridas.issubset(columnas_df):
            faltantes = columnas_requeridas - columnas_df
            self._agregar_error(
                1, f"Faltan columnas requeridas: {', '.join(faltantes)}"
            )
            return False

        return True

    def _validar_fila(self, datos: Dict, numero_fila: int) -> Optional[Dict]:
        """Valida los datos específicos de un episodio"""
        errores_fila = []

        # Paciente debe existir
        if not datos.get("paciente_rut"):
            errores_fila.append("RUT del paciente es requerido")
        else:
            try:
                paciente = Paciente.objects.get(rut=datos["paciente_rut"])
                datos["paciente"] = paciente
            except Paciente.DoesNotExist:
                errores_fila.append(
                    f"No existe paciente con RUT {datos['paciente_rut']}"
                )

        # Cama debe existir
        if not datos.get("cama_numero"):
            errores_fila.append("Número de cama es requerido")
        else:
            try:
                cama = Cama.objects.get(numero=datos["cama_numero"])
                datos["cama"] = cama
            except Cama.DoesNotExist:
                errores_fila.append(f"No existe cama con número {datos['cama_numero']}")

        # Fecha de ingreso válida
        if not datos.get("fecha_ingreso"):
            errores_fila.append("Fecha de ingreso es requerida")
        else:
            try:
                datos["fecha_ingreso_parsed"] = self._convertir_fecha(
                    datos["fecha_ingreso"]
                )
            except:
                errores_fila.append("Fecha de ingreso no tiene formato válido")

        # Fecha de egreso (si existe) debe ser posterior al ingreso
        if datos.get("fecha_egreso"):
            try:
                fecha_egreso = self._convertir_fecha(datos["fecha_egreso"])
                if (
                    "fecha_ingreso_parsed" in datos
                    and fecha_egreso <= datos["fecha_ingreso_parsed"]
                ):
                    errores_fila.append(
                        "Fecha de egreso debe ser posterior a la fecha de ingreso"
                    )
                datos["fecha_egreso_parsed"] = fecha_egreso
            except:
                errores_fila.append("Fecha de egreso no tiene formato válido")

        # Tipo de episodio válido
        tipos_validos = ["HOSPITALIZADO", "AMBULATORIO", "URGENCIA", "OTRO"]
        if not datos.get("tipo_episodio"):
            errores_fila.append("Tipo de episodio es requerido")
        elif datos["tipo_episodio"].upper() not in tipos_validos:
            errores_fila.append(
                f"Tipo de episodio debe ser uno de: {', '.join(tipos_validos)}"
            )

        if errores_fila:
            self._agregar_error(numero_fila, "; ".join(errores_fila))
            return None

        return datos

    def _procesar_fila_modelo(self, datos: Dict, numero_fila: int):
        """Crea un nuevo episodio con los datos validados"""
        episodio_data = {
            "paciente": datos["paciente"],
            "cama": datos["cama"],
            "fecha_ingreso": datos["fecha_ingreso_parsed"],
            "tipo_episodio": datos["tipo_episodio"].upper(),
            "diagnostico": datos.get("diagnostico", ""),
            "observaciones": datos.get("observaciones", ""),
        }

        if "fecha_egreso_parsed" in datos:
            episodio_data["fecha_egreso"] = datos["fecha_egreso_parsed"]

        Episodio.objects.create(**episodio_data)


class GestionExcelProcessor(ExcelProcessor):
    """Procesador para archivos Excel de gestiones"""

    def get_columnas_requeridas(self) -> List[str]:
        return ["episodio_id", "usuario_email", "tipo_gestion"]

    def get_columnas_opcionales(self) -> List[str]:
        return ["fecha_gestion", "observaciones", "prioridad"]

    def _validar_estructura(self) -> bool:
        """Valida que tenga las columnas necesarias para gestiones"""
        columnas_df = set(self.df.columns)
        columnas_requeridas = set(self.get_columnas_requeridas())

        if not columnas_requeridas.issubset(columnas_df):
            faltantes = columnas_requeridas - columnas_df
            self._agregar_error(
                1, f"Faltan columnas requeridas: {', '.join(faltantes)}"
            )
            return False

        return True

    def _validar_fila(self, datos: Dict, numero_fila: int) -> Optional[Dict]:
        """Valida los datos específicos de una gestión"""
        errores_fila = []

        # Episodio debe existir
        if not datos.get("episodio_id"):
            errores_fila.append("ID del episodio es requerido")
        else:
            try:
                episodio = Episodio.objects.get(id=datos["episodio_id"])
                datos["episodio"] = episodio
            except Episodio.DoesNotExist:
                errores_fila.append(f"No existe episodio con ID {datos['episodio_id']}")

        # Usuario debe existir
        if not datos.get("usuario_email"):
            errores_fila.append("Email del usuario es requerido")
        else:
            try:
                usuario = User.objects.get(email=datos["usuario_email"])
                datos["usuario"] = usuario
            except User.DoesNotExist:
                errores_fila.append(
                    f"No existe usuario con email {datos['usuario_email']}"
                )

        # Tipo de gestión válido
        tipos_validos = ["ADMINISTRATIVA", "CLINICA", "SOCIAL", "OTRO"]
        if not datos.get("tipo_gestion"):
            errores_fila.append("Tipo de gestión es requerido")
        elif datos["tipo_gestion"].upper() not in tipos_validos:
            errores_fila.append(
                f"Tipo de gestión debe ser uno de: {', '.join(tipos_validos)}"
            )

        # Fecha de gestión (si no se proporciona, usar fecha actual)
        if datos.get("fecha_gestion"):
            try:
                datos["fecha_gestion_parsed"] = self._convertir_fecha(
                    datos["fecha_gestion"]
                )
            except:
                errores_fila.append("Fecha de gestión no tiene formato válido")
        else:
            datos["fecha_gestion_parsed"] = date.today()

        if errores_fila:
            self._agregar_error(numero_fila, "; ".join(errores_fila))
            return None

        return datos

    def _procesar_fila_modelo(self, datos: Dict, numero_fila: int):
        """Crea una nueva gestión con los datos validados"""
        gestion_data = {
            "episodio": datos["episodio"],
            "usuario": datos["usuario"],
            "tipo_gestion": datos["tipo_gestion"].upper(),
            "fecha_gestion": datos["fecha_gestion_parsed"],
            "observaciones": datos.get("observaciones", ""),
            "prioridad": datos.get("prioridad", "NORMAL"),
        }

        Gestion.objects.create(**gestion_data)

    # Métodos auxiliares compartidos
    def _validar_rut(self, rut: str) -> bool:
        """Valida formato de RUT chileno"""
        if not rut:
            return False

        # Limpiar RUT (quitar puntos y guiones)
        rut_limpio = re.sub(r"[^0-9kK]", "", str(rut))

        if len(rut_limpio) < 8 or len(rut_limpio) > 9:
            return False

        return True

    def _convertir_fecha(self, fecha) -> date:
        """Convierte diferentes formatos de fecha a objeto date"""
        if isinstance(fecha, date):
            return fecha
        elif isinstance(fecha, datetime):
            return fecha.date()
        elif isinstance(fecha, str):
            # Intentar diferentes formatos
            formatos = [
                "%Y-%m-%d",
                "%d/%m/%Y",
                "%m/%d/%Y",
                "%d-%m-%Y",
                "%Y/%m/%d",
                "%m/%d/%y",
                "%d/%m/%y",
            ]
            for formato in formatos:
                try:
                    return datetime.strptime(fecha, formato).date()
                except:
                    continue
            raise ValueError(f"No se pudo convertir fecha: {fecha}")
        else:
            raise ValueError(f"Tipo de fecha no soportado: {type(fecha)}")


class PacienteEpisodioExcelProcessor(ExcelProcessor):
    """Procesador para archivos Excel que contienen datos de pacientes y episodios"""

    def get_columnas_requeridas(self) -> List[str]:
        return [
            "rut_paciente",
            "nombre_paciente",
            "episodio",
            "habitacion",
            "cama",
            "categoria_tratamiento",
            "fecha_admision",
        ]

    def get_columnas_opcionales(self) -> List[str]:
        return [
            "asign_enfermeria",
            "desc_enfermeria",
            "medico_tratante",
            "cama_bloqueada",
            "codigo_bloqueo",
            "descripcion_bloqueo",
            "tipo_movimiento",
            "fecha_carga",
            "desviación",
        ]

    def _validar_estructura(self) -> bool:
        """Valida que tenga las columnas necesarias para pacientes y episodios"""
        columnas_df = set(self.df.columns)
        columnas_requeridas = set(self.get_columnas_requeridas())

        if not columnas_requeridas.issubset(columnas_df):
            faltantes = columnas_requeridas - columnas_df
            self._agregar_error(
                1, f"Faltan columnas requeridas: {', '.join(faltantes)}"
            )
            return False

        return True

    def _validar_fila(self, datos: Dict, numero_fila: int) -> Optional[Dict]:
        """Valida los datos específicos de paciente y episodio"""
        errores_fila = []

        # Validar RUT del paciente
        if not datos.get("rut_paciente"):
            errores_fila.append("RUT del paciente es requerido")
        elif not self._validar_rut(datos["rut_paciente"]):
            errores_fila.append("RUT del paciente no tiene formato válido")

        # Validar nombre del paciente
        if not datos.get("nombre_paciente"):
            errores_fila.append("Nombre del paciente es requerido")

        # Validar número de episodio
        if not datos.get("episodio"):
            errores_fila.append("Número de episodio es requerido")
        else:
            try:
                episodio_num = int(datos["episodio"])
                # Verificar que no existe ya un episodio con este número
                if Episodio.objects.filter(episodio_cmbd=episodio_num).exists():
                    errores_fila.append(f"Ya existe episodio con número {episodio_num}")
                datos["episodio_cmbd"] = episodio_num
            except (ValueError, TypeError):
                errores_fila.append("Número de episodio debe ser numérico")

        # Validar y buscar cama
        if not datos.get("cama") or not datos.get("habitacion"):
            errores_fila.append("Código de cama y habitación son requeridos")
        else:
            try:
                cama = Cama.objects.get(
                    codigo_cama=datos["cama"], habitacion=datos["habitacion"]
                )

                # Verificar que la cama no esté ocupada por otro episodio activo
                episodio_activo = cama.episodios.filter(
                    fecha_egreso__isnull=True
                ).first()
                if episodio_activo:
                    errores_fila.append(
                        f"La cama {datos['cama']} ya está ocupada por episodio activo"
                    )

                datos["cama_obj"] = cama
            except Cama.DoesNotExist:
                errores_fila.append(
                    f"No existe cama {datos['cama']} en habitación {datos['habitacion']}"
                )

        # Validar fecha de admisión
        if not datos.get("fecha_admision"):
            errores_fila.append("Fecha de admisión es requerida")
        else:
            try:
                datos["fecha_admision_parsed"] = self._convertir_fecha_excel(
                    datos["fecha_admision"]
                )
            except Exception as e:
                errores_fila.append(f"Fecha de admisión inválida: {str(e)}")

        # Validar categoría de tratamiento
        if not datos.get("categoria_tratamiento"):
            errores_fila.append("Categoría de tratamiento es requerida")

        if errores_fila:
            self._agregar_error(numero_fila, "; ".join(errores_fila))
            return None

        return datos

    def _procesar_fila_modelo(self, datos: Dict, numero_fila: int):
        """Crea/actualiza paciente y crea episodio asociado"""
        try:
            # Crear o actualizar paciente
            paciente = self._crear_o_actualizar_paciente(datos)

            # Crear episodio
            self._crear_episodio(datos, paciente)

        except Exception as e:
            self._agregar_error(numero_fila, f"Error al procesar: {str(e)}")
            self.registros_error += 1
            raise

    def _crear_o_actualizar_paciente(self, datos: Dict) -> Paciente:
        """Crea un nuevo paciente o actualiza uno existente"""
        rut_paciente = datos["rut_paciente"]

        try:
            # Buscar paciente existente
            paciente = Paciente.objects.get(rut=rut_paciente)

            # Actualizar nombre si es diferente (opcional)
            if datos["nombre_paciente"] != paciente.nombre:
                paciente.nombre = datos["nombre_paciente"]
                paciente.save(update_fields=["nombre"])

            return paciente

        except Paciente.DoesNotExist:
            # Crear nuevo paciente con datos mínimos
            # Nota: Los campos requeridos como sexo y fecha_nacimiento
            # necesitarán valores por defecto o ser agregados al archivo
            paciente_data = {
                "rut": rut_paciente,
                "nombre": datos["nombre_paciente"],
                "sexo": "O",  # Valor por defecto - podría venir del archivo
                "fecha_nacimiento": date(1900, 1, 1),  # Valor por defecto
                "prevision_1": "OTRO",  # Valor por defecto
            }

            return Paciente.objects.create(**paciente_data)

    def _crear_episodio(self, datos: Dict, paciente: Paciente):
        """Crea un nuevo episodio para el paciente"""
        episodio_data = {
            "paciente": paciente,
            "cama": datos["cama_obj"],
            "episodio_cmbd": datos["episodio_cmbd"],
            "fecha_ingreso": timezone.make_aware(
                datetime.combine(datos["fecha_admision_parsed"], datetime.min.time())
            ),
            "tipo_actividad": datos.get("categoria_tratamiento", "Hospitalización"),
            "especialidad": datos.get("desc_enfermeria", ""),
            # Campos adicionales que podrían venir del archivo
            "inlier_outlier_flag": None,
            "estancia_prequirurgica": None,
            "estancia_postquirurgica": None,
            "estancia_norma_grd": None,
        }

        return Episodio.objects.create(**episodio_data)

    def _validar_rut(self, rut: str) -> bool:
        """Valida formato de RUT chileno"""
        if not rut:
            return False

        # Aceptar ambos formatos: XX.XXX.XXX-X o XXXXXXXX-X
        import re

        rut_str = str(rut).strip()

        # Formato con puntos: XX.XXX.XXX-X
        formato_con_puntos = re.match(r"^\d{1,2}\.\d{3}\.\d{3}-[\dkK]$", rut_str)
        # Formato sin puntos: XXXXXXXX-X
        formato_sin_puntos = re.match(r"^\d{7,8}-[\dkK]$", rut_str)

        return bool(formato_con_puntos or formato_sin_puntos)

    def _convertir_fecha_excel(self, fecha) -> date:
        """Convierte diferentes formatos de fecha de Excel a objeto date"""
        if pd.isna(fecha):
            raise ValueError("Fecha vacía")

        if isinstance(fecha, date):
            return fecha
        elif isinstance(fecha, datetime):
            return fecha.date()
        elif isinstance(fecha, (int, float)):
            # Fecha de Excel como número serial
            try:
                return pd.to_datetime(fecha, origin="1899-12-30", unit="D").date()
            except:
                raise ValueError(f"No se pudo convertir fecha numérica: {fecha}")
        elif isinstance(fecha, str):
            # Intentar diferentes formatos de texto
            formatos = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d", "%d.%m.%Y"]
            for formato in formatos:
                try:
                    return datetime.strptime(fecha.strip(), formato).date()
                except:
                    continue
            raise ValueError(f"No se pudo convertir fecha: {fecha}")
        else:
            raise ValueError(f"Tipo de fecha no soportado: {type(fecha)}")


# Agregar métodos auxiliares a la clase base
ExcelProcessor._validar_rut = lambda self, rut: GestionExcelProcessor._validar_rut(
    self, rut
)
ExcelProcessor._convertir_fecha = (
    lambda self, fecha: GestionExcelProcessor._convertir_fecha(self, fecha)
)

# ==========================================================================================
# 🧩 TESTS ADICIONALES - Cobertura de estructura y casos borde (procesors.py)
# ==========================================================================================

from unittest.mock import MagicMock

import pandas as pd
import pytest

from api.services import processors


@pytest.fixture
def archivo_mock():
    mock = MagicMock()
    mock.agregar_error = MagicMock()
    return mock


# ---------------------------------------------------
# 1️⃣ Estructura inválida en todos los procesadores
# ---------------------------------------------------


@pytest.mark.parametrize(
    "processor_class",
    [
        processors.UserExcelProcessor,
        processors.PacienteExcelProcessor,
        processors.CamaExcelProcessor,
        processors.EpisodioExcelProcessor,
        processors.GestionExcelProcessor,
        processors.PacienteEpisodioExcelProcessor,
    ],
)
def test_validar_estructura_invalida(processor_class, archivo_mock):
    """Debe agregar error cuando faltan columnas requeridas"""
    p = processor_class(archivo_mock)
    # DataFrame vacío sin columnas
    p.df = pd.DataFrame()
    result = p._validar_estructura()
    assert result is False
    archivo_mock.agregar_error.assert_called_once()


# ---------------------------------------------------
# 2️⃣ _convertir_fecha con formato americano mm/dd/yyyy
# ---------------------------------------------------


def test_convertir_fecha_formato_americano():
    """Cubre el formato mm/dd/yyyy y mm/dd/yy"""
    p = processors.GestionExcelProcessor(MagicMock())
    assert p._convertir_fecha("12/31/2023") == p._convertir_fecha("31/12/2023")
    assert isinstance(
        p._convertir_fecha("01/01/24"), type(p._convertir_fecha("2024-01-01"))
    )


# ---------------------------------------------------
# 3️⃣ _convertir_fecha con tipo no soportado
# ---------------------------------------------------


def test_convertir_fecha_tipo_invalido():
    """Debe lanzar ValueError con tipo no soportado (lista, dict, etc.)"""
    p = processors.GestionExcelProcessor(MagicMock())
    with pytest.raises(ValueError):
        p._convertir_fecha(["2024-01-01"])
    with pytest.raises(ValueError):
        p._convertir_fecha({"fecha": "2024-01-01"})


# ---------------------------------------------------
# 4️⃣ _validar_rut con largo incorrecto
# ---------------------------------------------------


def test_validar_rut_largo_incorrecto():
    """Cubre RUTs demasiado cortos o largos"""
    p = processors.GestionExcelProcessor(MagicMock())
    assert not p._validar_rut("12345")
    assert not p._validar_rut("1234567899999")
