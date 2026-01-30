# 🪟 Building HEXAGON for Windows

Since you're on Linux, you have **3 options** to share with Windows users:

---

## ⭐ Option 1: Build on Windows (RECOMMENDED)

### Your friend with Windows does:

1. **Install Prerequisites:**
   - Node.js: https://nodejs.org (v16+)
   - Python: https://python.org (v3.10+)
   - Git: https://git-scm.com

2. **Get the code:**
   ```cmd
   git clone <your-repo>
   cd hexagon-electron
   ```

3. **Build it:**
   ```cmd
   npm install
   npm run build:windows
   ```

4. **Result:**
   - Installer: `release/HEXAGON-1.0.0-win-x64.exe`
   - They can share this `.exe` with others!

---

## 🐧 Option 2: Install Wine on Linux (More Complex)

```bash
# Install Wine
sudo pacman -S wine wine-mono wine-gecko  # For Arch
# or
sudo apt install wine64  # For Ubuntu

# Then build
npm run build:windows
```

---

## 📦 Option 3: Share Linux Version + Instructions

1. **Build Linux version:**
   ```bash
   ./build.sh
   ```

2. **Share:**
   - File: `release/HEXAGON-1.0.0-linux-x64.AppImage`
   - Tell them to use WSL2 or Linux VM

---

## 🎯 Easiest Solution

**Ship the source code** and let Windows users build it themselves using Option 1.

Or use **GitHub Actions** to auto-build for all platforms!

