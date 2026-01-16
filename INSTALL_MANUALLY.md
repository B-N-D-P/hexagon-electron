# 🔧 Manual Installation Guide for HEXAGON UI

If the automated launcher script times out, follow these manual steps:

## Step 1: Create Virtual Environment

```bash
cd structural-repair-web
python3 -m venv ui_env
```

## Step 2: Activate Virtual Environment

**Linux/Mac:**
```bash
source ui_env/bin/activate
```

**Windows:**
```bash
ui_env\Scripts\activate
```

## Step 3: Upgrade pip and setuptools

```bash
pip install --upgrade pip setuptools wheel
```

## Step 4: Install Dependencies One by One

```bash
# Install in this order to avoid conflicts
pip install pyserial
pip install numpy
pip install scipy
pip install PyQt5
pip install pyqtgraph
```

## Step 5: Verify Installation

```bash
python3 verify_ui_setup.py
```

You should see all ✅ marks.

## Step 6: Launch the Application

```bash
python3 ui_main.py
```

---

## If Installation Still Fails

### For Python 3.14 Users

If you're using Python 3.14, try with Python 3.11 or 3.12 instead:

```bash
python3.12 -m venv ui_env
source ui_env/bin/activate
pip install --upgrade pip setuptools wheel
pip install pyserial numpy scipy PyQt5 pyqtgraph
python3.12 ui_main.py
```

### Alternative: Use System Python

```bash
# Install globally (if you prefer)
pip install --user pyserial numpy scipy PyQt5 pyqtgraph
python3 ui_main.py
```

### Troubleshooting Installation

**Error: "No module named 'setuptools'"**
```bash
pip install --upgrade setuptools
```

**Error: "wheel is not a valid wheel filename"**
```bash
pip install --upgrade wheel
```

**Error: "PyQt5 installation failed"**
```bash
# Try pre-built version
pip install PyQt5==5.15.7
```

---

## Quick Test

Once installed, run this to verify everything works:

```bash
python3 -c "import PyQt5, numpy, scipy, serial, pyqtgraph; print('✅ All dependencies installed successfully!')"
```

---

## Next Steps

Once installation succeeds:

1. Connect Arduino via USB
2. Run: `python3 ui_main.py`
3. Click "🔄 Refresh" to detect COM port
4. Click "🔌 Connect"
5. Start monitoring!

See **QUICK_START_UI.md** for full workflow.

---

**Need help?** Check **UI_README.md** troubleshooting section.
