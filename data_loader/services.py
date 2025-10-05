import pandas as pd
import json
from django.utils import timezone
from django.core.exceptions import ValidationError
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


class ExcelProcessor:
    """Clase para procesar archivos Excel"""
    
    def __init__(self, excel_upload):
        self.excel_upload = excel_upload
        self.df = None
    
    def process_file(self) -> Dict:
        """
        Procesa el archivo Excel y extrae datos para preview
        Returns: Diccionario con datos procesados y estadísticas
        """
        try:
            # Actualizar status
            self.excel_upload.status = 'processing'
            self.excel_upload.save()
            
            # Leer archivo Excel
            self.df = pd.read_excel(
                self.excel_upload.file.path,
                engine='openpyxl' if self.excel_upload.file.name.endswith('.xlsx') else 'xlrd'
            )
            
            # Procesar datos
            result = self._extract_data()
            
            # Guardar resultados
            self.excel_upload.status = 'processed'
            self.excel_upload.total_rows = len(self.df)
            self.excel_upload.processed_rows = result['valid_rows']
            self.excel_upload.error_rows = result['error_rows'] 
            self.excel_upload.headers = result['headers']
            self.excel_upload.preview_data = result['preview_data']
            self.excel_upload.error_log = result['errors']
            self.excel_upload.processed_at = timezone.now()
            self.excel_upload.save()
            
            logger.info(f"Processed Excel file: {self.excel_upload.original_filename}")
            return result
            
        except Exception as e:
            self.excel_upload.status = 'error'
            self.excel_upload.error_log = {'general_error': str(e)}
            self.excel_upload.save()
            logger.error(f"Error processing Excel: {str(e)}")
            raise ValidationError(f"Error procesando archivo Excel: {str(e)}")
    
    def _extract_data(self) -> Dict:
        """Extrae y valida datos del DataFrame"""
        
        # Limpiar DataFrame
        self.df = self.df.dropna(how='all')  # Eliminar filas completamente vacías
        
        # Obtener headers
        headers = self.df.columns.tolist()
        
        # Convertir a JSON serializable
        preview_data = []
        errors = []
        valid_rows = 0
        error_rows = 0
        
        # Procesar cada fila (máximo 100 para preview)
        max_preview = min(len(self.df), 100)
        
        for idx, row in self.df.head(max_preview).iterrows():
            try:
                # Convertir valores pandas/numpy a tipos Python nativos
                row_data = []
                for col in headers:
                    try:
                        value = row[col]
                        
                        # Manejar diferentes tipos de datos de forma segura
                        if pd.isna(value) or value is None:
                            clean_value = None
                        elif isinstance(value, pd.Timestamp):
                            clean_value = str(value) if not pd.isna(value) else None
                        elif hasattr(value, 'strftime'):
                            # Para objetos datetime
                            clean_value = str(value)
                        elif isinstance(value, (int, float)):
                            clean_value = float(value) if not pd.isna(value) else None
                        else:
                            clean_value = str(value)
                            
                        row_data.append(clean_value)
                    except Exception:
                        row_data.append(str(value) if value is not None else None)
                
                preview_data.append(row_data)
                valid_rows += 1
                
            except Exception as e:
                errors.append({
                    'row': int(idx) + 2,
                    'error': str(e)
                })
                # Añadir fila vacía en caso de error
                preview_data.append(['ERROR'] + [''] * (len(headers) - 1))
                error_rows += 1
        
        return {
            'success': True,
            'headers': headers,
            'preview_data': {'preview_data': preview_data},
            'total_rows': len(self.df),
            'rows_processed': valid_rows,
            'valid_rows': valid_rows,
            'error_rows': error_rows,
            'errors': errors,
            'stats': {
                'columns': len(headers),
                'total_rows': len(self.df),
                'preview_rows': len(preview_data),
                'success_rate': round((valid_rows / len(self.df)) * 100, 1) if len(self.df) > 0 else 0
            }
        }
    
    def get_column_info(self) -> List[Dict]:
        """Obtiene información detallada de cada columna"""
        if self.df is None:
            return []
        
        column_info = []
        for col in self.df.columns:
            col_data = self.df[col]
            
            info = {
                'name': col,
                'dtype': str(col_data.dtype),
                'null_count': int(col_data.isnull().sum()),
                'unique_count': int(col_data.nunique()),
                'sample_values': col_data.dropna().head(3).tolist()
            }
            
            # Información específica por tipo
            if col_data.dtype in ['int64', 'float64']:
                info['min_value'] = float(col_data.min()) if not col_data.empty else None
                info['max_value'] = float(col_data.max()) if not col_data.empty else None
                info['mean_value'] = float(col_data.mean()) if not col_data.empty else None
            
            column_info.append(info)
        
        return column_info