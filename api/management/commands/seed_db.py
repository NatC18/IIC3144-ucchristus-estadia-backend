"""
Management command para poblar la base de datos con datos de prueba
Uso: python manage.py seed_db
"""

from django.core.management.base import BaseCommand

from api.seeds.camas import create_camas
from api.seeds.episodios_gestiones import create_episodios_y_gestiones
from api.seeds.pacientes import create_pacientes
from api.seeds.users import create_users
from api.seeds.servicios import create_servicios


class Command(BaseCommand):
    help = "Pobla la base de datos con datos de prueba para UCChristus"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Fuerza la recreación de datos (elimina datos existentes)",
        )
        parser.add_argument(
            "--only",
            type=str,
            choices=["users", "pacientes", "camas", "episodios"],
            help="Solo ejecuta seeds específicos",
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS("\n🌱 Iniciando proceso de seeds para UCChristus\n")
        )

        if options["force"]:
            self.stdout.write(
                self.style.WARNING(
                    "⚠️  Modo force activado - se recrearán datos existentes"
                )
            )
            # Aquí podrías agregar lógica para limpiar la base de datos

        try:
            # Removemos transaction.atomic() por problemas con foreign keys
            if options["only"]:
                self._run_specific_seed(options["only"])
            else:
                self._run_all_seeds()

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"\n❌ Error durante la ejecución de seeds: {str(e)}")
            )
            raise

        self.stdout.write(self.style.SUCCESS("\n✅ Seeds ejecutados exitosamente!"))
        self.stdout.write(
            self.style.SUCCESS("🎉 Base de datos poblada con datos de prueba\n")
        )

    def _run_all_seeds(self):
        """Ejecuta todos los seeds en el orden correcto"""
        self.stdout.write("📝 Ejecutando todos los seeds...\n")

        # Orden importante: usuarios y pacientes primero, luego camas, finalmente episodios
        create_users()
        self.stdout.write("")

        create_pacientes()
        self.stdout.write("")

        create_camas()
        self.stdout.write("")

        create_episodios_y_gestiones()
        self.stdout.write("")

        create_servicios()
        self.stdout.write("")

    def _run_specific_seed(self, seed_type):
        """Ejecuta un seed específico"""
        self.stdout.write(f"📝 Ejecutando seed específico: {seed_type}\n")

        if seed_type == "users":
            create_users()
        elif seed_type == "pacientes":
            create_pacientes()
        elif seed_type == "camas":
            create_camas()
        elif seed_type == "episodios":
            create_episodios_y_gestiones()
        elif seed_type == "servicios":
            create_servicios()

        self.stdout.write("")
