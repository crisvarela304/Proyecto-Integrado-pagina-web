#!/bin/bash
# =============================================================================
# Entrypoint inteligente para Schoolar OS
# Ejecuta: wait_db → migrate → collectstatic → generate_school_code → gunicorn
# =============================================================================

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Iniciando Schoolar OS...${NC}"

# =============================================================================
# Función: Esperar a que PostgreSQL esté listo
# =============================================================================
wait_for_db() {
    echo -e "${YELLOW}🔍 Esperando a que PostgreSQL esté listo...${NC}"
    
    while ! pg_isready -h ${DB_HOST:-postgres} -p ${DB_PORT:-5432} -U ${DB_USER:-schoolar_user} > /dev/null 2>&1; do
        echo "   PostgreSQL no está listo, esperando 2 segundos..."
        sleep 2
    done
    
    echo -e "${GREEN}✅ PostgreSQL está listo!${NC}"
}

# =============================================================================
# Función: Ejecutar migraciones
# =============================================================================
run_migrations() {
    echo -e "${YELLOW}🔄 Ejecutando migraciones de base de datos...${NC}"
    python manage.py migrate --noinput
    echo -e "${GREEN}✅ Migraciones completadas!${NC}"
}

# =============================================================================
# Función: Recolectar archivos estáticos
# =============================================================================
collect_static() {
    echo -e "${YELLOW}📦 Recolectando archivos estáticos...${NC}"
    python manage.py collectstatic --noinput --clear
    echo -e "${GREEN}✅ Archivos estáticos listos!${NC}"
}

# =============================================================================
# Función: Generar/verificar código del colegio (Phone Home)
# =============================================================================
setup_school_code() {
    echo -e "${YELLOW}🏫 Verificando código del colegio...${NC}"
    
    # Ejecutar el command que genera o muestra el código
    python manage.py generate_school_code \
        ${COLEGIO_NOMBRE:+--nombre "$COLEGIO_NOMBRE"} \
        ${COLEGIO_URL:+--url "$COLEGIO_URL"}
    
    echo -e "${GREEN}✅ Código del colegio configurado!${NC}"
}

# =============================================================================
# Función: Crear superusuario si no existe
# =============================================================================
create_superuser() {
    if [ "$CREATE_SUPERUSER" = "true" ]; then
        echo -e "${YELLOW}👤 Verificando superusuario...${NC}"
        
        python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@schoolar.os', '${SUPERUSER_PASSWORD:-admin123}')
    print('✅ Superusuario creado: admin')
else:
    print('ℹ️  Superusuario ya existe')
EOF
    fi
}

# =============================================================================
# Main: Ejecutar secuencia de inicialización
# =============================================================================
main() {
    wait_for_db
    run_migrations
    collect_static
    setup_school_code
    create_superuser
    
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}🎉 Schoolar OS listo para producción!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    
    # Iniciar Gunicorn
    echo -e "${YELLOW}🚀 Iniciando servidor Gunicorn...${NC}"
    exec gunicorn config.wsgi:application \
        --bind 0.0.0.0:8000 \
        --workers ${GUNICORN_WORKERS:-4} \
        --worker-class sync \
        --worker-tmp-dir /tmp \
        --max-requests 1000 \
        --max-requests-jitter 100 \
        --timeout 30 \
        --keep-alive 2 \
        --access-logfile - \
        --error-logfile - \
        --log-level info
}

# Ejecutar
main "$@"
