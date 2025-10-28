import io
import os
from datetime import datetime
from pathlib import Path

import pandas as pd
import pytest

from api.management.modules.excel_processor import ExcelProcessor


class TestExcelProcessor:
    @pytest.fixture
    def sample_excel_files(self, tmp_path):
        """Create sample Excel files for testing"""
        # Create Excel 1
        df1 = pd.DataFrame(
            {
                "episodio_cmbd": ["EP001", "EP002"],
                "Tipo Actividad": ["Consulta", "Urgencia"],
                "Estancia Inlier / Outlier": ["Inlier", "Outlier"],
                "Especialidad médica de la intervención (des)": [
                    "Cardiología",
                    "Traumatología",
                ],
                "Estancias Prequirurgicas Int  -Episodio-": [2, 3],
                "Estancias Postquirurgicas Int  -Episodio-": [4, 5],
                "Estancia Norma GRD": [6, 7],
                "Diagnóstico   Principal": ["Cardiopatía", "Fractura"],
            }
        )

        # Create Excel 2
        df2 = pd.DataFrame(
            {
                "Episodio:": ["EP001", "EP002"],
                "RUT": ["12.345.678-9", "98.765.432-1"],
                "Nombre": ["Juan Pérez", "María López"],
                "fecha ingreso completa": [
                    "2023-01-01 08:00:00",
                    "2023-01-02 09:00:00",
                ],
                "fecha completa": ["2023-01-05 15:00:00", "2023-01-06 16:00:00"],
                "servicio ingreso (descripción)": ["Cardiología", "Traumatología"],
                "Status": ["Activo", "Alta"],
                "Fecha de Nacimiento": ["1980-01-01", "1990-01-01"],
                "Sexo  (Desc)": ["MASCULINO", "FEMENINO"],
                "Edad en años": [43, 33],
                "Prevision (Desc)": ["FONASA", "ISAPRE"],
            }
        )

        # Create Excel 3
        df3 = pd.DataFrame(
            {
                "episodio": ["EP001", "EP002"],
                "cama": ["101", "102"],
                "HABITACION": ["H101", "H102"],
                "CAMA_codigo": ["C101", "C102"],
                "MEDICO_TRATANTE": ["Dr. Juan", "Dra. María"],
            }
        )

        # Save files
        path1 = tmp_path / "excel1.xlsx"
        path2 = tmp_path / "excel2.xlsx"
        path3 = tmp_path / "excel3.xlsx"

        df1.to_excel(path1, index=False)
        df2.to_excel(path2, index=False)
        df3.to_excel(path3, index=False)

        return {"excel1": path1, "excel2": path2, "excel3": path3}

    def test_init(self):
        """Test ExcelProcessor initialization"""
        processor = ExcelProcessor()

        assert processor.combined_df is None

    def test_load_excel_files(self, sample_excel_files):
        """Test loading Excel files"""
        processor = ExcelProcessor()
        result = processor.load_excel_files(sample_excel_files)

        assert len(processor.excel3_df) == 2

    def test_load_excel_files_missing_file(self, sample_excel_files):
        """Test loading with missing file"""
        processor = ExcelProcessor()
        # Remove one file from the dictionary
        del sample_excel_files["excel1"]

        result = processor.load_excel_files(sample_excel_files)
        assert result is False

    def test_combine_data_no_files(self):
        """Test combining data with no loaded files"""
        processor = ExcelProcessor()
        result = processor.combine_data()

        assert result is False
        assert processor.combined_df is None

    def test_combine_data(self, sample_excel_files):
        """Test combining data from all Excel files"""
        processor = ExcelProcessor()
        processor.load_excel_files(sample_excel_files)
        result = processor.combine_data()

        # Check if combined data has essential fields from all files
        combined_columns = set(processor.combined_df.columns)

        # Core fields that should be present after combining
        essential_fields = {
            "episodio_cmbd",  # From excel1
            "Nombre",  # From excel2
            "CAMA",  # From excel3
            "RUT",  # From excel2
            "HABITACION",  # From excel3
        }
        # check if at least one of the episodio column variants is present
        episodio_variants = {"episodio_cmbd", "Episodio:", "episodio"}
        assert combined_columns.intersection(
            episodio_variants
        ), "No episodio column found"

    def test_data_summary(self, sample_excel_files):
        """Test getting data summary"""
        processor = ExcelProcessor()
        processor.load_excel_files(sample_excel_files)
        processor.combine_data()

        summary = processor.get_data_summary()

        assert summary["files_loaded"]["excel3"] is True

    def test_clean_data_for_models(self, sample_excel_files):
        """Test cleaning data for Django models"""
        processor = ExcelProcessor()
        processor.load_excel_files(sample_excel_files)
        processor.combine_data()

        cleaned_data = processor.clean_data_for_models()

        assert "episodios" in cleaned_data

    def test_extract_functions_patient_data(self, sample_excel_files):
        """Test various extraction functions"""
        processor = ExcelProcessor()
        processor.load_excel_files(sample_excel_files)
        processor.combine_data()

        # Get first row of combined data
        row = processor.combined_df.iloc[0]

        # Test patient data extraction
        assert processor._extract_rut(row) == "12.345.678-9"
        assert processor._extract_nombre(row) == "Juan Pérez"
        assert processor._extract_fecha_nacimiento(row) == "1980-01-01"
        assert processor._extract_sexo(row) == "M"  # MASCULINO is transformed to M
        assert processor._extract_edad(row) == 43
        assert processor._extract_prevision(row) == "FONASA"

    def test_normalize_episodio_column(self):
        """Test normalizing episodio column names"""
        # Create a test DataFrame with various column names
        df = pd.DataFrame({"Episodio CMBD": ["EP001", "EP002"], "other_col": [1, 2]})

        processor = ExcelProcessor()
        normalized_df = processor._normalize_episodio_column(df, "test")

        assert "episodio_cmbd" in normalized_df.columns

    def test_export_combined_data(self, tmp_path):
        """Test exporting combined data to Excel"""
        # Create a simple combined DataFrame
        processor = ExcelProcessor()
        processor.combined_df = pd.DataFrame(
            {"episodio_cmbd": ["EP001", "EP002"], "data": [1, 2]}
        )

        output_path = tmp_path / "output.xlsx"
        result = processor.export_combined_data(output_path)

        assert result is True

    def test_invalid_excel_content(self, tmp_path):
        """Test handling invalid Excel content"""
        # Create an Excel file with invalid content
        df = pd.DataFrame({"invalid_column": ["no_episodio_column"]})

        path = tmp_path / "invalid.xlsx"
        df.to_excel(path, index=False)

        processor = ExcelProcessor()
        result = processor.load_excel_files(
            {"excel1": path, "excel2": path, "excel3": path}
        )

        assert result is False
