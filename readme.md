# Web Pyrometer Monitoring System

A production-ready web application for real-time temperature monitoring of multiple Modbus RS485 pyrometer devices with network accessibility, historical data analysis, and multi-user support.

## Features

- **Real-time Monitoring:** Continuous polling and live temperature display with WebSocket updates
- **Multi-Device Support:** Monitor up to 16 Modbus devices simultaneously
- **Network Accessible:** Access from any computer on your local network
- **Historical Data:** PostgreSQL storage with CSV export and date-range filtering
- **Interactive Graphs:** Real-time temperature visualization with customizable time windows
- **Responsive UI:** Modern interface built with React 19 and Tailwind CSS

## Technology Stack

### Backend
- **FastAPI 0.118** - Async Python web framework
- **PostgreSQL** - Database for device config and readings
- **PyModbus 3.11.3** - Modbus RTU communication
- **Uvicorn** - ASGI server
- **SQLAlchemy 2.0** - ORM

### Frontend
- **React 19.1.1** - UI library
- **Vite 6.0** - Build tool and dev server
- **Tailwind CSS 3.4** - Styling
- **Recharts 3.3** - Charts
- **Axios** - HTTP client

---

## Quick Start (Production)

### Prerequisites

Install these on the **SERVER** computer only (clients just need a browser):

1. **Python 3.8+** - [Download](https://www.python.org/downloads/) (check "Add to PATH")
2. **PostgreSQL 14+** - [Download](https://www.postgresql.org/download/)
3. **Node.js 18+** - [Download](https://nodejs.org/) (only for initial build, optional for production)

### Installation (15 minutes)

**1. Clone or download this repository**
```bash
git clone <repository-url>
cd webpyro
```

**2. Run automated setup** (as Administrator)
```bash
setup-environment.bat
```
This installs all dependencies for both backend and frontend.

**3. Create PostgreSQL database**
```sql
-- Open pgAdmin or psql
CREATE DATABASE modbus_monitor;
```

**4. Configure backend**

Edit `backend\.env` (copy from `backend\.env.production` if needed):
```env
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/modbus_monitor
CONFIG_PIN=1234  # Change this!
DEBUG=False
MODBUS_POLL_INTERVAL=1
```

**Note:** Use `%40` for `@` in passwords (e.g., `admin@123` → `admin%40123`)

**5. Configure firewall** (as Administrator)
```bash
configure-firewall.bat
```

**6. Start the application**
```bash
PRODUCTION-START-MINIMAL.bat
```

**7. Access the application**
- From server: `http://localhost:5173`
- From network: `http://YOUR-SERVER-IP:5173`

Find your server IP: Run `ipconfig` in Command Prompt

### Stopping the Application
```bash
PRODUCTION-STOP.bat
```

---

## Manual Setup (Development or Advanced)

### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file (see Configuration section)

# Create database
psql -U postgres -c "CREATE DATABASE modbus_monitor;"

# Start server
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Development server (with hot-reload)
npm run dev

# Production build
npm run build

# Serve production build
npm run preview
```

---

## Building for Production

### Frontend Build

The frontend must be built before production deployment:

```bash
cd frontend

# Install dependencies (if not already done)
npm install

# Build for production
npm run build
```

This creates an optimized build in `frontend/dist/` with:
- Minified JavaScript and CSS
- Tree-shaking (removes unused code)
- Code splitting for faster loading
- Optimized assets

**Build output:** `frontend/dist/` (~5MB)

### Serving the Production Build

**Option 1: With Node.js (Vite Preview)**
```bash
cd frontend
npm run preview
```
- Requires: `node_modules/`, `package.json`, `vite.config.js`
- Use: `PRODUCTION-START.bat`

**Option 2: With Python HTTP Server (Recommended)**
```bash
cd frontend/dist
python -m http.server 5173 --bind 0.0.0.0
```
- Only requires: `dist/` folder
- Use: `PRODUCTION-START-MINIMAL.bat` ✅
- Smaller deployment package (~200MB vs ~300MB)

### Deployment Package

For deploying to a new server, you need:

```
webpyro/
├── backend/
│   ├── venv/               # Python environment
│   ├── app/                # Application code
│   ├── main.py
│   ├── requirements.txt
│   └── .env.production     # Template (copy to .env)
├── frontend/
│   └── dist/               # Production build (MINIMAL)
│   OR
│   ├── dist/               # Production build
│   ├── node_modules/       # NPM packages
│   ├── package.json        # For Vite preview
│   └── vite.config.js      # Vite config
├── PRODUCTION-START-MINIMAL.bat  # Recommended
├── PRODUCTION-STOP.bat
├── setup-environment.bat
└── configure-firewall.bat
```

**Package size:**
- Minimal (Python HTTP server): ~200MB
- Standard (Vite preview): ~300MB

---

## Configuration

### Backend (.env file)

The `.env.production` file is a **template**. Copy it to `.env` and customize:

**Why two files?**
- **`.env.production`** - Template with example values (safe for Git)
- **`.env`** - Your actual config with real passwords (**NOT** in Git)

```bash
# Copy template to create your config
cd backend
copy .env.production .env

# Edit .env with your settings
notepad .env
```

**Key settings:**

```env
# Database (required)
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/modbus_monitor

# Security (required)
CONFIG_PIN=1234  # Change this 4-digit PIN!
DEBUG=False      # Must be False in production

# Modbus (optional, can configure in UI)
MODBUS_TIMEOUT=1              # Seconds to wait for device response
MODBUS_POLL_INTERVAL=1        # Seconds between polling cycles
MODBUS_REGISTER_ADDRESS=4002  # Register type
MODBUS_FUNCTION_CODE=3        # Function code (3 or 4)
MODBUS_START_REGISTER=1       # Start register
MODBUS_REGISTER_COUNT=1       # Number of registers
```

### Frontend

Auto-detects backend URL based on hostname. No configuration needed for local network.

For custom setup, edit `frontend/src/services/api.js`:
```javascript
const hostname = window.location.hostname;
const apiUrl = `http://${hostname}:8000/api`;
```

---

## Usage

### First-Time Device Setup

1. Open the application in your browser
2. Click "Configure Devices" button
3. Add your Modbus devices:
   - Name: e.g., "Pyrometer 1"
   - Slave ID: Modbus device address (1-247)
   - COM Port: e.g., COM3 (check Device Manager)
   - Baud Rate: Match your device (9600, 19200, etc.)
   - Enable device
   - Show in graph (optional)
4. Click "Save Configuration"
5. Devices will start polling automatically

### Monitoring

- **Dashboard**: Real-time temperature cards with color-coded status
  - 🟢 Green: Reading OK
  - 🟡 Yellow: Stale data
  - 🔴 Red: Error
- **Graphs**: Time-series visualization (10 min - 3 hours)
- **Preview & Export**: Historical data with CSV export

### Network Access

**From server computer:**
```
http://localhost:5173
```

**From any computer on the network:**
```
http://192.168.1.100:5173  (use your server's IP)
```

**Find server IP:**
```bash
ipconfig  # Windows
ifconfig  # Linux/Mac
```

### Desktop Shortcut (Optional)

For easy access, create a shortcut on client computers:
1. Right-click Desktop → New → Shortcut
2. Location: `http://YOUR-SERVER-IP:5173`
3. Name: "Web Pyrometer"

---

## Project Structure

```
webpyro/
├── backend/                      # Python FastAPI backend
│   ├── main.py                   # Entry point
│   ├── requirements.txt          # Dependencies
│   ├── .env.production          # Config template
│   ├── .env                     # Actual config (not in Git)
│   └── app/
│       ├── models/              # Database models
│       ├── schemas/             # Pydantic schemas
│       ├── api/                 # API routes
│       │   ├── routes.py        # Main endpoints
│       │   ├── devices.py       # Device CRUD
│       │   └── websocket.py     # WebSocket handler
│       └── services/            # Business logic
│           ├── modbus_service.py     # Modbus communication
│           ├── polling_service.py    # Background polling
│           ├── buffer_service.py     # Ping-pong buffer
│           └── device_service.py     # Device operations
│
├── frontend/                     # React frontend
│   ├── src/
│   │   ├── pages/
│   │   │   ├── DashboardPage.jsx     # Real-time monitoring
│   │   │   └── PreviewPage.jsx       # Historical data
│   │   ├── components/
│   │   │   ├── Navbar.jsx
│   │   │   ├── ConfigModal.jsx       # Device config UI
│   │   │   └── GraphSection.jsx      # Charts
│   │   └── services/
│   │       ├── api.js                # API client
│   │       └── websocket.js          # WebSocket client
│   ├── dist/                    # Production build (generated)
│   ├── package.json
│   └── vite.config.js
│
├── setup-environment.bat         # Initial setup
├── configure-firewall.bat        # Firewall config
├── PRODUCTION-START-MINIMAL.bat  # Start (Python HTTP server)
├── PRODUCTION-STOP.bat          # Stop servers
├── .gitignore                   # Git ignore rules
└── README.md                    # This file
```

---

## API Documentation

### Interactive Docs

FastAPI provides built-in documentation:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Key Endpoints

**Devices**
- `GET /api/devices` - List all devices
- `POST /api/devices` - Create device
- `PUT /api/devices/{id}` - Update device
- `DELETE /api/devices/{id}` - Delete device

**Readings**
- `GET /api/reading/latest` - Latest reading per device
- `GET /api/reading/filter?start_time=...&end_time=...` - Filtered readings
- `GET /api/reading/export/csv` - Export CSV

**System**
- `GET /api/health` - Health check
- `GET /api/polling/stats` - Polling statistics

**Real-time**
- `WebSocket /api/ws` - Live temperature updates

---

## Database Schema

The application automatically creates these tables on first run:

### device_settings
Device configuration (name, slave ID, COM port, baud rate, etc.)

### device_readings
Recent temperature readings with timestamps and status

### reading_archive
Historical data archive

---

## Troubleshooting

### Centralized Logging System

The application includes comprehensive logging to help diagnose issues. All log files are in `backend/logs/`:

**Quick diagnosis:**
```powershell
# Check all errors (RECOMMENDED - check this first!)
Get-Content backend\logs\errors.log -Tail 20

# Monitor errors in real-time
Get-Content backend\logs\errors.log -Wait -Tail 20

# Check Modbus communication issues
Get-Content backend\logs\modbus.log -Tail 20

# Check API requests
Get-Content backend\logs\api.log -Tail 20
```

**Log files:**
- `errors.log` - All errors (check this first!) ⚠️
- `modbus.log` - Device communication issues
- `polling.log` - Polling service status
- `database.log` - Database connection issues
- `api.log` - HTTP request/response logs
- `websocket.log` - WebSocket connection logs
- `app.log` - General application logs

For complete logging documentation, see: **backend/LOGGING.md**

---

### Cannot connect to database
- Verify PostgreSQL is running (Services → postgresql-x64-XX)
- Check `DATABASE_URL` in `backend\.env`
- Ensure database `modbus_monitor` exists
- **Check logs**: `backend\logs\database.log` and `backend\logs\errors.log`

### Port already in use
```bash
# Find process using port
netstat -ano | findstr "8000"
netstat -ano | findstr "5173"

# Kill process
taskkill /PID <process-id> /F
```

### Modbus devices not responding
- Check COM port in Device Manager
- Verify baud rate matches device
- Ensure RS485 adapter is connected
- Check device slave ID is correct
- Verify device is powered on
- **Check logs**: `backend\logs\modbus.log` for detailed communication errors

### Cannot access from network
- Run `configure-firewall.bat` as Administrator
- Verify both computers on same network
- Ping server from client: `ping SERVER-IP`
- Temporarily disable antivirus to test

### No data showing
- Check device configuration (click "Configure Devices")
- Verify devices are enabled
- Check browser console for errors (F12)
- Verify backend is running: `http://localhost:8000/api/health`
- **Check logs**: `backend\logs\polling.log` to see if devices are being polled

---

## Development

### Adding API Endpoint

1. Add route in `backend/app/api/routes.py`
2. Add service logic in appropriate service file
3. Update frontend in `frontend/src/services/api.js`

### Adding Frontend Page

1. Create component in `frontend/src/pages/`
2. Add route in `frontend/src/App.jsx`
3. Add navigation in `frontend/src/components/Navbar.jsx`

### Testing Modbus

```bash
cd backend
python test_modbus.py
```

---

## Production Deployment

### Security Checklist

- [ ] Change `CONFIG_PIN` in `.env`
- [ ] Set `DEBUG=False` in `.env`
- [ ] Use strong PostgreSQL password
- [ ] Configure Windows Firewall
- [ ] Restrict network access if needed

### Running as Windows Service (Optional)

For automatic startup with Windows, use NSSM or Task Scheduler to run `PRODUCTION-START-MINIMAL.bat` on boot.

### Backup Strategy

**Database backup:**
```bash
pg_dump -U postgres modbus_monitor > backup.sql
```

**Configuration backup:**
- Backup `backend\.env` file
- Backup device configurations

---

## Scripts Reference

| Script | Purpose | Admin Required |
|--------|---------|----------------|
| `setup-environment.bat` | Install dependencies (run once) | Yes |
| `configure-firewall.bat` | Configure Windows Firewall | Yes |
| `PRODUCTION-START-MINIMAL.bat` | Start system (Python HTTP) | No |
| `PRODUCTION-STOP.bat` | Stop all servers | No |

**Daily operation:** Just run `PRODUCTION-START-MINIMAL.bat`

---

## Offline Deployment

This system works 100% offline on local network:

1. Download prerequisites on a computer with internet
2. Copy to USB drive with application files
3. Install on offline server
4. No internet needed for operation

---

## Support

**Check these first:**
- Terminal/console logs for errors
- API docs: `http://localhost:8000/docs`
- Browser console (F12)
- Verify configuration in `.env`

**Common fixes:**
- Restart servers
- Check PostgreSQL is running
- Verify firewall settings
- Check COM port in Device Manager

---

## License

Copyright 2025. All rights reserved.

---

## Version

**Version:** 2.0.0
**Last Updated:** November 13, 2025
**Status:** Production Ready

---

## Quick Reference

```bash
# Installation
setup-environment.bat                    # Run once as Admin
configure-firewall.bat                   # Run once as Admin

# Daily use
PRODUCTION-START-MINIMAL.bat            # Start system
PRODUCTION-STOP.bat                     # Stop system

# Access
http://localhost:5173                   # From server
http://YOUR-IP:5173                     # From network

# Backend API
http://localhost:8000/docs              # API documentation
http://localhost:8000/api/health        # Health check

# Build frontend
cd frontend && npm run build            # Creates dist/ folder

# Find server IP
ipconfig                                # Windows
```

---

**Made for industrial temperature monitoring 🔥**
