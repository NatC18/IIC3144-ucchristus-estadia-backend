"""
Comando de Django para importar datos desde archivos Excel locales
Simula la funcionalidad de OneDrive pero utilizando archivos del sistema local
"""

import logging
import os

import pandas as pd
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from api.management.modules.data_mapper import DataMapper
from api.management.modules.db_importer import DatabaseImporter
from api.management.modules.excel_processor import ExcelProcessor

# Configurar logging
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Importa datos desde archivos Excel locales (excel1.xlsx, excel2.xlsx, excel3.xlsx, excel4.xlsx)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--folder",
            type=str,
            default="excel_files",
            help="Carpeta donde están los archivos Excel (relativa al proyecto o ruta absoluta)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Simula la importación sin guardar datos en la base de datos",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Mostrar información detallada del proceso",
        )
        parser.add_argument(
            "--export-combined",
            type=str,
            help="Exportar datos combinados a un archivo Excel (ej: --export-combined combined_data.xlsx)",
        )
        parser.add_argument(
            "--list-files",
            action="store_true",
            help="Listar archivos Excel encontrados en la carpeta",
        )

    def handle(self, *args, **options):
        self.verbosity = 2 if options["verbose"] else 1

        try:
            # Determinar la ruta de la carpeta
            folder_path = self._get_folder_path(options["folder"])

            if options["list_files"]:
                self._list_excel_files(folder_path)
                return

            # Verificar que existen los archivos necesarios
            excel_files = self._check_excel_files(folder_path)

            if self.verbosity >= 2:
                self.stdout.write(f"📂 Carpeta de archivos: {folder_path}")
                self.stdout.write(
                    f"📊 Archivos encontrados: {list(excel_files.keys())}"
                )

            # Procesar archivos Excel
            self.stdout.write("🔄 Procesando archivos Excel...")
            excel_processor = ExcelProcessor()
            processed_data = excel_processor.process_local_files(excel_files)

            if self.verbosity >= 2:
                total_records = sum(len(df) for df in processed_data.values())
                self.stdout.write(f"📈 Registros procesados: {total_records}")
                for model_name, df in processed_data.items():
                    self.stdout.write(f"  📋 {model_name}: {len(df)} registros")

            # Exportar datos combinados si se solicita
            if options["export_combined"]:
                export_path = options["export_combined"]
                # Combinar todos los DataFrames para exportar
                all_data = pd.concat(
                    [
                        df.assign(tipo_datos=model_name)
                        for model_name, df in processed_data.items()
                    ],
                    ignore_index=True,
                )
                all_data.to_excel(export_path, index=False)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ Datos procesados exportados a: {export_path}"
                    )
                )

            # Mapear datos para Django
            self.stdout.write("🗺️  Mapeando datos para Django...")
            data_mapper = DataMapper()
            mapped_data = data_mapper.map_processed_data(processed_data)

            if self.verbosity >= 2:
                pacientes_count = len(mapped_data["pacientes"])
                episodios_count = len(mapped_data["episodios"])
                gestiones_count = len(mapped_data["gestiones"])

                self.stdout.write(f"👥 Pacientes a procesar: {pacientes_count}")
                self.stdout.write(f"📝 Episodios a procesar: {episodios_count}")
                self.stdout.write(f"💼 Gestiones a procesar: {gestiones_count}")

            # Importar a la base de datos (o simular)
            if options["dry_run"]:
                self.stdout.write("🧪 MODO DRY-RUN: Simulando importación...")
                self._simulate_import(mapped_data)
            else:
                self.stdout.write("💾 Importando datos a la base de datos...")
                db_importer = DatabaseImporter()
                results = db_importer.import_data(mapped_data)

                # Verificar si hay errores antes de mostrar resultados
                if "details" not in results:
                    raise CommandError(f"Error en estructura de resultados: {results}")

                self._show_import_results(results["details"])

            self.stdout.write(self.style.SUCCESS("✅ Proceso completado exitosamente!"))

        except Exception as e:
            logger.error(f"Error en la importación: {str(e)}")
            raise CommandError(f"Error: {str(e)}")

    def _get_folder_path(self, folder_input):
        """Determina la ruta absoluta de la carpeta"""
        if os.path.isabs(folder_input):
            folder_path = folder_input
        else:
            # Ruta relativa al directorio del proyecto
            project_root = settings.BASE_DIR
            folder_path = os.path.join(project_root, folder_input)

        if not os.path.exists(folder_path):
            raise CommandError(f"La carpeta no existe: {folder_path}")

        return folder_path

    def _check_excel_files(self, folder_path):
        """Verifica que existen los archivos Excel necesarios"""
        required_files = ["excel1.xlsx", "excel2.xlsx", "excel3.xlsx", "excel4.xlsx"]
        excel_files = {}

        for filename in required_files:
            file_path = os.path.join(folder_path, filename)
            if not os.path.exists(file_path):
                # Buscar archivos con extensiones alternativas
                alt_path = os.path.join(folder_path, filename.replace(".xlsx", ".xls"))
                if os.path.exists(alt_path):
                    file_path = alt_path
                else:
                    raise CommandError(
                        f"Archivo no encontrado: {filename} en {folder_path}"
                    )

            excel_files[filename.replace(".xlsx", "").replace(".xls", "")] = file_path

        return excel_files

    def _list_excel_files(self, folder_path):
        """Lista archivos Excel en la carpeta"""
        self.stdout.write(f"📂 Archivos en: {folder_path}")

        excel_extensions = [".xlsx", ".xls"]
        excel_files = []

        for file in os.listdir(folder_path):
            if any(file.lower().endswith(ext) for ext in excel_extensions):
                file_path = os.path.join(folder_path, file)
                file_size = os.path.getsize(file_path)
                excel_files.append((file, file_size))

        if excel_files:
            self.stdout.write("📊 Archivos Excel encontrados:")
            for filename, size in excel_files:
                size_mb = size / (1024 * 1024)
                self.stdout.write(f"  📄 {filename} ({size_mb:.2f} MB)")
        else:
            self.stdout.write("❌ No se encontraron archivos Excel")

        # Verificar archivos requeridos
        required_files = [
            "excel1.xlsx",
            "excel2.xlsx",
            "excel3.xlsx",
            "excel4.xlsx",
            "excel1.xls",
            "excel2.xls",
            "excel3.xls",
            "excel4.xls",
        ]
        found_required = [f for f, _ in excel_files if f in required_files]

        if found_required:
            self.stdout.write("\n✅ Archivos requeridos encontrados:")
            for filename in found_required:
                self.stdout.write(f"  ✓ {filename}")
        else:
            self.stdout.write(
                "\n⚠️  Archivos requeridos (excel1, excel2, excel3, excel4) no encontrados"
            )

    def _simulate_import(self, mapped_data):
        """Simula la importación mostrando estadísticas"""
        self.stdout.write("📊 Simulación de importación:")

        pacientes = mapped_data["pacientes"]
        episodios = mapped_data["episodios"]
        gestiones = mapped_data["gestiones"]

        self.stdout.write(f"  👥 Pacientes: {len(pacientes)} registros")
        if pacientes and self.verbosity >= 2:
            sample_patient = pacientes[0]
            self.stdout.write(
                f"    📋 Ejemplo: RUT {sample_patient.get('rut', 'N/A')}, "
                f"Nombre {sample_patient.get('nombre', 'N/A')}"
            )

        self.stdout.write(f"  📝 Episodios: {len(episodios)} registros")
        if episodios and self.verbosity >= 2:
            sample_episode = episodios[0]
            self.stdout.write(
                f"    📋 Ejemplo: CMBD {sample_episode.get('episodio_cmbd', 'N/A')}"
            )

        self.stdout.write(f"  💼 Gestiones: {len(gestiones)} registros")
        if gestiones and self.verbosity >= 2:
            sample_gestion = gestiones[0]
            self.stdout.write(
                f"    📋 Ejemplo: Fecha {sample_gestion.get('fecha_ingreso', 'N/A')}"
            )

        self.stdout.write("🧪 Modo DRY-RUN: No se guardaron datos en la base de datos")

    def _show_import_results(self, results):
        """Muestra los resultados de la importación"""
        self.stdout.write("📊 Resultados de la importación:")

        # Pacientes
        p_created = results["pacientes"]["created"]
        p_updated = results["pacientes"]["updated"]
        p_errors = results["pacientes"]["errors"]

        self.stdout.write(
            f"  👥 Pacientes: {p_created} creados, {p_updated} actualizados"
        )
        if p_errors > 0:
            self.stdout.write(f"    ❌ Errores: {p_errors}")

        # Episodios
        e_created = results["episodios"]["created"]
        e_updated = results["episodios"]["updated"]
        e_errors = results["episodios"]["errors"]

        self.stdout.write(
            f"  📝 Episodios: {e_created} creados, {e_updated} actualizados"
        )
        if e_errors > 0:
            self.stdout.write(f"    ❌ Errores: {e_errors}")
            # Mostrar primeros errores de episodios
            if "errors" in results and len(results["errors"]) > 0:
                self.stdout.write("    📋 Primeros errores:")
                for error in results["errors"][:5]:  # Mostrar solo los primeros 5
                    self.stdout.write(f"      - {error}")

        # Gestiones
        g_created = results["gestiones"]["created"]
        g_updated = results["gestiones"]["updated"]
        g_errors = results["gestiones"]["errors"]

        self.stdout.write(
            f"  💼 Gestiones: {g_created} creadas, {g_updated} actualizadas"
        )
        if g_errors > 0:
            self.stdout.write(f"    ❌ Errores: {g_errors}")

        total_created = p_created + e_created + g_created
        total_updated = p_updated + e_updated + g_updated
        total_errors = p_errors + e_errors + g_errors

        self.stdout.write(
            f"\n📈 Total: {total_created} creados, {total_updated} actualizados"
        )
        if total_errors > 0:
            self.stdout.write(f"❌ Total errores: {total_errors}")
        else:
            self.stdout.write("✅ Sin errores")
