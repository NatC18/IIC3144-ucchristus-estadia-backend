# UCChristus Backend

Backend API para el sistema de gestión hospitalaria UCChristus desarrollado con Django Rest Framework.

## 🚀 Inicio Rápido

### Prerrequisitos
- Docker y Docker Compose

### 1. Levantar el Servicio

```bash
# Clonar repositorio
git clone <repository-url>
cd IIC3144-ucchristus-estadia-backend

# Levantar contenedores
docker compose up -d

# Verificar que está funcionando
docker compose ps
```

El servicio estará disponible en: **http://localhost:8001**

### 2. Poblar la Base de Datos

```bash
# Ejecutar migraciones
docker compose exec web python manage.py migrate

# Poblar con datos de prueba
docker compose exec web python manage.py seed_db
```

### 3. Acceso al Sistema

**Panel de Administración:** http://localhost:8001/admin
- Usuario: `admin@ucchristus.cl`
- Contraseña: `admin123`

**API:** http://localhost:8001/api/

## 🛠️ Comandos Útiles

```bash
# Ver logs
docker compose logs -f web

# Acceder al contenedor
docker compose exec web bash

# Verificar linting
bash check-linting.sh

# Correr tests coverage
bash docker-compose run --rm web ./run-tests.sh
```
## 🏥 Tecnologías

- Django 5.2.7
- Django Rest Framework
- PostgreSQL 15
- Docker Compose
- JWT Authentication