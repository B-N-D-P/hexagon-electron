const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods to renderer process
contextBridge.exposeInMainWorld('electronAPI', {
  // Backend communication
  getBackendUrl: () => ipcRenderer.invoke('get-backend-url'),
  checkBackendStatus: () => ipcRenderer.invoke('check-backend-status'),
  
  // File dialogs
  selectFile: (options) => ipcRenderer.invoke('select-file', options),
  selectFolder: () => ipcRenderer.invoke('select-folder'),
  saveFile: (options) => ipcRenderer.invoke('save-file', options),
  
  // Platform info
  platform: process.platform,
  isElectron: true,
  version: '1.0.0'
});

console.log('[HEXAGON] Preload script loaded');
