# ============================================================================
# MAKEFILE - STRUCTURAL HEALTH MONITORING SYSTEM
# ============================================================================
# Convenient shortcuts for Docker operations
# ============================================================================

.PHONY: help build start stop restart logs status clean backup test

# Default target
help:
	@echo "╔════════════════════════════════════════════════════════════════════════════╗"
	@echo "║                                                                            ║"
	@echo "║         STRUCTURAL HEALTH MONITORING - DOCKER COMMANDS                     ║"
	@echo "║                                                                            ║"
	@echo "╚════════════════════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "Available commands:"
	@echo ""
	@echo "  make start          - Start all services (builds if needed)"
	@echo "  make stop           - Stop all services"
	@echo "  make restart        - Restart all services"
	@echo "  make logs           - View logs (all services)"
	@echo "  make status         - Check service status"
	@echo "  make build          - Build/rebuild images"
	@echo "  make clean          - Remove containers and images"
	@echo "  make clean-all      - Remove everything including volumes"
	@echo "  make backup         - Backup all data volumes"
	@echo "  make test           - Test the deployment"
	@echo ""
	@echo "Quick start: make start"
	@echo ""

# Build images
build:
	@echo "🔨 Building Docker images..."
	docker-compose build --no-cache

# Start services
start:
	@echo "🚀 Starting services..."
	@./docker-start.sh || docker-compose up -d

# Stop services
stop:
	@echo "🛑 Stopping services..."
	@./docker-stop.sh || docker-compose down

# Restart services
restart:
	@echo "🔄 Restarting services..."
	docker-compose restart

# View logs
logs:
	@echo "📋 Viewing logs (Ctrl+C to exit)..."
	docker-compose logs -f

# Check status
status:
	@echo "📊 Service Status:"
	@docker-compose ps
	@echo ""
	@echo "🏥 Health Checks:"
	@curl -s http://localhost:8000/health | python3 -m json.tool 2>/dev/null || echo "Backend not responding"

# Clean containers and images
clean:
	@echo "🧹 Cleaning containers and images..."
	docker-compose down
	docker rmi structural-health-monitoring-backend:latest || true
	docker rmi structural-health-monitoring-frontend:latest || true

# Clean everything including volumes
clean-all:
	@echo "⚠️  WARNING: This will delete all data!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose down -v; \
		docker volume rm shm-uploads shm-outputs shm-ml-models || true; \
	fi

# Backup volumes
backup:
	@echo "💾 Backing up data volumes..."
	@mkdir -p backups
	@DATE=$$(date +%Y%m%d_%H%M%S); \
	docker run --rm -v shm-uploads:/data -v $$(pwd)/backups:/backup alpine \
		tar czf /backup/uploads-$$DATE.tar.gz -C /data . && \
	docker run --rm -v shm-outputs:/data -v $$(pwd)/backups:/backup alpine \
		tar czf /backup/outputs-$$DATE.tar.gz -C /data . && \
	docker run --rm -v shm-ml-models:/data -v $$(pwd)/backups:/backup alpine \
		tar czf /backup/ml-models-$$DATE.tar.gz -C /data . && \
	echo "✓ Backups created in ./backups/" || echo "✗ Backup failed"

# Test deployment
test:
	@echo "🧪 Testing deployment..."
	@echo ""
	@echo "1. Checking Docker..."
	@docker info > /dev/null && echo "   ✓ Docker is running" || echo "   ✗ Docker is not running"
	@echo ""
	@echo "2. Checking containers..."
	@docker ps | grep -q shm-backend && echo "   ✓ Backend container running" || echo "   ✗ Backend not running"
	@docker ps | grep -q shm-frontend && echo "   ✓ Frontend container running" || echo "   ✗ Frontend not running"
	@echo ""
	@echo "3. Checking health..."
	@curl -sf http://localhost:8000/health > /dev/null && echo "   ✓ Backend healthy" || echo "   ✗ Backend unhealthy"
	@curl -sf http://localhost:3000 > /dev/null && echo "   ✓ Frontend accessible" || echo "   ✗ Frontend not accessible"
	@echo ""
	@echo "4. Checking volumes..."
	@docker volume ls | grep -q shm-uploads && echo "   ✓ Uploads volume exists" || echo "   ✗ Uploads volume missing"
	@docker volume ls | grep -q shm-outputs && echo "   ✓ Outputs volume exists" || echo "   ✗ Outputs volume missing"
	@docker volume ls | grep -q shm-ml-models && echo "   ✓ ML models volume exists" || echo "   ✗ ML models volume missing"
	@echo ""
