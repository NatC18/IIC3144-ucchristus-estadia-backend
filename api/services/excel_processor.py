"""
Procesador base para archivos Excel
"""
import pandas as pd
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
from django.db import transaction
from django.core.exceptions import ValidationError
from api.models import ArchivoCarga


class ExcelProcessor(ABC):
    """
    Clase base abstracta para procesadores de archivos Excel específicos por modelo
    """
    
    def __init__(self, archivo_carga: ArchivoCarga):
        self.archivo_carga = archivo_carga
        self.df: Optional[pd.DataFrame] = None
        self.errores: List[Dict] = []
        self.registros_procesados = 0
        self.registros_error = 0
    
    def procesar_archivo(self) -> Dict[str, Any]:
        """
        Método principal que procesa todo el archivo Excel
        """
        try:
            # Actualizar estado a procesando
            self.archivo_carga.estado = 'PROCESANDO'
            self.archivo_carga.save(update_fields=['estado'])
            
            # Cargar archivo Excel
            self._cargar_excel()
            
            # Validar estructura
            if not self._validar_estructura():
                # Si la estructura es inválida, finalizar con error
                self._finalizar_procesamiento()
                return {
                    'estado': self.archivo_carga.estado,
                    'filas_procesadas': self.registros_procesados,
                    'filas_error': self.registros_error,
                    'errores': self.errores
                }
            
            # Procesar filas
            self._procesar_filas()
            
            # Finalizar procesamiento
            self._finalizar_procesamiento()
            
            return {
                'estado': self.archivo_carga.estado,
                'filas_procesadas': self.registros_procesados,
                'filas_error': self.registros_error,
                'errores': self.errores
            }
            
        except Exception as e:
            self._manejar_error(str(e))
            # Asegurar finalización incluso en errores críticos
            try:
                self._finalizar_procesamiento()
            except:
                pass
            return {
                'estado': 'ERROR',
                'error': str(e),
                'filas_procesadas': self.registros_procesados,
                'filas_error': self.registros_error,
                'errores': self.errores
            }
    
    def _cargar_excel(self):
        """Carga el archivo Excel en un DataFrame de pandas"""
        try:
            # Intentar cargar como xlsx primero, luego xls
            try:
                self.df = pd.read_excel(self.archivo_carga.archivo.path, engine='openpyxl')
            except:
                self.df = pd.read_excel(self.archivo_carga.archivo.path, engine='xlrd')
            
            # Limpiar nombres de columnas (eliminar espacios y convertir a minúsculas)
            self.df.columns = [col.strip().lower().replace(' ', '_') for col in self.df.columns]
            
            # Actualizar total de filas
            self.archivo_carga.filas_totales = len(self.df)
            self.archivo_carga.save(update_fields=['filas_totales'])
            
        except Exception as e:
            raise ValidationError(f"Error al cargar archivo Excel: {str(e)}")
    
    def _procesar_filas(self):
        """Procesa todas las filas del DataFrame"""
        for index, fila in self.df.iterrows():
            try:
                # Convertir fila a diccionario y limpiar valores nulos
                datos_fila = self._limpiar_fila(fila.to_dict())
                
                # Validar fila específica del modelo
                datos_validados = self._validar_fila(datos_fila, index + 2)  # +2 porque Excel empieza en 1 y hay header
                
                if datos_validados:
                    # Procesar fila específica del modelo
                    self._procesar_fila_modelo(datos_validados, index + 2)
                    self.registros_procesados += 1
                else:
                    # Si la validación falló, incrementar contador de errores
                    self.registros_error += 1
                    
            except Exception as e:
                self._agregar_error(index + 2, str(e))
                self.registros_error += 1
            
            # Actualizar progreso cada 10 filas
            if (index + 1) % 10 == 0:
                self.archivo_carga.actualizar_progreso(self.registros_procesados, self.registros_error)
        
        # Actualizar progreso final después de procesar todas las filas
        self.archivo_carga.actualizar_progreso(self.registros_procesados, self.registros_error)
    
    def _limpiar_fila(self, datos: Dict) -> Dict:
        """Limpia y normaliza los datos de una fila"""
        datos_limpios = {}
        for key, value in datos.items():
            if pd.isna(value):
                datos_limpios[key] = None
            elif isinstance(value, str):
                datos_limpios[key] = value.strip()
            else:
                datos_limpios[key] = value
        return datos_limpios
    
    def _agregar_error(self, fila: int, error: str, detalle: Optional[str] = None):
        """Agrega un error a la lista de errores"""
        error_info = {
            'fila': fila,
            'error': error,
        }
        if detalle:
            error_info['detalle'] = detalle
            
        self.errores.append(error_info)
        self.archivo_carga.agregar_error(fila, error, detalle)
    
    def _finalizar_procesamiento(self):
        """Finaliza el procesamiento y actualiza el estado"""
        # Si hay errores estructurales y no se procesó nada
        if not self.archivo_carga.filas_totales and self.errores:
            self.archivo_carga.estado = 'ERROR'
            self.archivo_carga.filas_errores = len(self.errores)
            self.archivo_carga.save(update_fields=['estado', 'filas_errores'])
        else:
            # Procesamiento normal
            self.archivo_carga.actualizar_progreso(self.registros_procesados, self.registros_error)
        
        # Guardar errores en el archivo
        if self.errores:
            self.archivo_carga.errores = self.errores
            self.archivo_carga.save(update_fields=['errores'])
    
    def _manejar_error(self, error: str):
        """Maneja errores globales del procesamiento"""
        self.archivo_carga.estado = 'ERROR'
        self.archivo_carga.agregar_error(0, f"Error global: {error}")
        self.archivo_carga.save(update_fields=['estado'])
    
    # Métodos abstractos que deben implementar las clases hijas
    
    @abstractmethod
    def _validar_estructura(self) -> bool:
        """
        Valida que el archivo tenga la estructura correcta para el modelo
        Debe retornar True si la estructura es válida
        """
        pass
    
    @abstractmethod
    def _validar_fila(self, datos: Dict, numero_fila: int) -> Optional[Dict]:
        """
        Valida los datos de una fila específica
        Debe retornar los datos validados o None si hay errores
        """
        pass
    
    @abstractmethod
    def _procesar_fila_modelo(self, datos: Dict, numero_fila: int):
        """
        Procesa y guarda los datos de una fila en el modelo específico
        """
        pass
    
    @abstractmethod
    def get_columnas_requeridas(self) -> List[str]:
        """
        Retorna la lista de columnas requeridas para el modelo
        """
        pass
    
    @abstractmethod
    def get_columnas_opcionales(self) -> List[str]:
        """
        Retorna la lista de columnas opcionales para el modelo
        """
        pass