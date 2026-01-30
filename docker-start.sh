#!/bin/bash
# ============================================================================
# DOCKER DEPLOYMENT SCRIPT - STRUCTURAL HEALTH MONITORING SYSTEM
# ============================================================================
# One-command deployment script for production use
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print banner
print_banner() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                                                                            ║${NC}"
    echo -e "${BLUE}║         STRUCTURAL HEALTH MONITORING SYSTEM - DOCKER DEPLOYMENT            ║${NC}"
    echo -e "${BLUE}║                                                                            ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# Check if Docker is installed and running
check_docker() {
    echo -e "${YELLOW}[1/7]${NC} Checking Docker installation..."
    
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}✗ Docker is not installed!${NC}"
        echo "Please install Docker: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        echo -e "${RED}✗ Docker is not running!${NC}"
        echo "Please start Docker and try again."
        exit 1
    fi
    
    echo -e "${GREEN}✓ Docker is installed and running${NC}"
}

# Check if docker-compose is available
check_docker_compose() {
    echo -e "${YELLOW}[2/7]${NC} Checking Docker Compose..."
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        echo -e "${RED}✗ Docker Compose is not installed!${NC}"
        echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Docker Compose is available${NC}"
}

# Check system resources
check_resources() {
    echo -e "${YELLOW}[3/7]${NC} Checking system resources..."
    
    # Check available disk space (need at least 5GB)
    available_space=$(df -BG . | tail -1 | awk '{print $4}' | sed 's/G//')
    
    if [ "$available_space" -lt 5 ]; then
        echo -e "${RED}✗ Insufficient disk space: ${available_space}GB available (need 5GB minimum)${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ System resources OK (${available_space}GB available)${NC}"
}

# Stop any existing containers
stop_existing() {
    echo -e "${YELLOW}[4/7]${NC} Stopping existing containers..."
    
    if docker ps -a | grep -q "shm-"; then
        docker-compose down 2>/dev/null || docker compose down 2>/dev/null || true
        echo -e "${GREEN}✓ Stopped existing containers${NC}"
    else
        echo -e "${GREEN}✓ No existing containers to stop${NC}"
    fi
}

# Build and start containers
start_containers() {
    echo -e "${YELLOW}[5/7]${NC} Building Docker images (this may take 5-10 minutes)..."
    
    # Use docker compose (newer) or docker-compose (older)
    if docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
    else
        COMPOSE_CMD="docker-compose"
    fi
    
    echo -e "${BLUE}Building images...${NC}"
    $COMPOSE_CMD build --no-cache
    
    echo -e "${YELLOW}[6/7]${NC} Starting containers..."
    $COMPOSE_CMD up -d
    
    echo -e "${GREEN}✓ Containers started${NC}"
}

# Wait for services to be healthy
wait_for_services() {
    echo -e "${YELLOW}[7/7]${NC} Waiting for services to be healthy..."
    
    max_attempts=60
    attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        backend_health=$(docker inspect --format='{{.State.Health.Status}}' shm-backend 2>/dev/null || echo "starting")
        frontend_health=$(docker inspect --format='{{.State.Health.Status}}' shm-frontend 2>/dev/null || echo "starting")
        
        if [ "$backend_health" = "healthy" ] && [ "$frontend_health" = "healthy" ]; then
            echo -e "${GREEN}✓ All services are healthy!${NC}"
            break
        fi
        
        echo -ne "${BLUE}Waiting... (${attempt}/${max_attempts}) Backend: ${backend_health}, Frontend: ${frontend_health}${NC}\r"
        sleep 2
        attempt=$((attempt + 1))
    done
    
    if [ $attempt -eq $max_attempts ]; then
        echo -e "${RED}✗ Services did not become healthy in time${NC}"
        echo "Check logs with: docker-compose logs"
        exit 1
    fi
}

# Print success message and access information
print_success() {
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                                                                            ║${NC}"
    echo -e "${GREEN}║                    🎉  DEPLOYMENT SUCCESSFUL!  🎉                          ║${NC}"
    echo -e "${GREEN}║                                                                            ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BLUE}Access your application:${NC}"
    echo ""
    echo -e "  ${GREEN}Frontend UI:${NC}      http://localhost:3000"
    echo -e "  ${GREEN}Backend API:${NC}      http://localhost:8000"
    echo -e "  ${GREEN}API Docs:${NC}         http://localhost:8000/docs"
    echo -e "  ${GREEN}Health Check:${NC}     http://localhost:8000/health"
    echo ""
    echo -e "${BLUE}Useful commands:${NC}"
    echo ""
    echo -e "  ${YELLOW}View logs:${NC}        docker-compose logs -f"
    echo -e "  ${YELLOW}Stop services:${NC}    docker-compose down"
    echo -e "  ${YELLOW}Restart:${NC}          docker-compose restart"
    echo -e "  ${YELLOW}Check status:${NC}     docker-compose ps"
    echo -e "  ${YELLOW}View volumes:${NC}     docker volume ls | grep shm"
    echo ""
    echo -e "${BLUE}Data persistence:${NC}"
    echo ""
    echo -e "  ${GREEN}Uploads:${NC}          Docker volume 'shm-uploads'"
    echo -e "  ${GREEN}Outputs:${NC}          Docker volume 'shm-outputs'"
    echo -e "  ${GREEN}ML Models:${NC}        Docker volume 'shm-ml-models'"
    echo ""
    echo -e "${YELLOW}Note:${NC} Your data is persisted in Docker volumes and will survive container restarts."
    echo ""
}

# Main execution
main() {
    print_banner
    check_docker
    check_docker_compose
    check_resources
    stop_existing
    start_containers
    wait_for_services
    print_success
}

# Run main function
main
