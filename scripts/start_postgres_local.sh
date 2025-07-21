#!/bin/bash
# PostgreSQL Homebrew Service Manager for macOS with project DB/user auto-setup
# Usage: ./start_postgres_local.sh [start|stop|restart|status]
# Default: start and ensure DB/user

SERVICE="postgresql@15"

# Load environment variables from .env.local or .env safely
if [ -f .env.local ]; then
  set -a
  source .env.local
  set +a
elif [ -f .env ]; then
  set -a
  source .env
  set +a
fi

PG_DB="${POSTGRES_DB:-dev_rag}"
PG_USER="${POSTGRES_USER:-devuser}"
PG_PASS="${POSTGRES_PASSWORD:-devpass}"
PG_PORT="${POSTGRES_PORT:-5432}"

function status() {
  brew services list | grep "$SERVICE"
  if command -v pg_isready >/dev/null 2>&1; then
    pg_isready -p "$PG_PORT"
    if [ $? -eq 0 ]; then
      echo "PostgreSQL ($SERVICE) is running and accepting connections."
    else
      echo "PostgreSQL ($SERVICE) is NOT accepting connections."
    fi
  else
    echo "[ERROR] pg_isready not found. Please install postgresql client tools (brew install libpq && brew link --force libpq)."
  fi
}

function ensure_current_user_db() {
  CURRENT_USER=$(whoami)
  if ! command -v psql >/dev/null 2>&1; then
    echo "[ERROR] psql not found. Please install postgresql client tools (brew install libpq && brew link --force libpq)."
    return 1
  fi
  # Try to connect to current user's DB, if fails, try to create it
  psql -U "$CURRENT_USER" -p "$PG_PORT" -d "$CURRENT_USER" -c "\q" 2>/dev/null
  if [ $? -ne 0 ]; then
    echo "Database '$CURRENT_USER' does not exist. Creating..."
    createdb -U "$CURRENT_USER" -p "$PG_PORT" "$CURRENT_USER" 2>/dev/null
    if [ $? -eq 0 ]; then
      echo "Database '$CURRENT_USER' created."
    else
      echo "[ERROR] Could not create database '$CURRENT_USER'. Please create it manually."
      return 1
    fi
  fi
  return 0
}

function ensure_postgres_superuser() {
  if ! command -v psql >/dev/null 2>&1; then
    echo "[ERROR] psql not found. Please install postgresql client tools (brew install libpq && brew link --force libpq)."
    return 1
  fi
  # Try to connect as postgres, if fails, try to create it
  psql -U postgres -p "$PG_PORT" -c "\q" 2>/dev/null
  if [ $? -ne 0 ]; then
    echo "Superuser 'postgres' does not exist. Attempting to create..."
    CURRENT_USER=$(whoami)
    ensure_current_user_db || return 1
    psql -U "$CURRENT_USER" -p "$PG_PORT" -d "$CURRENT_USER" -tc "SELECT 1 FROM pg_roles WHERE rolname='postgres'" | grep -q 1 || \
      psql -U "$CURRENT_USER" -p "$PG_PORT" -d "$CURRENT_USER" -c "CREATE USER postgres WITH SUPERUSER CREATEDB CREATEROLE LOGIN;"
    if [ $? -eq 0 ]; then
      echo "Superuser 'postgres' created."
    else
      echo "[ERROR] Could not create 'postgres' superuser. Please create it manually."
      return 1
    fi
  fi
  return 0
}

function ensure_db_and_user() {
  if ! command -v psql >/dev/null 2>&1; then
    echo "[ERROR] psql not found. Please install postgresql client tools (brew install libpq && brew link --force libpq)."
    return
  fi
  ensure_postgres_superuser || return
  echo "Ensuring PostgreSQL user '$PG_USER' and database '$PG_DB' exist..."
  # Create user if not exists
  psql -U postgres -p "$PG_PORT" -tc "SELECT 1 FROM pg_roles WHERE rolname='$PG_USER'" | grep -q 1 || \
    psql -U postgres -p "$PG_PORT" -c "CREATE USER $PG_USER WITH PASSWORD '$PG_PASS';"
  # Create database if not exists
  psql -U postgres -p "$PG_PORT" -tc "SELECT 1 FROM pg_database WHERE datname='$PG_DB'" | grep -q 1 || \
    psql -U postgres -p "$PG_PORT" -c "CREATE DATABASE $PG_DB OWNER $PG_USER;"
  # Grant privileges
  psql -U postgres -p "$PG_PORT" -c "GRANT ALL PRIVILEGES ON DATABASE $PG_DB TO $PG_USER;"
  echo "User and database ready."
}

function start() {
  echo "Starting PostgreSQL ($SERVICE) via Homebrew..."
  brew services start $SERVICE
  sleep 2
  status
  ensure_db_and_user
}

function stop() {
  echo "Stopping PostgreSQL ($SERVICE) via Homebrew..."
  brew services stop $SERVICE
  sleep 2
  status
}

function restart() {
  echo "Restarting PostgreSQL ($SERVICE) via Homebrew..."
  brew services restart $SERVICE
  sleep 2
  status
  ensure_db_and_user
}

case "$1" in
  start|"" )
    start
    ;;
  stop)
    stop
    ;;
  restart)
    restart
    ;;
  status)
    status
    ;;
  *)
    echo "Usage: $0 [start|stop|restart|status]"
    exit 1
    ;;
esac 