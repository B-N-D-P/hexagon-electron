# 🪟 Building HEXAGON on Windows

GitHub Actions can't build the Windows version due to timeout (Python ML dependencies are huge).

**Don't worry!** Building on Windows is actually **super easy** and only takes 5-10 minutes.

---

## 📋 Prerequisites

1. **Python 3.10+**: https://www.python.org/downloads/
   - ✅ Check "Add Python to PATH" during installation
   
2. **Node.js 16+**: https://nodejs.org/
   
3. **Git** (optional): https://git-scm.com/

---

## 🚀 Build Steps

### 1. Get the code

```cmd
git clone https://github.com/B-N-D-P/hexagon-electron.git
cd hexagon-electron
```

Or download ZIP from GitHub and extract it.

### 2. Install Python dependencies

```cmd
cd backend
pip install -r requirements.txt
pip install pyinstaller
cd ..
```

### 3. Install Node dependencies

```cmd
cd hexagon-electron
npm install
cd ..
```

### 4. Build everything!

```cmd
cd hexagon-electron
npm run build:windows
```

**Time:** ~5-10 minutes

---

## 📦 Result

You'll get: `hexagon-electron\release\HEXAGON-1.0.0-win-x64.exe`

This is a **complete installer** with:
- ✅ Python backend bundled
- ✅ All ML models included
- ✅ Frontend React app
- ✅ No dependencies needed!

**Double-click to install** and share with friends!

---

## 🐛 Troubleshooting

### "python not found"
- Reinstall Python and check "Add to PATH"
- Or use: `py -m pip install ...` instead of `pip install ...`

### "npm not found"
- Reinstall Node.js
- Restart your terminal

### "Build failed"
- Make sure you're in the right directory
- Try: `npm install` again
- Check you have at least 5GB free disk space

---

## 💡 Why build locally?

- **Faster**: 5-10 min vs 15+ min timeout on GitHub
- **More reliable**: No cloud build limits
- **You control it**: Customize as needed

---

## ✨ That's it!

The built `.exe` is in `hexagon-electron\release\`

Share it with anyone - they just double-click to install! 🎉
