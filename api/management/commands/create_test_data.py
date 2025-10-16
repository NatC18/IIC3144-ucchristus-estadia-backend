"""
Comando para crear datos de prueba
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from api.models import Paciente
from datetime import date


class Command(BaseCommand):
    help = 'Crea datos de prueba para el sistema'

    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            action='store_true',
            help='Crear usuarios de prueba',
        )
        parser.add_argument(
            '--pacientes',
            action='store_true',
            help='Crear pacientes de prueba',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Crear todos los datos de prueba',
        )

    def handle(self, *args, **options):
        if options['all'] or options['users']:
            self.create_users()
        
        if options['all'] or options['pacientes']:
            self.create_pacientes()

    def create_users(self):
        """Crear usuarios de prueba"""
        self.stdout.write('Creando usuarios de prueba...')
        
        # Superusuario
        if not User.objects.filter(username='admin').exists():
            admin = User.objects.create_superuser(
                username='admin',
                email='admin@ucchristus.cl',
                password='admin123',
                first_name='Administrador',
                last_name='Sistema'
            )
            Token.objects.create(user=admin)
            self.stdout.write(
                self.style.SUCCESS(f'✓ Superusuario creado: admin/admin123')
            )
        
        # Usuario regular
        if not User.objects.filter(username='medico').exists():
            medico = User.objects.create_user(
                username='medico',
                email='medico@ucchristus.cl',
                password='medico123',
                first_name='Dr. Juan',
                last_name='Pérez'
            )
            Token.objects.create(user=medico)
            self.stdout.write(
                self.style.SUCCESS(f'✓ Usuario creado: medico/medico123')
            )

    def create_pacientes(self):
        """Crear pacientes de prueba"""
        self.stdout.write('Creando pacientes de prueba...')
        
        pacientes_data = [
            {
                'rut': '12.345.678-5',
                'nombre': 'Juan Pérez García',
                'sexo': 'M',
                'fecha_nacimiento': date(1980, 5, 15),
                'prevision': 'FONASA',
                'convenio': 'Urgencia',
                'score_social': 85
            },
            {
                'rut': '98.765.432-5',
                'nombre': 'María González López',
                'sexo': 'F',
                'fecha_nacimiento': date(1995, 8, 22),
                'prevision': 'ISAPRE',
                'convenio': 'Consulta General',
                'score_social': 92
            },
            {
                'rut': '11.111.111-1',
                'nombre': 'Carlos Rodríguez Silva',
                'sexo': 'M',
                'fecha_nacimiento': date(1975, 12, 3),
                'prevision': 'PARTICULAR',
                'convenio': 'Especialidad',
                'score_social': 78
            },
            {
                'rut': '22.222.222-2',
                'nombre': 'Ana Martínez Torres',
                'sexo': 'F',
                'fecha_nacimiento': date(1988, 3, 10),
                'prevision': 'FONASA',
                'convenio': 'Medicina General',
                'score_social': 88
            },
            {
                'rut': '33.333.333-3',
                'nombre': 'Luis Hernández Vega',
                'sexo': 'M',
                'fecha_nacimiento': date(1992, 7, 25),
                'prevision': 'ISAPRE',
                'convenio': 'Cardiología',
                'score_social': 95
            }
        ]
        
        created_count = 0
        for paciente_data in pacientes_data:
            paciente, created = Paciente.objects.get_or_create(
                rut=paciente_data['rut'],
                defaults=paciente_data
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Paciente creado: {paciente.nombre}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Total de pacientes creados: {created_count}')
        )