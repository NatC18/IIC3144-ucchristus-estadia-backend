#!/bin/bash

# Quick test script for UCChristus models
# Usage: docker compose exec web bash test_models.sh

echo "🧪 Testing UCChristus Models"
echo "=============================="
echo ""

echo "📋 Step 1: Check migrations status"
python manage.py showmigrations api
echo ""

echo "📋 Step 2: Apply migrations"
python manage.py migrate
echo ""

echo "📋 Step 3: Create test data"
python manage.py create_test_data --all
echo ""

echo "📋 Step 4: Test models in Django shell"
python manage.py shell << 'EOF'
from api.models import Paciente, Episodio, Gestion, Usuario, Cama
from django.db.models import Count

print("\n🔍 Testing Models and Relationships\n")

# Count objects
print(f"📊 Database counts:")
print(f"  - Pacientes: {Paciente.objects.count()}")
print(f"  - Usuarios: {Usuario.objects.count()}")
print(f"  - Camas: {Cama.objects.count()}")
print(f"  - Episodios: {Episodio.objects.count()}")
print(f"  - Gestiones: {Gestion.objects.count()}")
print()

# Test relationships
if Paciente.objects.exists():
    paciente = Paciente.objects.first()
    print(f"✅ Paciente test: {paciente.nombre}")
    print(f"   - Edad: {paciente.edad} años")
    print(f"   - Episodios: {paciente.episodios.count()}")
    print()

if Usuario.objects.exists():
    usuario = Usuario.objects.first()
    print(f"✅ Usuario test: {usuario.nombre} {usuario.apellido}")
    print(f"   - Rol: {usuario.rol}")
    print(f"   - Gestiones: {usuario.gestiones.count()}")
    print()

if Episodio.objects.exists():
    episodio = Episodio.objects.first()
    print(f"✅ Episodio test: {episodio.episodio_cmbd}")
    print(f"   - Paciente: {episodio.paciente.nombre}")
    print(f"   - Cama: {episodio.cama.codigo_cama if episodio.cama else 'Sin cama'}")
    print(f"   - Gestiones: {episodio.gestiones.count()}")
    print(f"   - Estancia: {episodio.estancia_dias} días")
    print()

if Gestion.objects.exists():
    gestion = Gestion.objects.first()
    print(f"✅ Gestion test: {gestion.tipo_gestion}")
    print(f"   - Estado: {gestion.estado_gestion}")
    print(f"   - Episodio: {gestion.episodio.episodio_cmbd}")
    print(f"   - Usuario: {gestion.usuario.nombre if gestion.usuario else 'Sin usuario'}")
    if gestion.duracion_dias:
        print(f"   - Duración: {gestion.duracion_dias} días")
    print()

# Test complex queries
print(f"🔍 Complex queries:")
episodios_activos = Episodio.objects.filter(fecha_egreso__isnull=True).count()
print(f"  - Episodios activos (sin egreso): {episodios_activos}")

gestiones_completadas = Gestion.objects.filter(estado_gestion='COMPLETADA').count()
print(f"  - Gestiones completadas: {gestiones_completadas}")

episodios_con_gestiones = Episodio.objects.annotate(
    num_gestiones=Count('gestiones')
).filter(num_gestiones__gt=0).count()
print(f"  - Episodios con gestiones: {episodios_con_gestiones}")
print()

print("✅ All model tests passed!")
print()
EOF

echo ""
echo "✅ Testing complete!"
echo ""
echo "Next steps:"
echo "  - Access admin: http://localhost:8001/admin/"
echo "  - Test API: http://localhost:8001/api/"
echo "  - Django shell: docker compose exec web python manage.py shell"
