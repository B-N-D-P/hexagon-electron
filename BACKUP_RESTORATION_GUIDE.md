# 🔒 System Backup & Restoration Guide

## Backup Information

**Backup Created:** January 29, 2026 at 18:03:23  
**Backup Location:** `/mnt/storage/system_backup_20260129_180323`  
**Backup Size:** 1.3 GB  
**Original System:** `/mnt/storage/structural-repair-web`

---

## 📦 Backup Contents

### ✅ Included Files (25,221 total)
- **19,074 Python files** - All backend logic, ML models, services
- **31 JSX files** - React frontend components
- **29 JavaScript files** - Frontend services and utilities
- **48 Markdown files** - Complete documentation
- **80 CSV files** - Training and test datasets
- **Configuration files** - .env, docker-compose.yml, package.json, etc.
- **Scripts** - Shell scripts for automation
- **Research materials** - PDFs, posters, figures

### ❌ Excluded (Can be Reinstalled)
- Python virtual environments (`venv`, `ui_env`, `ui_env_new`) - 2.4 GB
- Node.js modules (`node_modules`) - 513 MB
- Python cache (`__pycache__`, `*.pyc`)
- Build artifacts (`.vite`, `deps_temp*`)

---

## 🔄 How to Restore the System

### Method 1: Full Restoration

```bash
# 1. Copy backup to desired location
cd /path/to/destination
cp -r /mnt/storage/system_backup_20260129_180323 ./structural-repair-web
cd structural-repair-web

# 2. Reinstall Python dependencies (Backend)
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Reinstall Node.js dependencies (Frontend)
cd ../frontend
npm install

# 4. Setup UI environment (Optional - for CLI interface)
cd ..
python3 -m venv ui_env
source ui_env/bin/activate
pip install -r ui_requirements.txt

# 5. Configure environment variables
cp .env.example .env
# Edit .env with your settings

# 6. Test the system
bash QUICK_START.sh
```

### Method 2: Selective Restoration

```bash
# Restore only specific components:

# Backend only
cp -r /mnt/storage/system_backup_20260129_180323/backend ./

# Frontend only
cp -r /mnt/storage/system_backup_20260129_180323/frontend ./

# Data files only
cp -r /mnt/storage/system_backup_20260129_180323/datas ./

# Documentation only
cp /mnt/storage/system_backup_20260129_180323/*.md ./
```

---

## 🧪 Verification After Restoration

### 1. Check Critical Files
```bash
# Backend
ls -la backend/app.py backend/parameter_calculator.py

# Frontend
ls -la frontend/src/App.jsx frontend/src/pages/Upload.jsx

# Data
ls -la datas/baseline/ datas/damaged/ datas/repaired/

# ML Models
ls -la backend/ml_models/
```

### 2. Test Backend
```bash
cd backend
source venv/bin/activate
python app.py  # Should start Flask server on port 5000
```

### 3. Test Frontend
```bash
cd frontend
npm run dev  # Should start Vite dev server on port 5173
```

### 4. Test Full System
```bash
bash start_all.sh  # Start all services
bash stop_all.sh   # Stop all services
```

---

## 📋 Critical Components Verified

### Backend (`backend/`)
- ✅ `app.py` - Main Flask application (60 KB)
- ✅ `parameter_calculator.py` - Core math/physics calculations
- ✅ `services/` - Damage classification, health monitoring, report generation
- ✅ `ml_models/` - ML feature extraction and anomaly detection
- ✅ `requirements.txt` - Python dependencies

### Frontend (`frontend/`)
- ✅ `src/App.jsx` - Main React application
- ✅ `src/pages/Upload.jsx` - File upload and analysis page (41 KB)
- ✅ `src/pages/Dashboard.jsx` - Results dashboard
- ✅ `src/components/` - Reusable UI components
- ✅ `package.json` - Node.js dependencies

### Data (`datas/`)
- ✅ `baseline/` - Healthy structure data
- ✅ `damaged/` - Damaged structure data  
- ✅ `repaired/` - Repaired structure data (good/bad/verybad repair)
- ✅ 80 CSV files total

### Documentation
- ✅ `README.md` - Main project documentation
- ✅ `COMPLETE_PROJECT_SUMMARY.md` - Comprehensive overview
- ✅ `ML456_INTEGRATION_GUIDE.md` - ML model integration
- ✅ `QUICK_START.md` - Quick setup guide

---

## 🆘 Troubleshooting

### Issue: Missing Python packages
```bash
# Reinstall all backend dependencies
cd backend
pip install -r requirements.txt
```

### Issue: Missing Node modules
```bash
# Reinstall all frontend dependencies
cd frontend
npm install
```

### Issue: Permission errors
```bash
# Fix file permissions
chmod +x scripts/*.sh
chmod +x *.sh
```

### Issue: ML model not found
```bash
# ML models are included in backup
# Check: backend/ml_models/trained/
ls -la backend/ml_models/trained/
```

---

## 📞 Additional Resources

- **Main Documentation:** `README.md`
- **Quick Start:** `QUICK_START.md`, `START_HERE.md`
- **ML Integration:** `ML456_INTEGRATION_GUIDE.md`
- **UI Setup:** `UI_DEPLOYMENT_GUIDE.md`
- **Validation:** `VALIDATOR_QUICKSTART.md`

---

## ⚠️ Important Notes

1. **Virtual environments are NOT included** - They must be recreated after restoration
2. **Node modules are NOT included** - Run `npm install` after restoration
3. **All source code and data ARE included** - No data loss
4. **Git history IS included** - `.git` folder is backed up
5. **Configuration templates ARE included** - `.env.example` is backed up

---

## 🔐 Backup Integrity

- Original system size: 5.2 GB
- Backup size: 1.3 GB (after excluding reinstallable dependencies)
- Compression: None (direct copy for maximum compatibility)
- File count: 25,221 files
- Verification: Manual checks performed on critical files

**✅ Backup Status: VERIFIED AND COMPLETE**

---

*Backup created before implementing retrofitting scenario fixes to the repair quality index model.*
