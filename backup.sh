#!/bin/bash

# Cargar las variables de entorno desde el archivo .env
if [ -f .env ]; then
  source .env
else
  echo "Archivo .env no encontrado."
  exit 1
fi

# Obtener el nombre de la rama actual de Git
BRANCH_NAME=$(git rev-parse --abbrev-ref HEAD)

# Generar un timestamp en formato YYYYmmddHHMMSS
TIMESTAMP=$(date +%Y%m%d%H%M%S)

# Definir el nombre del archivo de respaldo
BACKUP_FILE="backup_${BRANCH_NAME}_${TIMESTAMP}.sql"

# Exportar la contraseña para pg_dump (PostgreSQL)
export PGPASSWORD="$DB_PASSWORD"

# Crear el dump de la base de datos PostgreSQL
pg_dump \
  --host="$DB_HOST" \
  --port="$DB_PORT" \
  --username="$DB_USER" \
  --dbname="$DB_NAME" \
  --file="$BACKUP_FILE"

# Verificar si el dump se realizó correctamente
if [ $? -eq 0 ]; then
  echo "Backup creado: $BACKUP_FILE"
  git add "$BACKUP_FILE"
  git commit -m "Backup de la BD para la rama $BRANCH_NAME ($TIMESTAMP)"
else
  echo "Error: no se pudo generar el backup de la base de datos."
  exit 1
fi
