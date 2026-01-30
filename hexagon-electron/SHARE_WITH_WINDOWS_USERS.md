# 🎯 How to Share HEXAGON with Windows Friends

## ✅ What We Built Successfully

✓ Frontend (React app)
✓ Backend (Python server with PyInstaller) 
✓ All ML models included
✓ Linux AppImage ready to build

## 🪟 Windows Options

### **Option A: You Build on Linux with Wine** ⭐ EASIEST

1. **Install Wine:**
   ```bash
   sudo pacman -S wine
   ```

2. **Build Windows installer:**
   ```bash
   npm run build:windows
   ```

3. **Share the file:**
   - Location: `release/HEXAGON-1.0.0-win-x64.exe` 
   - Size: ~300 MB
   - Your friends just double-click to install!

---

### **Option B: Your Friends Build on Windows**

**They install:**
- Node.js (https://nodejs.org)
- Python 3.10+ (https://python.org)

**They run:**
```cmd
git clone <your-repo-url>
cd hexagon-electron
npm install
npm run build:windows
```

**Result:** `release/HEXAGON-1.0.0-win-x64.exe`

---

### **Option C: Share Source Code** 

Send them:
1. The entire project folder
2. Instructions from Option B
3. They build it themselves

---

## 📦 Alternative: Build Linux Version Now

You can build the Linux AppImage right now:

```bash
./build.sh
```

Result: `release/HEXAGON-1.0.0-linux-x64.AppImage`

Your Windows friends can run this in WSL2!

---

## 🚀 My Recommendation

**Install Wine and build Windows installer (Option A)**:

```bash
sudo pacman -S wine
npm run build:windows
```

Then share the `.exe` file via:
- Google Drive
- GitHub Releases  
- Dropbox
- USB drive

Your friends get a **one-click installer**! 🎉

