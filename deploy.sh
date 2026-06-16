#!/bin/bash
set -euo pipefail

# ─────────────────────────────────────────────────────────────
# Dormtel App - Hostinger VPS Deployment Script
# Usage: bash deploy.sh [setup|deploy|status|logs|stop]
# ─────────────────────────────────────────────────────────────

PROJECT_DIR="/opt/dormtel"
COMPOSE_FILE="docker-compose.prod.yml"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()   { echo -e "${GREEN}[DORMTEL]${NC} $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

check_prerequisites() {
    command -v docker >/dev/null 2>&1 || error "Docker is not installed"
    command -v docker compose >/dev/null 2>&1 || error "Docker Compose is not installed"
    log "Docker $(docker --version | awk '{print $3}') found"
    log "Docker Compose $(docker compose version --short) found"
}

setup() {
    log "Setting up Dormtel on this VPS..."
    check_prerequisites

    # Create project directory
    sudo mkdir -p "$PROJECT_DIR"
    sudo chown "$(whoami)":"$(whoami)" "$PROJECT_DIR"

    log "Project directory created at $PROJECT_DIR"
    log ""
    log "Next steps:"
    log "  1. Copy project files to $PROJECT_DIR"
    log "  2. Copy .env.production.example to $PROJECT_DIR/.env"
    log "  3. Edit .env with your production values"
    log "  4. Run: bash deploy.sh deploy"
}

deploy() {
    log "Deploying Dormtel..."
    check_prerequisites

    cd "$PROJECT_DIR"

    if [ ! -f .env ]; then
        error ".env file not found. Copy .env.production.example to .env and fill in values."
    fi

    # Validate required env vars
    source .env
    [ -z "${POSTGRES_PASSWORD:-}" ] && error "POSTGRES_PASSWORD not set in .env"
    [ -z "${SECRET_KEY:-}" ] && error "SECRET_KEY not set in .env"
    [ "${POSTGRES_PASSWORD}" = "CHANGE_ME_STRONG_PASSWORD_HERE" ] && error "Change POSTGRES_PASSWORD from default!"
    [ "${SECRET_KEY}" = "CHANGE_ME_GENERATE_A_STRONG_KEY" ] && error "Change SECRET_KEY from default!"

    log "Building containers..."
    docker compose -f "$COMPOSE_FILE" build --no-cache

    log "Starting services..."
    docker compose -f "$COMPOSE_FILE" up -d

    log "Waiting for services to be healthy..."
    sleep 10

    # Health check
    if curl -sf http://localhost/health > /dev/null 2>&1; then
        log "API is healthy!"
    else
        warn "API health check failed. Checking logs..."
        docker compose -f "$COMPOSE_FILE" logs --tail=20 api
    fi

    log ""
    log "Deployment complete!"
    log "  Frontend: http://$(hostname -I | awk '{print $1}')"
    log "  API Docs: http://$(hostname -I | awk '{print $1}')/docs"
    log "  Health:   http://$(hostname -I | awk '{print $1}')/health"
}

status() {
    cd "$PROJECT_DIR" 2>/dev/null || error "Project not found at $PROJECT_DIR"
    docker compose -f "$COMPOSE_FILE" ps
}

logs() {
    cd "$PROJECT_DIR" 2>/dev/null || error "Project not found at $PROJECT_DIR"
    docker compose -f "$COMPOSE_FILE" logs -f --tail=50
}

stop() {
    cd "$PROJECT_DIR" 2>/dev/null || error "Project not found at $PROJECT_DIR"
    log "Stopping Dormtel..."
    docker compose -f "$COMPOSE_FILE" down
    log "Stopped."
}

case "${1:-}" in
    setup)  setup ;;
    deploy) deploy ;;
    status) status ;;
    logs)   logs ;;
    stop)   stop ;;
    *)
        echo "Dormtel VPS Deployment Script"
        echo ""
        echo "Usage: bash deploy.sh <command>"
        echo ""
        echo "Commands:"
        echo "  setup   - Initial VPS setup (create directories)"
        echo "  deploy  - Build and deploy the application"
        echo "  status  - Show running containers"
        echo "  logs    - Tail container logs"
        echo "  stop    - Stop all containers"
        ;;
esac
