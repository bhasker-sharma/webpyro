# Pyrometer Desktop Monitor - Standalone Desktop Application

This is the desktop version of the Pyrometer Monitor application, packaged as a standalone Windows executable with an easy-to-use installer.

## Overview

The desktop version has been converted from the web-based application to a standalone desktop application with the following improvements:

- **No External Dependencies**: No need to install Python, Node.js, or PostgreSQL separately
- **SQLite Database**: Lightweight, file-based database included
- **Native Desktop Window**: Runs as a native Windows application using pywebview
- **Easy Installation**: Professional installer like any commercial software
- **Single Click Launch**: Just double-click the icon to run

## Directory Structure

```
desktop-software/
├── backend/                    # Python backend code
│   ├── app/                   # Application modules
│   │   ├── models/           # Database models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── api/              # API routes
│   │   ├── services/         # Business logic services
│   │   ├── config.py         # Configuration (SQLite)
│   │   ├── database.py       # Database connection (SQLite)
│   │   ├── logging_config.py # Logging setup
│   │   └── rs485_client.py   # RS485 communication
│   ├── main.py               # Desktop application entry point
│   ├── requirements.txt      # Python dependencies
│   ├── pyrometer_desktop.spec # PyInstaller build configuration
│   └── dist/                 # Built executable (after build)
├── frontend/                  # React frontend
│   ├── src/                  # Source code
│   ├── dist/                 # Built frontend (after build)
│   └── package.json          # npm dependencies
├── installer/                 # Installer configuration
│   └── installer_script.iss  # Inno Setup script
├── build-scripts/             # Build automation scripts
│   ├── build.bat            # Build executable
│   └── build-installer.bat  # Build installer
├── output/                    # Final installer output (after build)
└── README.md                 # This file
```

## Key Changes from Web Version

### 1. Database Migration
- **From**: PostgreSQL (requires separate server installation)
- **To**: SQLite (file-based, bundled with application)
- **Location**: Database file stored in `data/pyrometer.db` next to the executable

### 2. Desktop Window
- **From**: Browser-based interface
- **To**: Native desktop window using `pywebview`
- **Benefits**: Looks and feels like a native application

### 3. Configuration
- **From**: Manual .env file configuration
- **To**: Automatic configuration with sensible defaults
- **Server**: Runs on localhost (127.0.0.1:8000) for security

### 4. Packaging
- **From**: Manual installation of Python, dependencies, and database
- **To**: Single installer file with everything included

## Building the Application

### Prerequisites

1. **Python 3.11+**
   - Download from: https://www.python.org/downloads/
   - During installation, check "Add Python to PATH"

2. **Node.js 18+**
   - Download from: https://nodejs.org/
   - Choose LTS version

3. **Inno Setup 6** (for creating installer)
   - Download from: https://jrsoftware.org/isdl.php
   - Install to default location: `C:\Program Files (x86)\Inno Setup 6\`

### Build Steps

#### Option 1: Automated Build (Recommended)

1. **Open Command Prompt** in the `desktop-software` folder

2. **Run the build script**:
   ```cmd
   cd build-scripts
   build.bat
   ```

   This will:
   - Install Python dependencies
   - Build the React frontend
   - Create the executable using PyInstaller
   - Place the result in `backend\dist\PyrometerMonitor\`

3. **Create the installer**:
   ```cmd
   build-installer.bat
   ```

   This will:
   - Use Inno Setup to create a professional installer
   - Place the installer in `output\PyrometerMonitor_Setup_v1.0.0.exe`

#### Option 2: Manual Build

1. **Install Python dependencies**:
   ```cmd
   cd backend
   pip install -r requirements.txt
   ```

2. **Build the frontend**:
   ```cmd
   cd ..\frontend
   npm install
   npm run build
   ```

3. **Build the executable**:
   ```cmd
   cd ..\backend
   pyinstaller pyrometer_desktop.spec --clean --noconfirm
   ```

4. **Build the installer** (open Inno Setup):
   - Open `installer\installer_script.iss` in Inno Setup
   - Click "Build" → "Compile"

## Testing the Application

### Test the Executable Directly

Before creating the installer, you can test the executable:

```cmd
cd backend\dist\PyrometerMonitor
PyrometerMonitor.exe
```

The application should:
1. Start the backend server
2. Open a desktop window
3. Display the dashboard interface
4. Create a `data` folder with `pyrometer.db` database file

### Test the Installer

1. Run the installer: `output\PyrometerMonitor_Setup_v1.0.0.exe`
2. Follow the installation wizard
3. Launch the application from the desktop icon or Start Menu
4. Verify all features work correctly

## Distributing to Users

### What to Give Users

Provide users with the installer file:
- **File**: `PyrometerMonitor_Setup_v1.0.0.exe`
- **Size**: Approximately 150-250 MB (includes all dependencies)

### User Installation Instructions

1. **Download** the installer file
2. **Double-click** to run the installer
3. **Follow** the installation wizard:
   - Accept the license agreement
   - Choose installation location (default: `C:\Program Files\Pyrometer Desktop Monitor\`)
   - Select whether to create desktop icon
   - Click Install
4. **Launch** the application:
   - From desktop icon (if created)
   - From Start Menu → Pyrometer Desktop Monitor
   - From installation folder

### First Run

On first run, the application will:
1. Create a `data` folder for the database
2. Initialize the SQLite database
3. Start the monitoring services
4. Display the dashboard

### Data Location

User data is stored in:
- **Installation folder**: `C:\Program Files\Pyrometer Desktop Monitor\data\pyrometer.db`
- **Logs**: `C:\Program Files\Pyrometer Desktop Monitor\logs\`

### Uninstallation

Users can uninstall via:
- **Control Panel** → Programs → Uninstall a program
- **Start Menu** → Pyrometer Desktop Monitor → Uninstall

## Configuration

### Default Settings

The application uses these default settings:

```python
app_name: "Pyrometer Desktop Monitor"
debug: False
modbus_timeout: 5
modbus_poll_interval: 5
data_retention_days: 90
server_host: "127.0.0.1"  # Localhost only
server_port: 8000
config_pin: "1234"
```

### Customizing Settings

Advanced users can modify settings by:
1. Creating a `.env` file in the installation folder
2. Adding custom configuration values
3. Restarting the application

## Troubleshooting

### Build Issues

**Problem**: PyInstaller fails with "module not found" error
**Solution**: Make sure all dependencies are installed:
```cmd
pip install -r requirements.txt
```

**Problem**: Frontend build fails
**Solution**: Clear npm cache and reinstall:
```cmd
cd frontend
rd /s /q node_modules
npm cache clean --force
npm install
npm run build
```

**Problem**: Inno Setup not found
**Solution**: Install Inno Setup from https://jrsoftware.org/isdl.php

### Runtime Issues

**Problem**: Application doesn't start
**Solution**:
- Check if port 8000 is already in use
- Run as Administrator
- Check logs in the `logs` folder

**Problem**: Database errors
**Solution**:
- Delete `data\pyrometer.db` to reset the database
- Restart the application

**Problem**: COM port not detected
**Solution**:
- Ensure the RS485 adapter is connected
- Install the correct drivers for the adapter
- Run the application as Administrator

## Development

### Running in Development Mode

For development and testing:

```cmd
cd backend
python main.py
```

This will:
- Run with DEBUG mode enabled
- Show console output
- Use local database file
- Open the desktop window

### Modifying the Code

1. Make changes to Python code in `backend/app/`
2. Make changes to React code in `frontend/src/`
3. Test changes by running `python main.py`
4. Rebuild the frontend: `cd frontend && npm run build`
5. Rebuild the executable: `cd backend && pyinstaller pyrometer_desktop.spec`

## Technical Details

### Architecture

```
┌─────────────────────────────────┐
│   Desktop Window (pywebview)    │
│   Native OS Window              │
└─────────────┬───────────────────┘
              │ HTTP/WebSocket
              ↓
┌─────────────────────────────────┐
│   FastAPI Backend               │
│   - REST API                    │
│   - WebSocket for real-time     │
│   - Background services         │
└─────────────┬───────────────────┘
              │ SQLAlchemy
              ↓
┌─────────────────────────────────┐
│   SQLite Database               │
│   - device_settings             │
│   - device_readings             │
│   - reading_archive             │
└─────────────────────────────────┘
              ↑
              │ Modbus RTU / RS485
┌─────────────────────────────────┐
│   Pyrometer Devices             │
│   (Serial/COM Port)             │
└─────────────────────────────────┘
```

### Technologies Used

- **Backend**: FastAPI, Uvicorn, SQLAlchemy
- **Frontend**: React, Vite, Tailwind CSS, Recharts
- **Database**: SQLite 3
- **Desktop**: pywebview (uses system's Edge/Chrome WebView2)
- **Modbus**: pymodbus, pyserial
- **Packaging**: PyInstaller, Inno Setup

### Dependencies

**Python** (`requirements.txt`):
- fastapi==0.118.0
- uvicorn==0.37.0
- SQLAlchemy==2.0.43
- pywebview==5.3
- pyinstaller==6.11.1
- pymodbus==3.11.3
- pyserial==3.5
- And more... (see requirements.txt)

**JavaScript** (`package.json`):
- react==19.1.1
- vite==6.0.0
- recharts==3.3.0
- tailwindcss==3.4.0
- And more... (see package.json)

## Version History

### Version 1.0.0 (Current)
- Initial desktop release
- Migrated from PostgreSQL to SQLite
- Added pywebview desktop wrapper
- Created installer with Inno Setup
- Full feature parity with web version

## Support

For issues or questions:
1. Check the logs in the `logs` folder
2. Review this README
3. Contact TIPL support

## License

[Add your license information here]

---

**Built with** ❤️ **by TIPL**
