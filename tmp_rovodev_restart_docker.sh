#!/bin/bash
# Restart Docker containers with ML456 volume mounted

echo "🔄 Restarting Docker containers with ML456 models..."
echo ""

echo "1️⃣ Stopping containers..."
sudo docker compose down

echo ""
echo "2️⃣ Starting containers with new configuration..."
sudo docker compose up -d

echo ""
echo "3️⃣ Waiting for services to be healthy..."
sleep 5

echo ""
echo "4️⃣ Checking container status..."
sudo docker compose ps

echo ""
echo "5️⃣ Verifying ML456 is accessible in container..."
sudo docker compose exec backend ls -la /home/itachi/ml456_advanced/checkpoints/advanced/ 2>&1 | head -5

echo ""
echo "6️⃣ Checking backend logs..."
sudo docker compose logs --tail=30 backend | grep -E "ml456|ML456|predictor|loaded"

echo ""
echo "✅ Done! Test the ML Baseline Prediction in the UI now."
