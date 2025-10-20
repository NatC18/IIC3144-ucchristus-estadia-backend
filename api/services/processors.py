"""
Procesadores específicos para cada modelo del sistema
"""
import re
from datetime import datetime, date
from typing import Dict, List, Optional
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import make_password

from api.models import User, Paciente, Cama, Episodio, Gestion, Servicio
from .excel_processor import ExcelProcessor


class UserExcelProcessor(ExcelProcessor):
    """Procesador para archivos Excel de usuarios"""
    
    def get_columnas_requeridas(self) -> List[str]:
        return ['email', 'nombre', 'apellido', 'rol']
    
    def get_columnas_opcionales(self) -> List[str]:
        return ['rut', 'telefono', 'is_staff', 'is_active', 'password']
    
    def _validar_estructura(self) -> bool:
        """Valida que tenga las columnas necesarias para usuarios"""
        columnas_df = set(self.df.columns)
        columnas_requeridas = set(self.get_columnas_requeridas())
        
        if not columnas_requeridas.issubset(columnas_df):
            faltantes = columnas_requeridas - columnas_df
            self._agregar_error(1, f"Faltan columnas requeridas: {', '.join(faltantes)}")
            return False
        
        return True
    
    def _validar_fila(self, datos: Dict, numero_fila: int) -> Optional[Dict]:
        """Valida los datos específicos de un usuario"""
        errores_fila = []
        
        # Email requerido y válido
        if not datos.get('email'):
            errores_fila.append("Email es requerido")
        elif not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', datos['email']):
            errores_fila.append("Email no tiene formato válido")
        elif User.objects.filter(email=datos['email']).exists():
            errores_fila.append(f"Ya existe usuario con email {datos['email']}")
        
        # Nombre y apellido requeridos
        if not datos.get('nombre'):
            errores_fila.append("Nombre es requerido")
        if not datos.get('apellido'):
            errores_fila.append("Apellido es requerido")
        
        # Rol válido
        roles_validos = ['ADMIN', 'MEDICO', 'ENFERMERO', 'RECEPCION', 'OTRO']
        if not datos.get('rol'):
            errores_fila.append("Rol es requerido")
        elif datos['rol'].upper() not in roles_validos:
            errores_fila.append(f"Rol debe ser uno de: {', '.join(roles_validos)}")
        
        # RUT válido (si se proporciona)
        if datos.get('rut'):
            if not self._validar_rut(datos['rut']):
                errores_fila.append("RUT no tiene formato válido")
        
        if errores_fila:
            self._agregar_error(numero_fila, "; ".join(errores_fila))
            return None
        
        return datos
    
    def _procesar_fila_modelo(self, datos: Dict, numero_fila: int):
        """Crea un nuevo usuario con los datos validados"""
        user_data = {
            'email': datos['email'],
            'nombre': datos['nombre'],
            'apellido': datos['apellido'],
            'rol': datos['rol'].upper(),
            'rut': datos.get('rut', ''),
            'is_staff': datos.get('is_staff', False),
            'is_active': datos.get('is_active', True),
        }
        
        # Generar password si no se proporciona
        password = datos.get('password', 'temp123')
        user_data['password'] = make_password(password)
        
        # Crear usuario
        User.objects.create(**user_data)


class PacienteExcelProcessor(ExcelProcessor):
    """Procesador para archivos Excel de pacientes"""
    
    def get_columnas_requeridas(self) -> List[str]:
        return ['rut', 'nombre', 'sexo', 'fecha_nacimiento', 'prevision']
    
    def get_columnas_opcionales(self) -> List[str]:
        return ['convenio', 'score_social']
    
    def _validar_estructura(self) -> bool:
        """Valida que tenga las columnas necesarias para pacientes"""
        columnas_df = set(self.df.columns)
        columnas_requeridas = set(self.get_columnas_requeridas())
        
        if not columnas_requeridas.issubset(columnas_df):
            faltantes = columnas_requeridas - columnas_df
            self._agregar_error(1, f"Faltan columnas requeridas: {', '.join(faltantes)}")
            return False
        
        return True
    
    def _validar_fila(self, datos: Dict, numero_fila: int) -> Optional[Dict]:
        """Valida los datos específicos de un paciente"""
        errores_fila = []
        
        # RUT requerido y único
        if not datos.get('rut'):
            errores_fila.append("RUT es requerido")
        elif not self._validar_rut(datos['rut']):
            errores_fila.append("RUT no tiene formato válido")
        elif Paciente.objects.filter(rut=datos['rut']).exists():
            errores_fila.append(f"Ya existe paciente con RUT {datos['rut']}")
        
        # Nombre requerido
        if not datos.get('nombre'):
            errores_fila.append("Nombre es requerido")
        
        # Sexo válido
        sexos_validos = ['M', 'F', 'O']
        if not datos.get('sexo'):
            errores_fila.append("Sexo es requerido")
        elif datos['sexo'].upper() not in sexos_validos:
            errores_fila.append(f"Sexo debe ser uno de: {', '.join(sexos_validos)}")
        
        # Fecha de nacimiento válida
        if not datos.get('fecha_nacimiento'):
            errores_fila.append("Fecha de nacimiento es requerida")
        else:
            try:
                fecha_nac = self._convertir_fecha(datos['fecha_nacimiento'])
                if fecha_nac > date.today():
                    errores_fila.append("Fecha de nacimiento no puede ser futura")
            except:
                errores_fila.append("Fecha de nacimiento no tiene formato válido")
        
        # Previsión válida (opcional)
        previsiones_validas = ['FONASA', 'ISAPRE', 'PARTICULAR', 'OTRO']
        if datos.get('prevision') and datos['prevision'].upper() not in previsiones_validas:
            errores_fila.append(f"Previsión debe ser una de: {', '.join(previsiones_validas)}")
        
        if errores_fila:
            self._agregar_error(numero_fila, "; ".join(errores_fila))
            return None
        
        return datos
    
    def _procesar_fila_modelo(self, datos: Dict, numero_fila: int):
        """Crea un nuevo paciente con los datos validados"""
        fecha_nacimiento = self._convertir_fecha(datos['fecha_nacimiento'])
        
        paciente_data = {
            'rut': datos['rut'],
            'nombre': datos['nombre'],
            'sexo': datos['sexo'].upper(),
            'fecha_nacimiento': fecha_nacimiento,
            'prevision_1': datos.get('prevision', '').upper() if datos.get('prevision') else None,
            'convenio': datos.get('convenio', ''),
            'score_social': datos.get('score_social'),
        }
        
        Paciente.objects.create(**paciente_data)


class CamaExcelProcessor(ExcelProcessor):
    """Procesador para archivos Excel de camas"""
    
    def get_columnas_requeridas(self) -> List[str]:
        return ['numero', 'ubicacion', 'tipo', 'estado']
    
    def get_columnas_opcionales(self) -> List[str]:
        return ['servicio', 'observaciones']
    
    def _validar_estructura(self) -> bool:
        """Valida que tenga las columnas necesarias para camas"""
        columnas_df = set(self.df.columns)
        columnas_requeridas = set(self.get_columnas_requeridas())
        
        if not columnas_requeridas.issubset(columnas_df):
            faltantes = columnas_requeridas - columnas_df
            self._agregar_error(1, f"Faltan columnas requeridas: {', '.join(faltantes)}")
            return False
        
        return True
    
    def _validar_fila(self, datos: Dict, numero_fila: int) -> Optional[Dict]:
        """Valida los datos específicos de una cama"""
        errores_fila = []
        
        # Número de cama requerido y único
        if not datos.get('numero'):
            errores_fila.append("Número de cama es requerido")
        elif Cama.objects.filter(numero=datos['numero']).exists():
            errores_fila.append(f"Ya existe cama con número {datos['numero']}")
        
        # Ubicación requerida
        if not datos.get('ubicacion'):
            errores_fila.append("Ubicación es requerida")
        
        # Tipo válido
        tipos_validos = ['INDIVIDUAL', 'DOBLE', 'UCI', 'INTERMEDIO', 'OTRO']
        if not datos.get('tipo'):
            errores_fila.append("Tipo es requerido")
        elif datos['tipo'].upper() not in tipos_validos:
            errores_fila.append(f"Tipo debe ser uno de: {', '.join(tipos_validos)}")
        
        # Estado válido
        estados_validos = ['DISPONIBLE', 'OCUPADA', 'MANTENIMIENTO', 'FUERA_SERVICIO']
        if not datos.get('estado'):
            errores_fila.append("Estado es requerido")
        elif datos['estado'].upper() not in estados_validos:
            errores_fila.append(f"Estado debe ser uno de: {', '.join(estados_validos)}")
        
        if errores_fila:
            self._agregar_error(numero_fila, "; ".join(errores_fila))
            return None
        
        return datos
    
    def _procesar_fila_modelo(self, datos: Dict, numero_fila: int):
        """Crea una nueva cama con los datos validados"""
        cama_data = {
            'numero': datos['numero'],
            'ubicacion': datos['ubicacion'],
            'tipo': datos['tipo'].upper(),
            'estado': datos['estado'].upper(),
            'observaciones': datos.get('observaciones', ''),
        }
        
        Cama.objects.create(**cama_data)


class EpisodioExcelProcessor(ExcelProcessor):
    """Procesador para archivos Excel de episodios"""
    
    def get_columnas_requeridas(self) -> List[str]:
        return ['paciente_rut', 'cama_numero', 'fecha_ingreso', 'tipo_episodio']
    
    def get_columnas_opcionales(self) -> List[str]:
        return ['fecha_egreso', 'diagnostico', 'observaciones']
    
    def _validar_estructura(self) -> bool:
        """Valida que tenga las columnas necesarias para episodios"""
        columnas_df = set(self.df.columns)
        columnas_requeridas = set(self.get_columnas_requeridas())
        
        if not columnas_requeridas.issubset(columnas_df):
            faltantes = columnas_requeridas - columnas_df
            self._agregar_error(1, f"Faltan columnas requeridas: {', '.join(faltantes)}")
            return False
        
        return True
    
    def _validar_fila(self, datos: Dict, numero_fila: int) -> Optional[Dict]:
        """Valida los datos específicos de un episodio"""
        errores_fila = []
        
        # Paciente debe existir
        if not datos.get('paciente_rut'):
            errores_fila.append("RUT del paciente es requerido")
        else:
            try:
                paciente = Paciente.objects.get(rut=datos['paciente_rut'])
                datos['paciente'] = paciente
            except Paciente.DoesNotExist:
                errores_fila.append(f"No existe paciente con RUT {datos['paciente_rut']}")
        
        # Cama debe existir
        if not datos.get('cama_numero'):
            errores_fila.append("Número de cama es requerido")
        else:
            try:
                cama = Cama.objects.get(numero=datos['cama_numero'])
                datos['cama'] = cama
            except Cama.DoesNotExist:
                errores_fila.append(f"No existe cama con número {datos['cama_numero']}")
        
        # Fecha de ingreso válida
        if not datos.get('fecha_ingreso'):
            errores_fila.append("Fecha de ingreso es requerida")
        else:
            try:
                datos['fecha_ingreso_parsed'] = self._convertir_fecha(datos['fecha_ingreso'])
            except:
                errores_fila.append("Fecha de ingreso no tiene formato válido")
        
        # Fecha de egreso (si existe) debe ser posterior al ingreso
        if datos.get('fecha_egreso'):
            try:
                fecha_egreso = self._convertir_fecha(datos['fecha_egreso'])
                if 'fecha_ingreso_parsed' in datos and fecha_egreso <= datos['fecha_ingreso_parsed']:
                    errores_fila.append("Fecha de egreso debe ser posterior a la fecha de ingreso")
                datos['fecha_egreso_parsed'] = fecha_egreso
            except:
                errores_fila.append("Fecha de egreso no tiene formato válido")
        
        # Tipo de episodio válido
        tipos_validos = ['HOSPITALIZADO', 'AMBULATORIO', 'URGENCIA', 'OTRO']
        if not datos.get('tipo_episodio'):
            errores_fila.append("Tipo de episodio es requerido")
        elif datos['tipo_episodio'].upper() not in tipos_validos:
            errores_fila.append(f"Tipo de episodio debe ser uno de: {', '.join(tipos_validos)}")
        
        if errores_fila:
            self._agregar_error(numero_fila, "; ".join(errores_fila))
            return None
        
        return datos
    
    def _procesar_fila_modelo(self, datos: Dict, numero_fila: int):
        """Crea un nuevo episodio con los datos validados"""
        episodio_data = {
            'paciente': datos['paciente'],
            'cama': datos['cama'],
            'fecha_ingreso': datos['fecha_ingreso_parsed'],
            'tipo_episodio': datos['tipo_episodio'].upper(),
            'diagnostico': datos.get('diagnostico', ''),
            'observaciones': datos.get('observaciones', ''),
        }
        
        if 'fecha_egreso_parsed' in datos:
            episodio_data['fecha_egreso'] = datos['fecha_egreso_parsed']
        
        Episodio.objects.create(**episodio_data)


class GestionExcelProcessor(ExcelProcessor):
    """Procesador para archivos Excel de gestiones"""
    
    def get_columnas_requeridas(self) -> List[str]:
        return ['episodio_id', 'usuario_email', 'tipo_gestion']
    
    def get_columnas_opcionales(self) -> List[str]:
        return ['fecha_gestion', 'observaciones', 'prioridad']
    
    def _validar_estructura(self) -> bool:
        """Valida que tenga las columnas necesarias para gestiones"""
        columnas_df = set(self.df.columns)
        columnas_requeridas = set(self.get_columnas_requeridas())
        
        if not columnas_requeridas.issubset(columnas_df):
            faltantes = columnas_requeridas - columnas_df
            self._agregar_error(1, f"Faltan columnas requeridas: {', '.join(faltantes)}")
            return False
        
        return True
    
    def _validar_fila(self, datos: Dict, numero_fila: int) -> Optional[Dict]:
        """Valida los datos específicos de una gestión"""
        errores_fila = []
        
        # Episodio debe existir
        if not datos.get('episodio_id'):
            errores_fila.append("ID del episodio es requerido")
        else:
            try:
                episodio = Episodio.objects.get(id=datos['episodio_id'])
                datos['episodio'] = episodio
            except Episodio.DoesNotExist:
                errores_fila.append(f"No existe episodio con ID {datos['episodio_id']}")
        
        # Usuario debe existir
        if not datos.get('usuario_email'):
            errores_fila.append("Email del usuario es requerido")
        else:
            try:
                usuario = User.objects.get(email=datos['usuario_email'])
                datos['usuario'] = usuario
            except User.DoesNotExist:
                errores_fila.append(f"No existe usuario con email {datos['usuario_email']}")
        
        # Tipo de gestión válido
        tipos_validos = ['ADMINISTRATIVA', 'CLINICA', 'SOCIAL', 'OTRO']
        if not datos.get('tipo_gestion'):
            errores_fila.append("Tipo de gestión es requerido")
        elif datos['tipo_gestion'].upper() not in tipos_validos:
            errores_fila.append(f"Tipo de gestión debe ser uno de: {', '.join(tipos_validos)}")
        
        # Fecha de gestión (si no se proporciona, usar fecha actual)
        if datos.get('fecha_gestion'):
            try:
                datos['fecha_gestion_parsed'] = self._convertir_fecha(datos['fecha_gestion'])
            except:
                errores_fila.append("Fecha de gestión no tiene formato válido")
        else:
            datos['fecha_gestion_parsed'] = date.today()
        
        if errores_fila:
            self._agregar_error(numero_fila, "; ".join(errores_fila))
            return None
        
        return datos
    
    def _procesar_fila_modelo(self, datos: Dict, numero_fila: int):
        """Crea una nueva gestión con los datos validados"""
        gestion_data = {
            'episodio': datos['episodio'],
            'usuario': datos['usuario'],
            'tipo_gestion': datos['tipo_gestion'].upper(),
            'fecha_gestion': datos['fecha_gestion_parsed'],
            'observaciones': datos.get('observaciones', ''),
            'prioridad': datos.get('prioridad', 'NORMAL'),
        }
        
        Gestion.objects.create(**gestion_data)
    
    # Métodos auxiliares compartidos
    def _validar_rut(self, rut: str) -> bool:
        """Valida formato de RUT chileno"""
        if not rut:
            return False
        
        # Limpiar RUT (quitar puntos y guiones)
        rut_limpio = re.sub(r'[^0-9kK]', '', str(rut))
        
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
            formatos = ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d']
            for formato in formatos:
                try:
                    return datetime.strptime(fecha, formato).date()
                except:
                    continue
            raise ValueError(f"No se pudo convertir fecha: {fecha}")
        else:
            raise ValueError(f"Tipo de fecha no soportado: {type(fecha)}")


# Agregar métodos auxiliares a la clase base
ExcelProcessor._validar_rut = lambda self, rut: GestionExcelProcessor._validar_rut(self, rut)
ExcelProcessor._convertir_fecha = lambda self, fecha: GestionExcelProcessor._convertir_fecha(self, fecha)