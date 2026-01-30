# 🎯 HEXAGON - Electron Desktop App

**Standalone Desktop Application for Structural Analysis**

---

## 🚀 Quick Start

### **1. Verify Setup**
```bash
./test-setup.sh
```

### **2. Build Complete App**
```bash
./build.sh
```

### **3. Run**
```bash
cd release/
./HEXAGON-*.AppImage
```

---

## 📦 What Gets Built

- **Frontend**: React UI bundled with Vite
- **Backend**: Python server packaged with PyInstaller
- **ML Models**: 3 models + ML456 (all embedded)
- **Output**: Single AppImage file (~200-300 MB)

---

## 🛠️ Available Scripts

| Script | Purpose |
|--------|---------|
| `./test-setup.sh` | Verify all prerequisites |
| `./build.sh` | Build complete application |
| `./dev.sh` | Run in development mode |
| `./create-simple-icon.py` | Regenerate icons |

---

## 📁 Files

```
hexagon-electron/
├── build.sh              ← Main build script
├── dev.sh                ← Development mode
├── test-setup.sh         ← Setup verification
├── package.json          ← Electron config
├── build_backend.py      ← Backend bundler
├── frontend-adapter.js   ← Frontend API config
├── electron/
│   ├── main.js          ← Electron main process
│   └── preload.js       ← Secure IPC bridge
└── resources/
    ├── icon.png         ← App icon
    └── tray-icon.png    ← Tray icon
```

---

## 🔧 Build Process

```
[1/6] Install Electron dependencies (npm install)
[2/6] Build frontend (React + Vite)
[3/6] Copy frontend to Electron
[4/6] Build Python backend (PyInstaller)
[5/6] Package Electron app
[6/6] Create AppImage
```

**Time**: ~5-10 minutes

---

## 📋 Prerequisites

**Required:**
- Python 3.14.2 ✓
- Node.js v25.4.0 ✓
- npm 11.7.0 ✓

**Optional:**
- ImageMagick (for icon creation)
- FUSE2 (for AppImage)

---

## 🎨 Features

- ✅ System tray integration
- ✅ Window state persistence
- ✅ Completely offline
- ✅ Dark mode UI
- ✅ Drag & drop uploads
- ✅ PDF export
- ✅ All ML models bundled

---

## 🐛 Troubleshooting

**Icons missing:**
```bash
python create-simple-icon.py
```

**Dependencies missing:**
```bash
pip install flask scikit-learn torch pyinstaller
```

**AppImage won't run:**
```bash
chmod +x HEXAGON-*.AppImage
# Or use:
./HEXAGON-*.AppImage --appimage-extract-and-run
```

---

## 📖 Full Documentation

See: `../HEXAGON_ELECTRON_APP.md`

---

**Ready to build?**

```bash
./build.sh
```

🚀
