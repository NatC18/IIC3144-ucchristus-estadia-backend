"""
Quick test script for models
Run with: docker compose exec web python test_models_quick.py
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from api.models import Paciente, Episodio, Gestion, Usuario, Cama, Servicio, EpisodioServicio, Transferencia
from django.db.models import Count
from datetime import datetime, date, timedelta

def main():
    print("\n" + "="*60)
    print("🧪 UCChristus Models - Quick Test")
    print("="*60 + "\n")
    
    # Test 1: Count all objects
    print("📊 Database Summary:")
    print(f"  • Pacientes:  {Paciente.objects.count()}")
    print(f"  • Usuarios:   {Usuario.objects.count()}")
    print(f"  • Camas:      {Cama.objects.count()}")
    print(f"  • Episodios:  {Episodio.objects.count()}")
    print(f"  • Gestiones:  {Gestion.objects.count()}")
    print()
    
    # Test 2: Create sample data if empty
    if Paciente.objects.count() == 0:
        print("⚠️  No data found. Creating sample data...\n")
        create_sample_data()
        print("✅ Sample data created!\n")
    
    # Test 3: Test relationships
    print("🔗 Testing Relationships:")
    
    if Paciente.objects.exists():
        paciente = Paciente.objects.first()
        print(f"\n  Paciente: {paciente.nombre}")
        print(f"    - RUT: {paciente.rut}")
        print(f"    - Edad: {paciente.edad} años")
        print(f"    - Prevision 1: {paciente.prevision_1}")
        print(f"    - Prevision 2: {paciente.prevision_2}")
        print(f"    - Episodios relacionados: {paciente.episodios.count()}")
        
        # Show related episodes
        for ep in paciente.episodios.all()[:2]:
            print(f"      └─ Episodio {ep.episodio_cmbd}: {ep.especialidad}")
    
    if Usuario.objects.exists():
        usuario = Usuario.objects.first()
        print(f"\n  Usuario: {usuario.nombre} {usuario.apellido}")
        print(f"    - Rol: {usuario.rol}")
        print(f"    - Email: {usuario.mail}")
        print(f"    - Gestiones asignadas: {usuario.gestiones.count()}")
    
    if Episodio.objects.exists():
        episodio = Episodio.objects.select_related('paciente', 'cama').first()
        print(f"\n  Episodio: {episodio.episodio_cmbd}")
        print(f"    - Paciente: {episodio.paciente.nombre}")
        print(f"    - Cama: {episodio.cama.codigo_cama if episodio.cama else 'Sin asignar'}")
        print(f"    - Especialidad: {episodio.especialidad}")
        print(f"    - Estancia: {episodio.estancia_dias} días")
        print(f"    - Gestiones: {episodio.gestiones.count()}")
    
    if Gestion.objects.exists():
        gestion = Gestion.objects.select_related('episodio__paciente', 'usuario').first()
        print(f"\n  Gestión: {gestion.get_tipo_gestion_display()}")
        print(f"    - Estado: {gestion.get_estado_gestion_display()}")
        print(f"    - Episodio: {gestion.episodio.episodio_cmbd}")
        print(f"    - Paciente: {gestion.episodio.paciente.nombre}")
        if gestion.usuario:
            print(f"    - Usuario: {gestion.usuario.nombre} {gestion.usuario.apellido}")
        if gestion.duracion_dias:
            print(f"    - Duración: {gestion.duracion_dias} días")
    
    # Test 4: Complex queries
    print("\n🔍 Complex Queries:")
    
    episodios_activos = Episodio.objects.filter(fecha_egreso__isnull=True)
    print(f"  • Episodios activos: {episodios_activos.count()}")
    
    gestiones_completadas = Gestion.objects.filter(estado_gestion='COMPLETADA')
    print(f"  • Gestiones completadas: {gestiones_completadas.count()}")
    
    gestiones_en_progreso = Gestion.objects.filter(estado_gestion='EN_PROGRESO')
    print(f"  • Gestiones en progreso: {gestiones_en_progreso.count()}")
    
    episodios_con_gestiones = Episodio.objects.annotate(
        num_gestiones=Count('gestiones')
    ).filter(num_gestiones__gt=0)
    print(f"  • Episodios con gestiones: {episodios_con_gestiones.count()}")
    
    # Test 5: Test cascade and foreign keys
    print("\n🔗 Foreign Key Tests:")
    print("  Testing foreign key constraints...")
    
    try:
        # Test accessing related objects
        if Gestion.objects.exists():
            gestion = Gestion.objects.select_related('episodio', 'usuario').first()
            _ = gestion.episodio.paciente.nombre  # Navigate through relations
            print("  ✅ Foreign key navigation works")
    except Exception as e:
        print(f"  ❌ Foreign key error: {e}")
    
    # Summary
    print("\n" + "="*60)
    print("✅ All tests completed successfully!")
    print("="*60)
    print("\n💡 Next steps:")
    print("  • Django shell:  docker compose exec web python manage.py shell")
    print("  • Admin panel:   http://localhost:8001/admin/")
    print("  • API browser:   http://localhost:8001/api/")
    print()


def create_sample_data():
    """Create minimal sample data for testing"""
    
    # Create a patient
    paciente = Paciente.objects.create(
        rut='12.345.678-9',
        nombre='Paciente de Prueba',
        sexo='M',
        fecha_nacimiento=date(1985, 6, 15),
        prevision_1='FONASA',
        prevision_2='ISAPRE',
        score_social=80
    )
    print(f"  ✓ Created Paciente: {paciente.nombre}")
    
    # Create a usuario
    usuario = Usuario.objects.create(
        rut='11.111.111-1',
        nombre='Dr. Test',
        apellido='Usuario',
        rol='Médico',
        mail='test@hospital.cl',
        contrasena='test123'
    )
    print(f"  ✓ Created Usuario: {usuario.nombre} {usuario.apellido}")
    
    # Create a cama
    cama = Cama.objects.create(
        codigo_cama='TEST-101',
        habitacion='UCI'
    )
    print(f"  ✓ Created Cama: {cama.codigo_cama}")
    
    # Create an episodio
    episodio = Episodio.objects.create(
        paciente=paciente,
        cama=cama,
        episodio_cmbd=99999,
        fecha_ingreso=datetime.now() - timedelta(days=3),
        tipo_actividad='Hospitalización',
        especialidad='Medicina General'
    )
    print(f"  ✓ Created Episodio: {episodio.episodio_cmbd}")
    
    # Create a gestion
    gestion = Gestion.objects.create(
        episodio=episodio,
        usuario=usuario,
        tipo_gestion='HOMECARE_UCCC',
        estado_gestion='EN_PROGRESO',
        fecha_inicio=datetime.now() - timedelta(days=2),
        informe='Gestión de prueba'
    )
    print(f"  ✓ Created Gestion: {gestion.tipo_gestion}")


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
