#!/bin/bash
# Rebuild and restart the backend with the file persistence fix

echo "🔨 Rebuilding backend container..."
sudo docker compose build backend

echo ""
echo "🔄 Restarting services..."
sudo docker compose up -d

echo ""
echo "📊 Container status:"
sudo docker compose ps

echo ""
echo "📝 Backend logs (last 20 lines):"
sudo docker compose logs --tail=20 backend

echo ""
echo "✅ Rebuild complete!"
echo ""
echo "To test the fix:"
echo "1. Upload files through the web UI"
echo "2. Run: sudo docker compose restart backend"
echo "3. Try to analyze - files should now persist!"
