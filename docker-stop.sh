#!/bin/bash
# ============================================================================
# DOCKER STOP SCRIPT - STRUCTURAL HEALTH MONITORING SYSTEM
# ============================================================================
# Gracefully stop all services
# ============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                                            ║${NC}"
echo -e "${BLUE}║              STOPPING STRUCTURAL HEALTH MONITORING SYSTEM                  ║${NC}"
echo -e "${BLUE}║                                                                            ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Determine compose command
if docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD="docker-compose"
fi

echo -e "${YELLOW}Stopping services...${NC}"
$COMPOSE_CMD down

echo ""
echo -e "${GREEN}✓ All services stopped${NC}"
echo ""
echo -e "${BLUE}Note:${NC} Your data is preserved in Docker volumes:"
echo -e "  - shm-uploads"
echo -e "  - shm-outputs"
echo -e "  - shm-ml-models"
echo ""
echo -e "${YELLOW}To completely remove everything (including data):${NC}"
echo -e "  docker-compose down -v"
echo ""
