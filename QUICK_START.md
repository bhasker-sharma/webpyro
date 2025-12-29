# Quick Start Guide - Building the Desktop Application

This guide will help you quickly build the desktop application installer.

## Prerequisites (One-Time Setup)

Install these tools first (if not already installed):

1. **Python 3.11+**: https://www.python.org/downloads/
   - ✅ Check "Add Python to PATH" during installation

2. **Node.js 18+**: https://nodejs.org/
   - Download and install LTS version

3. **Inno Setup 6**: https://jrsoftware.org/isdl.php
   - Install to default location

## Build in 3 Easy Steps

### Step 1: Build the Application

Open Command Prompt in the `desktop-software` folder and run:

```cmd
cd build-scripts
build.bat
```

**What this does**:
- ✅ Installs Python dependencies
- ✅ Builds the React frontend
- ✅ Creates the executable

**Expected result**: Executable created at `backend\dist\PyrometerMonitor\PyrometerMonitor.exe`

### Step 2: Test the Application (Optional but Recommended)

Before creating the installer, test the executable:

```cmd
cd ..\backend\dist\PyrometerMonitor
PyrometerMonitor.exe
```

**Expected result**: Desktop window opens with the dashboard

### Step 3: Create the Installer

```cmd
cd ..\..\..\build-scripts
build-installer.bat
```

**What this does**:
- ✅ Creates professional Windows installer

**Expected result**: Installer created at `output\PyrometerMonitor_Setup_v1.0.0.exe`

## Done!

You now have a professional installer that you can distribute to users:
- **Location**: `desktop-software\output\PyrometerMonitor_Setup_v1.0.0.exe`
- **Size**: ~150-250 MB
- **Ready to distribute**: Yes!

## Distributing to Users

Send users the installer file and these instructions:

1. Double-click `PyrometerMonitor_Setup_v1.0.0.exe`
2. Follow the installation wizard
3. Launch from desktop icon or Start Menu
4. Connect pyrometer device and start monitoring!

## Troubleshooting

**Build fails?**
- Make sure all prerequisites are installed
- Run Command Prompt as Administrator
- Check that port 8000 is not in use

**Installer fails?**
- Check that Inno Setup is installed at: `C:\Program Files (x86)\Inno Setup 6\`
- Make sure the executable was built first (Step 1)

**Need help?**
- Check the full README.md for detailed instructions
- Review the logs in `backend\logs\` folder

---

That's it! You're ready to create and distribute the desktop application.
