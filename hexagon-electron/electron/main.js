const { app, BrowserWindow, Tray, Menu, ipcMain, dialog, shell } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const treeKill = require('tree-kill');
const Store = require('electron-store');
const express = require('express');

// Initialize electron-store for persistent settings
const store = new Store();

let mainWindow = null;
let tray = null;
let backendProcess = null;
let backendReady = false;

const isDev = !app.isPackaged; // Better detection: true if not packaged
const BACKEND_PORT = 5000;
const FRONTEND_DEV_PORT = 5173;

// Backend server startup
function startBackend() {
  return new Promise((resolve, reject) => {
    // In development mode, backend is already running via npm run dev
    if (isDev) {
      console.log('[HEXAGON] Development mode: Skipping backend start (already running)');
      // Just wait a moment and resolve
      setTimeout(() => {
        backendReady = true;
        resolve();
      }, 1000);
      return;
    }

    // Production: Run packaged executable
    const backendExecutable = process.platform === 'win32' ? 'backend.exe' : 'backend';
    const backendPath = path.join(process.resourcesPath, 'backend', backendExecutable);

    console.log('[HEXAGON] Starting backend server...');
    console.log('[HEXAGON] Backend path:', backendPath);

    backendProcess = spawn(backendPath, [], {
      env: { ...process.env, PORT: BACKEND_PORT }
    });

    backendProcess.stdout.on('data', (data) => {
      console.log(`[Backend] ${data.toString()}`);
      if (data.toString().includes('Running on') || data.toString().includes('Uvicorn running')) {
        backendReady = true;
        resolve();
      }
    });

    backendProcess.stderr.on('data', (data) => {
      console.error(`[Backend Error] ${data.toString()}`);
    });

    backendProcess.on('error', (error) => {
      console.error('[Backend] Failed to start:', error);
      reject(error);
    });

    backendProcess.on('close', (code) => {
      console.log(`[Backend] Process exited with code ${code}`);
      backendReady = false;
    });

    // Timeout if backend doesn't start in 30 seconds
    setTimeout(() => {
      if (!backendReady) {
        reject(new Error('Backend startup timeout'));
      }
    }, 30000);
  });
}

// Create main window
function createWindow() {
  // Restore window state from store
  const windowState = store.get('windowState', {
    width: 1400,
    height: 900,
    x: undefined,
    y: undefined,
    isMaximized: false
  });

  mainWindow = new BrowserWindow({
    width: windowState.width,
    height: windowState.height,
    x: windowState.x,
    y: windowState.y,
    minWidth: 1024,
    minHeight: 768,
    icon: path.join(__dirname, '../resources/icon.png'),
    backgroundColor: '#0f172a', // Dark slate background
    show: false, // Don't show until ready
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    },
    frame: true,
    title: 'HEXAGON - Structural Analysis'
  });

  // Maximize if it was maximized before
  if (windowState.isMaximized) {
    mainWindow.maximize();
  }

  // Save window state on resize/move
  const saveWindowState = () => {
    const bounds = mainWindow.getBounds();
    store.set('windowState', {
      width: bounds.width,
      height: bounds.height,
      x: bounds.x,
      y: bounds.y,
      isMaximized: mainWindow.isMaximized()
    });
  };

  mainWindow.on('resize', saveWindowState);
  mainWindow.on('move', saveWindowState);

  // Load frontend
  const frontendURL = isDev
    ? `http://localhost:${FRONTEND_DEV_PORT}`
    : `file://${path.join(__dirname, '../dist/index.html')}`;

  mainWindow.loadURL(frontendURL);

  // Show window when ready
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    if (isDev) {
      mainWindow.webContents.openDevTools();
    }
  });

  // Handle external links - open in system browser instead of Electron window
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    // Only open HTML reports in browser, not PDFs (PDFs should download)
    if (url.includes('.html') && (url.startsWith('http://localhost:') || url.startsWith('http://127.0.0.1:'))) {
      shell.openExternal(url);
      return { action: 'deny' };
    }
    // For other external URLs, open in browser
    if (url.startsWith('http://') || url.startsWith('https://')) {
      shell.openExternal(url);
      return { action: 'deny' };
    }
    // Allow default behavior for other cases (like file downloads)
    return { action: 'allow' };
  });

  // Handle PDF downloads - prevent opening in new window, download instead
  mainWindow.webContents.session.on('will-download', (event, item, webContents) => {
    // Let the download happen normally - user's browser will handle it
    console.log('[HEXAGON] Downloading:', item.getFilename());
  });

  // Handle window close - minimize to tray instead
  mainWindow.on('close', (event) => {
    if (!app.isQuitting) {
      event.preventDefault();
      mainWindow.hide();
      
      // Show notification on first minimize
      if (!store.get('minimizeNotificationShown')) {
        tray.displayBalloon({
          title: 'HEXAGON',
          content: 'Application minimized to system tray. Right-click the icon to quit.',
          icon: path.join(__dirname, '../resources/icon.png')
        });
        store.set('minimizeNotificationShown', true);
      }
    }
  });
}

// Create system tray
function createTray() {
  const iconPath = path.join(__dirname, '../resources/tray-icon.png');
  tray = new Tray(iconPath);

  const contextMenu = Menu.buildFromTemplate([
    {
      label: 'Show HEXAGON',
      click: () => {
        mainWindow.show();
        mainWindow.focus();
      }
    },
    {
      label: 'About',
      click: () => {
        dialog.showMessageBox(mainWindow, {
          type: 'info',
          title: 'About HEXAGON',
          message: 'HEXAGON v1.0.0',
          detail: 'AI-Powered Structural Analysis Desktop Application\n\nIncludes:\n- Damage Classifier\n- Health Monitor\n- ML456 Baseline Predictor\n\nCompletely offline and secure.',
          buttons: ['OK']
        });
      }
    },
    { type: 'separator' },
    {
      label: 'Quit HEXAGON',
      click: () => {
        app.isQuitting = true;
        app.quit();
      }
    }
  ]);

  tray.setToolTip('HEXAGON - Structural Analysis');
  tray.setContextMenu(contextMenu);

  // Double-click tray icon to show window
  tray.on('double-click', () => {
    mainWindow.show();
    mainWindow.focus();
  });
}

// App lifecycle
app.whenReady().then(async () => {
  console.log('[HEXAGON] Application starting...');
  
  try {
    // Start backend first
    await startBackend();
    console.log('[HEXAGON] Backend ready!');

    // Create UI
    createWindow();
    createTray();

    console.log('[HEXAGON] Application ready!');
  } catch (error) {
    console.error('[HEXAGON] Startup failed:', error);
    dialog.showErrorBox(
      'Startup Error',
      `Failed to start HEXAGON backend:\n${error.message}\n\nPlease check logs and try again.`
    );
    app.quit();
  }
});

// Quit when all windows closed (except on macOS)
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    // Don't quit, just hide (tray app)
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

// Cleanup on quit
app.on('before-quit', () => {
  app.isQuitting = true;
});

app.on('will-quit', () => {
  // Kill backend process
  if (backendProcess) {
    console.log('[HEXAGON] Shutting down backend...');
    treeKill(backendProcess.pid, 'SIGTERM', (err) => {
      if (err) {
        console.error('[HEXAGON] Failed to kill backend:', err);
      }
    });
  }
});

// IPC handlers
ipcMain.handle('get-backend-url', () => {
  return `http://localhost:${BACKEND_PORT}`;
});

ipcMain.handle('check-backend-status', () => {
  return backendReady;
});

ipcMain.handle('select-file', async (event, options) => {
  const result = await dialog.showOpenDialog(mainWindow, options);
  return result;
});

ipcMain.handle('select-folder', async () => {
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openDirectory']
  });
  return result;
});

ipcMain.handle('save-file', async (event, options) => {
  const result = await dialog.showSaveDialog(mainWindow, options);
  return result;
});

console.log('[HEXAGON] Electron main process initialized');
