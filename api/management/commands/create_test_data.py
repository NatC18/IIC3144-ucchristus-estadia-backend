"""
Comando para crear datos de prueba
"""

from datetime import date

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from rest_framework.authtoken.models import Token
from api.models import Paciente, Episodio, Gestion, Usuario, Cama, Servicio
from datetime import date, datetime, timedelta
import uuid


class Command(BaseCommand):
    help = "Crea datos de prueba para el sistema"

    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            action='store_true',
            help='Crear usuarios de prueba (Django auth)',
        )
        parser.add_argument(
            '--usuarios',
            action='store_true',
            help='Crear usuarios del sistema',
        )
        parser.add_argument(
            '--pacientes',
            action='store_true',
            help='Crear pacientes de prueba',
        )
        parser.add_argument(
            '--camas',
            action='store_true',
            help='Crear camas y servicios',
        )
        parser.add_argument(
            '--episodios',
            action='store_true',
            help='Crear episodios de prueba',
        )
        parser.add_argument(
            '--gestiones',
            action='store_true',
            help='Crear gestiones de prueba',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Crear todos los datos de prueba',
        )

    def handle(self, *args, **options):
        if options["all"] or options["users"]:
            self.create_users()
        
        if options['all'] or options['usuarios']:
            self.create_usuarios()
        
        if options['all'] or options['pacientes']:
            self.create_pacientes()
        
        if options['all'] or options['camas']:
            self.create_camas()
        
        if options['all'] or options['episodios']:
            self.create_episodios()
        
        if options['all'] or options['gestiones']:
            self.create_gestiones()

    def create_users(self):
        """Crear usuarios de prueba"""
        self.stdout.write("Creando usuarios de prueba...")

        # Superusuario
        if not User.objects.filter(username="admin").exists():
            admin = User.objects.create_superuser(
                username="admin",
                email="admin@ucchristus.cl",
                password="admin123",
                first_name="Administrador",
                last_name="Sistema",
            )
            Token.objects.create(user=admin)
            self.stdout.write(
                self.style.SUCCESS(f"✓ Superusuario creado: admin/admin123")
            )

        # Usuario regular
        if not User.objects.filter(username="medico").exists():
            medico = User.objects.create_user(
                username="medico",
                email="medico@ucchristus.cl",
                password="medico123",
                first_name="Dr. Juan",
                last_name="Pérez",
            )
            Token.objects.create(user=medico)
            self.stdout.write(
                self.style.SUCCESS(f'✓ Usuario creado: medico/medico123')
            )

    def create_usuarios(self):
        """Crear usuarios del sistema de prueba"""
        self.stdout.write('Creando usuarios del sistema...')
        
        usuarios_data = [
            {
                'rut': '15.555.555-5',
                'nombre': 'Dr. Juan',
                'apellido': 'Pérez',
                'rol': 'Médico',
                'mail': 'juan.perez@ucchristus.cl',
                'contrasena': 'hashed_password_123'
            },
            {
                'rut': '16.666.666-6',
                'nombre': 'Dra. María',
                'apellido': 'González',
                'rol': 'Médico',
                'mail': 'maria.gonzalez@ucchristus.cl',
                'contrasena': 'hashed_password_456'
            },
            {
                'rut': '17.777.777-7',
                'nombre': 'Enf. Carlos',
                'apellido': 'López',
                'rol': 'Enfermero',
                'mail': 'carlos.lopez@ucchristus.cl',
                'contrasena': 'hashed_password_789'
            }
        ]
        
        created_count = 0
        for usuario_data in usuarios_data:
            usuario, created = Usuario.objects.get_or_create(
                rut=usuario_data['rut'],
                defaults=usuario_data
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Usuario creado: {usuario.nombre} {usuario.apellido}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Total de usuarios creados: {created_count}')
        )

    def create_pacientes(self):
        """Crear pacientes de prueba"""
        self.stdout.write("Creando pacientes de prueba...")

        pacientes_data = [
            {
                'rut': '12.345.678-5',
                'nombre': 'Juan Pérez García',
                'sexo': 'M',
                'fecha_nacimiento': date(1980, 5, 15),
                'prevision_1': 'FONASA',
                'convenio': 'Urgencia',
                'score_social': 85
            },
            {
                'rut': '98.765.432-5',
                'nombre': 'María González López',
                'sexo': 'F',
                'fecha_nacimiento': date(1995, 8, 22),
                'prevision_1': 'ISAPRE',
                'convenio': 'Consulta General',
                'score_social': 92
            },
            {
                'rut': '11.111.111-1',
                'nombre': 'Carlos Rodríguez Silva',
                'sexo': 'M',
                'fecha_nacimiento': date(1975, 12, 3),
                'prevision_1': 'PARTICULAR',
                'prevision_2': 'FONASA',
                'convenio': 'Especialidad',
                'score_social': 78
            },
            {
                'rut': '22.222.222-2',
                'nombre': 'Ana Martínez Torres',
                'sexo': 'F',
                'fecha_nacimiento': date(1988, 3, 10),
                'prevision_1': 'FONASA',
                'convenio': 'Medicina General',
                'score_social': 88
            },
            {
                'rut': '33.333.333-3',
                'nombre': 'Luis Hernández Vega',
                'sexo': 'M',
                'fecha_nacimiento': date(1992, 7, 25),
                'prevision_1': 'ISAPRE',
                'convenio': 'Cardiología',
                'score_social': 95
            }
        ]

        created_count = 0
        for paciente_data in pacientes_data:
            paciente, created = Paciente.objects.get_or_create(
                rut=paciente_data["rut"], defaults=paciente_data
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"✓ Paciente creado: {paciente.nombre}")
                )

        self.stdout.write(
            self.style.SUCCESS(f"Total de pacientes creados: {created_count}")
        )

    def create_camas(self):
        """Crear camas y servicios de prueba"""
        self.stdout.write('Creando camas de prueba...')
        
        camas_data = [
            {'codigo_cama': 'UCI-101', 'habitacion': 'UCI'},
            {'codigo_cama': 'UCI-102', 'habitacion': 'UCI'},
            {'codigo_cama': 'MED-201', 'habitacion': 'Medicina Interna'},
            {'codigo_cama': 'MED-202', 'habitacion': 'Medicina Interna'},
            {'codigo_cama': 'CIR-301', 'habitacion': 'Cirugía'},
        ]
        
        created_count = 0
        for cama_data in camas_data:
            cama, created = Cama.objects.get_or_create(
                codigo_cama=cama_data['codigo_cama'],
                defaults=cama_data
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Cama creada: {cama.codigo_cama}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Total de camas creadas: {created_count}')
        )

    def create_episodios(self):
        """Crear episodios de prueba"""
        self.stdout.write('Creando episodios de prueba...')
        
        # Get existing data
        pacientes = list(Paciente.objects.all()[:3])
        camas = list(Cama.objects.filter(estado='OCUPADA')[:3])
        
        if not pacientes:
            self.stdout.write(
                self.style.WARNING('⚠ No hay pacientes. Ejecuta --pacientes primero.')
            )
            return
        
        if not camas:
            self.stdout.write(
                self.style.WARNING('⚠ No hay camas. Usando None para camas.')
            )
            camas = [None] * 3
        
        episodios_data = [
            {
                'paciente': pacientes[0],
                'cama': camas[0] if camas[0] else None,
                'episodio_cmbd': 10001,
                'fecha_ingreso': datetime.now() - timedelta(days=5),
                'tipo_actividad': 'Hospitalización',
                'especialidad': 'Medicina Interna',
                'estancia_prequirurgica': 2.0,
                'estancia_postquirurgica': 3.0,
            },
            {
                'paciente': pacientes[1] if len(pacientes) > 1 else pacientes[0],
                'cama': camas[1] if len(camas) > 1 and camas[1] else None,
                'episodio_cmbd': 10002,
                'fecha_ingreso': datetime.now() - timedelta(days=3),
                'tipo_actividad': 'Urgencia',
                'especialidad': 'UCI',
                'estancia_prequirurgica': 0.0,
                'estancia_postquirurgica': 1.0,
            },
            {
                'paciente': pacientes[2] if len(pacientes) > 2 else pacientes[0],
                'cama': camas[2] if len(camas) > 2 and camas[2] else None,
                'episodio_cmbd': 10003,
                'fecha_ingreso': datetime.now() - timedelta(days=10),
                'fecha_egreso': datetime.now() - timedelta(days=2),
                'tipo_actividad': 'Hospitalización',
                'especialidad': 'Cirugía',
                'estancia_prequirurgica': 1.0,
                'estancia_postquirurgica': 7.0,
            }
        ]
        
        created_count = 0
        for episodio_data in episodios_data:
            # Check if episodio already exists
            exists = Episodio.objects.filter(
                episodio_cmbd=episodio_data['episodio_cmbd']
            ).exists()
            
            if not exists:
                episodio = Episodio.objects.create(**episodio_data)
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Episodio creado: {episodio.episodio_cmbd} - {episodio.paciente.nombre}'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Total de episodios creados: {created_count}')
        )

    def create_gestiones(self):
        """Crear gestiones de prueba"""
        self.stdout.write('Creando gestiones de prueba...')
        
        # Get existing data
        episodios = list(Episodio.objects.all()[:3])
        usuarios = list(Usuario.objects.all()[:2])
        
        if not episodios:
            self.stdout.write(
                self.style.WARNING('⚠ No hay episodios. Ejecuta --episodios primero.')
            )
            return
        
        if not usuarios:
            self.stdout.write(
                self.style.WARNING('⚠ No hay usuarios. Ejecuta --usuarios primero.')
            )
            return
        
        gestiones_data = [
            {
                'episodio': episodios[0],
                'usuario': usuarios[0],
                'tipo_gestion': 'HOMECARE_UCCC',
                'estado_gestion': 'EN_PROGRESO',
                'fecha_inicio': datetime.now() - timedelta(days=4),
                'informe': 'Gestión de homecare en progreso para paciente de medicina interna'
            },
            {
                'episodio': episodios[1] if len(episodios) > 1 else episodios[0],
                'usuario': usuarios[1] if len(usuarios) > 1 else usuarios[0],
                'tipo_gestion': 'COBERTURA',
                'estado_gestion': 'COMPLETADA',
                'fecha_inicio': datetime.now() - timedelta(days=2),
                'fecha_fin': datetime.now() - timedelta(days=1),
                'informe': 'Cobertura verificada y autorizada'
            },
            {
                'episodio': episodios[2] if len(episodios) > 2 else episodios[0],
                'usuario': usuarios[0],
                'tipo_gestion': 'TRASLADO',
                'estado_gestion': 'INICIADA',
                'fecha_inicio': datetime.now() - timedelta(hours=6),
                'informe': 'Solicitud de traslado iniciada'
            }
        ]
        
        created_count = 0
        for gestion_data in gestiones_data:
            # Check if similar gestion exists
            exists = Gestion.objects.filter(
                episodio=gestion_data['episodio'],
                tipo_gestion=gestion_data['tipo_gestion']
            ).exists()
            
            if not exists:
                gestion = Gestion.objects.create(**gestion_data)
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Gestion creada: {gestion.tipo_gestion} - {gestion.estado_gestion}'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Total de gestiones creadas: {created_count}')
        )