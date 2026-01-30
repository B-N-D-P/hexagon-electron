/**
 * HEXAGON Frontend Adapter
 * Injects Electron API configuration into frontend bundle
 */

const fs = require('fs');
const path = require('path');

const DIST_DIR = path.join(__dirname, 'dist');
const INDEX_HTML = path.join(DIST_DIR, 'index.html');

console.log('[HEXAGON] Adapting frontend for Electron...');

// Read index.html
let html = fs.readFileSync(INDEX_HTML, 'utf8');

// Inject Electron API bridge script before closing head tag
const electronBridge = `
<script>
  // HEXAGON Electron Bridge
  if (window.electronAPI) {
    console.log('[HEXAGON] Running in Electron mode');
    
    // Override API URL to use Electron backend
    window.electronAPI.getBackendUrl().then(url => {
      window.__HEXAGON_API_URL__ = url;
      console.log('[HEXAGON] Backend URL:', url);
    });
    
    // Enhanced file upload with Electron dialog
    window.__HEXAGON_ELECTRON__ = true;
  } else {
    console.log('[HEXAGON] Running in browser mode');
    window.__HEXAGON_API_URL__ = import.meta.env.VITE_API_URL || 'http://localhost:5000';
  }
</script>
`;

html = html.replace('</head>', electronBridge + '</head>');

// Write back
fs.writeFileSync(INDEX_HTML, html);

console.log('[HEXAGON] ✓ Frontend adapted for Electron');
