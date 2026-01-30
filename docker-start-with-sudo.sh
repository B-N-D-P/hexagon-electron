#!/bin/bash
# ============================================================================
# DOCKER DEPLOYMENT SCRIPT - WITH SUDO SUPPORT
# ============================================================================
# Handles cases where user needs sudo for Docker commands
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check if we need sudo for Docker
DOCKER_CMD="docker"
if ! docker ps >/dev/null 2>&1; then
    if sudo docker ps >/dev/null 2>&1; then
        DOCKER_CMD="sudo docker"
        COMPOSE_CMD="sudo docker-compose"
        echo -e "${YELLOW}Note: Using sudo for Docker commands${NC}"
    else
        echo -e "${RED}✗ Cannot access Docker even with sudo${NC}"
        exit 1
    fi
else
    COMPOSE_CMD="docker-compose"
fi

# Check if docker-compose exists
if ! command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="$DOCKER_CMD compose"
fi

print_banner() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                                                                            ║${NC}"
    echo -e "${BLUE}║         STRUCTURAL HEALTH MONITORING SYSTEM - DOCKER DEPLOYMENT            ║${NC}"
    echo -e "${BLUE}║                                                                            ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

check_docker() {
    echo -e "${YELLOW}[1/7]${NC} Checking Docker installation..."
    
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}✗ Docker is not installed!${NC}"
        echo "Please install Docker: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    if ! $DOCKER_CMD info &> /dev/null; then
        echo -e "${RED}✗ Docker is not accessible!${NC}"
        echo "Try: sudo systemctl start docker"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Docker is installed and running${NC}"
}

check_docker_compose() {
    echo -e "${YELLOW}[2/7]${NC} Checking Docker Compose..."
    
    if ! command -v docker-compose &> /dev/null && ! $DOCKER_CMD compose version &> /dev/null; then
        echo -e "${RED}✗ Docker Compose is not installed!${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Docker Compose is available${NC}"
}

check_resources() {
    echo -e "${YELLOW}[3/7]${NC} Checking system resources..."
    
    available_space=$(df -BG . | tail -1 | awk '{print $4}' | sed 's/G//')
    
    if [ "$available_space" -lt 5 ]; then
        echo -e "${RED}✗ Insufficient disk space: ${available_space}GB available (need 5GB minimum)${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ System resources OK (${available_space}GB available)${NC}"
}

stop_existing() {
    echo -e "${YELLOW}[4/7]${NC} Stopping existing containers..."
    
    if $DOCKER_CMD ps -a | grep -q "shm-"; then
        $COMPOSE_CMD down 2>/dev/null || true
        echo -e "${GREEN}✓ Stopped existing containers${NC}"
    else
        echo -e "${GREEN}✓ No existing containers to stop${NC}"
    fi
}

start_containers() {
    echo -e "${YELLOW}[5/7]${NC} Building Docker images (this may take 5-10 minutes)..."
    
    echo -e "${BLUE}Building images...${NC}"
    $COMPOSE_CMD build --no-cache
    
    echo -e "${YELLOW}[6/7]${NC} Starting containers..."
    $COMPOSE_CMD up -d
    
    echo -e "${GREEN}✓ Containers started${NC}"
}

wait_for_services() {
    echo -e "${YELLOW}[7/7]${NC} Waiting for services to be healthy..."
    
    max_attempts=60
    attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        backend_health=$($DOCKER_CMD inspect --format='{{.State.Health.Status}}' shm-backend 2>/dev/null || echo "starting")
        frontend_health=$($DOCKER_CMD inspect --format='{{.State.Health.Status}}' shm-frontend 2>/dev/null || echo "starting")
        
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
        echo "Check logs with: $COMPOSE_CMD logs"
        exit 1
    fi
}

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
    echo -e "  ${YELLOW}View logs:${NC}        $COMPOSE_CMD logs -f"
    echo -e "  ${YELLOW}Stop services:${NC}    $COMPOSE_CMD down"
    echo -e "  ${YELLOW}Restart:${NC}          $COMPOSE_CMD restart"
    echo -e "  ${YELLOW}Check status:${NC}     $COMPOSE_CMD ps"
    echo ""
    
    if [ "$DOCKER_CMD" = "sudo docker" ]; then
        echo -e "${YELLOW}Note: You're using sudo for Docker. To avoid this in the future:${NC}"
        echo -e "  sudo usermod -aG docker \$USER"
        echo -e "  Then logout and login again"
        echo ""
    fi
}

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

main
