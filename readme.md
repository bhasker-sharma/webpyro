# Web Pyrometer Monitoring System

A professional, production-ready web application for real-time temperature monitoring of multiple Modbus RS485 pyrometer devices with network accessibility, historical data analysis, and multi-user support.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Database Schema](#database-schema)
- [Architecture](#architecture)
- [Network Access](#network-access)
- [Development Guide](#development-guide)
- [Troubleshooting](#troubleshooting)

## Overview

The Web Pyrometer Monitoring System is designed to monitor temperature readings from Modbus-based pyrometer devices via RS485/COM ports. It displays real-time data to multiple network users and maintains historical records for analysis and reporting.

### Key Capabilities

- Real-time monitoring of up to 16 Modbus temperature devices
- Network-accessible from any computer on the network
- WebSocket-based real-time data streaming
- Historical data storage in PostgreSQL
- CSV export with date-range filtering
- Interactive real-time temperature graphs
- Efficient background polling with buffer management
- Professional responsive UI with Tailwind CSS

## Features

### Real-time Monitoring
- Continuous polling of all configured Modbus devices
- Live temperature display with status indicators (OK, Stale, Error)
- Last update timestamp for each device
- Color-coded status visualization

### Device Management
- Configure up to 16 devices per installation
- Set device parameters: Slave ID, COM port, Baud rate, Graph visibility
- Enable/disable devices individually
- Store configurations persistently in PostgreSQL

### Data Collection & Storage
- Automatic background polling service
- Ping-pong buffer system for efficient batch database writes
- Timestamp, status, and raw hex value storage
- Support for data archiving

### Historical Data Access
- Filter readings by date/time range
- Export to CSV format
- View in tabular and graphical formats
- Calculate statistics across devices

### Real-time Visualization
- Live temperature cards with status color-coding
- Time-series graphs with sliding time windows (10 min - 3 hours)
- Multi-device overlay on single graph
- Responsive grid layout (auto-adjusts to device count)

### Network Features
- Accessible from any computer on network
- Auto-detection of network hostname/IP
- CORS enabled for cross-origin requests
- WebSocket for real-time updates to unlimited clients

## Technology Stack

### Backend
- **Framework:** FastAPI 0.118.0 (async Python)
- **Database:** PostgreSQL 12+ with SQLAlchemy 2.0.43 ORM
- **Modbus:** PyModBus 3.11.3 (Modbus RTU protocol)
- **Serial:** PySerial 3.5
- **Server:** Uvicorn 0.37.0 (ASGI)
- **Validation:** Pydantic 2.11.10

### Frontend
- **Framework:** React 19.1.1
- **Build:** Vite 6.0.0
- **Styling:** Tailwind CSS 3.4.0
- **HTTP:** Axios 1.12.2
- **Routing:** React Router DOM 7.9.3
- **Charts:** Recharts 3.3.0

## Project Structure

```
webpyro/
├── backend/                           # Python FastAPI backend
│   ├── main.py                       # Entry point, lifespan management
│   ├── requirements.txt              # Python dependencies
│   ├── .env                          # Configuration (database, modbus)
│   ├── test_modbus.py               # Modbus testing utility
│   │
│   └── app/                          # Application package
│       ├── config.py                # Pydantic settings
│       ├── database.py              # SQLAlchemy setup
│       │
│       ├── models/
│       │   └── device.py            # ORM models
│       │
│       ├── schemas/
│       │   └── device.py            # Pydantic validation schemas
│       │
│       ├── api/
│       │   ├── routes.py            # Main API endpoints
│       │   ├── devices.py           # Device CRUD endpoints
│       │   └── websocket.py         # WebSocket handler
│       │
│       └── services/                # Business logic layer
│           ├── modbus_service.py    # Modbus communication
│           ├── device_service.py    # Device CRUD logic
│           ├── polling_service.py   # Background polling loop
│           ├── buffer_service.py    # Ping-pong buffer
│           ├── reading_service.py   # Query and statistics
│           └── websocket_service.py # Connection management
│
├── frontend/                         # React + Vite
│   ├── index.html                   # HTML entry
│   ├── package.json                 # Dependencies
│   ├── vite.config.js              # Vite config
│   ├── tailwind.config.js          # Tailwind config
│   │
│   └── src/
│       ├── App.jsx                  # Root component, routing
│       ├── main.jsx                 # React entry
│       ├── index.css                # Global styles
│       │
│       ├── pages/
│       │   ├── DashboardPage.jsx    # Real-time monitoring
│       │   └── PreviewPage.jsx      # Historical data & export
│       │
│       ├── components/
│       │   ├── Navbar.jsx           # Navigation header
│       │   ├── ConfigModal.jsx      # Device configuration UI
│       │   └── GraphSection.jsx     # Real-time graphs
│       │
│       ├── services/
│       │   ├── api.js               # Axios API helpers
│       │   └── websocket.js         # WebSocket client
│       │
│       └── utils/
│           └── graphColors.js       # Color mapping
│
└── README.md                         # This file
```

### Where to Find Things

#### Adding/Modifying Features

| What You Want to Change | File to Modify | Line Reference |
|------------------------|----------------|----------------|
| **Backend** |
| Add new API endpoint | `backend/app/api/routes.py` | Add route function |
| Modbus communication logic | `backend/app/services/modbus_service.py` | modify read_temperature() |
| Polling interval/behavior | `backend/app/services/polling_service.py` | modify polling_loop() |
| Database models | `backend/app/models/device.py` | Add/modify SQLAlchemy models |
| Device CRUD operations | `backend/app/services/device_service.py` | Add/modify functions |
| Buffer batch size | `backend/app/services/buffer_service.py` | Change BUFFER_THRESHOLD |
| **Frontend** |
| Dashboard layout | `frontend/src/pages/DashboardPage.jsx` | Modify grid/card layout |
| Device card appearance | `frontend/src/pages/DashboardPage.jsx` | Modify renderDeviceCard() |
| Historical data page | `frontend/src/pages/PreviewPage.jsx` | Modify preview logic |
| Device configuration UI | `frontend/src/components/ConfigModal.jsx` | Modify form fields |
| Graph visualization | `frontend/src/components/GraphSection.jsx` | Modify chart config |
| Navigation menu | `frontend/src/components/Navbar.jsx` | Add/modify links |
| API URL configuration | `frontend/src/services/api.js` | Change baseURL |
| WebSocket connection | `frontend/src/services/websocket.js` | Modify connection logic |
| **Configuration** |
| Database connection | `backend/.env` | DATABASE_URL |
| Polling interval | `backend/.env` | MODBUS_POLL_INTERVAL |
| Modbus register settings | `backend/.env` | MODBUS_* variables |

## Installation

### Prerequisites

- Python 3.8+
- Node.js 16+
- PostgreSQL 12+
- RS485/USB converter (if using physical devices)

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Create virtual environment:
```bash
python -m venv venv
```

3. Activate virtual environment:
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

5. Create `.env` file (see Configuration section below)

6. Create PostgreSQL database:
```sql
CREATE DATABASE modbus_monitor;
```

7. Run backend server:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Run development server:
```bash
npm run dev
```

The application will be accessible at:
- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`

## Configuration

### Backend Environment Variables (.env)

Create a `.env` file in the `backend/` directory:

```env
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/modbus_monitor

# Application Settings
APP_NAME=Modbus Temperature Monitor
DEBUG=True

# Modbus Communication Settings
MODBUS_TIMEOUT=5                    # Connection timeout (seconds)
MODBUS_POLL_INTERVAL=5              # Polling interval (seconds)

# Modbus Register Settings (applied to ALL devices)
MODBUS_REGISTER_ADDRESS=4002        # Starting register address
MODBUS_FUNCTION_CODE=3              # 3=Holding Register, 4=Input Register
MODBUS_START_REGISTER=0             # Start register offset
MODBUS_REGISTER_COUNT=2             # Number of registers (1 or 2)
```

### Frontend Configuration

The frontend auto-detects the backend URL based on the current hostname:

```javascript
// In frontend/src/services/api.js
const hostname = window.location.hostname;
const apiUrl = `http://${hostname}:8000/api`;
```

For custom configuration, modify `frontend/src/services/api.js`.

## Usage

### First Time Setup

1. Start both backend and frontend servers
2. Open browser and navigate to `http://localhost:5173`
3. Click "Configure Devices" button
4. Add your Modbus devices:
   - Enter device name
   - Set Slave ID (Modbus device address)
   - Set COM port (e.g., COM3)
   - Set Baud rate (e.g., 9600)
   - Enable the device
   - Choose if device should show in graph
5. Click "Save Configuration"

### Monitoring Temperatures

- Dashboard shows real-time temperature cards
- Status colors:
  - **Green:** Reading OK
  - **Yellow:** Stale data (old reading)
  - **Red:** Error reading device
- Graphs update automatically
- Select time range (10min, 30min, 1hr, 3hr)

### Viewing Historical Data

1. Click "Preview & Export" in navbar
2. Select date/time range
3. Select device (or "All Devices")
4. Click "Apply Filter"
5. View data in table and graph
6. Click "Export CSV" to download

### Network Access

To access from other computers on the network:

1. Find server's IP address:
```bash
# Windows
ipconfig

# Linux/Mac
ifconfig
```

2. On other computers, navigate to:
```
http://<server-ip>:5173
```

Example: `http://192.168.1.100:5173`

## API Documentation

### Interactive API Docs

FastAPI provides interactive documentation:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Key Endpoints

#### Device Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/devices` | List all devices |
| GET | `/api/devices?enabled_only=true` | List enabled devices |
| POST | `/api/devices` | Create new device |
| GET | `/api/devices/{id}` | Get device by ID |
| PUT | `/api/devices/{id}` | Update device |
| DELETE | `/api/devices/{id}` | Delete device |

#### Readings

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/reading/latest` | Latest reading per device |
| GET | `/api/reading/device/{id}` | Device reading history |
| GET | `/api/reading/filter?start_time=...&end_time=...` | Filtered readings |
| GET | `/api/reading/stats` | Statistics across devices |
| GET | `/api/reading/export/csv` | Export to CSV |

#### System

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/polling/stats` | Polling statistics |
| POST | `/api/polling/restart` | Restart polling service |

#### Real-time

| Protocol | Endpoint | Description |
|----------|----------|-------------|
| WebSocket | `/api/ws` | Real-time temperature updates |

### WebSocket Message Format

```json
{
  "type": "reading_update",
  "data": {
    "device_id": 1,
    "device_name": "Pyrometer 1",
    "temperature": 450.25,
    "status": "OK",
    "raw_hex": "044E 0020",
    "timestamp": "2024-11-03T10:30:45Z"
  }
}
```

## Database Schema

### Tables

#### device_settings
Stores device configuration.

```sql
CREATE TABLE device_settings (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    slave_id INTEGER NOT NULL,
    baud_rate INTEGER NOT NULL,
    com_port VARCHAR(20) NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    show_in_graph BOOLEAN DEFAULT TRUE,
    register_address INTEGER,
    function_code INTEGER,
    start_register INTEGER,
    register_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### device_readings
Stores recent temperature readings.

```sql
CREATE TABLE device_readings (
    id BIGSERIAL PRIMARY KEY,
    device_id INTEGER REFERENCES device_settings(id) ON DELETE CASCADE,
    device_name VARCHAR(100),
    ts_utc TIMESTAMP NOT NULL,
    value FLOAT,
    status VARCHAR(10),
    raw_hex VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### reading_archive
Stores archived historical readings.

```sql
CREATE TABLE reading_archive (
    id BIGSERIAL PRIMARY KEY,
    device_id INTEGER,
    device_name VARCHAR(100),
    ts_utc TIMESTAMP NOT NULL,
    value FLOAT,
    status VARCHAR(10),
    raw_hex VARCHAR(100),
    archived_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Architecture

### Data Flow

```
┌─────────────────┐
│ Modbus Devices  │ (Physical pyrometers)
│ via RS485       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Polling Service │ (Reads every 5 seconds)
└────────┬────────┘
         │
         ├──────────────┬────────────────┐
         ▼              ▼                ▼
┌──────────────┐ ┌─────────────┐ ┌──────────────┐
│ Buffer       │ │ WebSocket   │ │ Database     │
│ Service      │ │ Broadcast   │ │ (PostgreSQL) │
└──────────────┘ └──────┬──────┘ └──────────────┘
                        │
                        ▼
                 ┌─────────────┐
                 │ Web Clients │ (Browsers)
                 │ (React App) │
                 └─────────────┘
```

### Ping-Pong Buffer System

The application uses a dual-buffer system for efficient database writes:

1. **Buffer A** collects readings while active
2. When Buffer A reaches 100 readings:
   - Switch to **Buffer B** (now active)
   - Spawn background thread to save Buffer A to database
3. Buffer B continues collecting while Buffer A saves
4. Process repeats, alternating buffers

**Benefits:**
- No data loss during database writes
- Non-blocking operation
- Efficient batch inserts (100 records per transaction)

### Modbus Communication

The system supports both 16-bit and 32-bit temperature encoding:

**16-bit (Single Register):**
```python
temperature = register_value / 10.0
# Example: 4502 → 450.2°C
```

**32-bit (Two Registers):**
```python
# Big-endian 32-bit float
byte_data = struct.pack('>HH', reg1, reg2)
temperature = struct.unpack('>f', byte_data)[0]
```

## Network Access

### Single-PC Setup
- Backend and frontend on same machine
- Access via `http://localhost:5173`

### Network Monitoring
- Backend runs on server with pyrometers connected
- Frontend accessible from any computer on network
- Auto-detects server hostname/IP
- Example: `http://192.168.1.100:5173`

### Configuration

Both servers must bind to `0.0.0.0` (all network interfaces):

**Backend:**
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
# Already configured in vite.config.js
vite --host 0.0.0.0
```

## Development Guide

### Adding a New API Endpoint

1. Define route in `backend/app/api/routes.py`:
```python
@router.get("/myendpoint")
async def my_endpoint():
    return {"message": "Hello"}
```

2. Add service logic in appropriate service file

3. Update frontend API client in `frontend/src/services/api.js`:
```javascript
export const getMyData = async () => {
    const response = await apiClient.get('/myendpoint');
    return response.data;
};
```

### Adding a New Frontend Page

1. Create component in `frontend/src/pages/MyPage.jsx`
2. Add route in `frontend/src/App.jsx`:
```javascript
<Route path="/mypage" element={<MyPage />} />
```
3. Add navigation link in `frontend/src/components/Navbar.jsx`

### Modifying Database Schema

1. Update model in `backend/app/models/device.py`
2. Update schema in `backend/app/schemas/device.py`
3. Create database migration (manual SQL or Alembic)
4. Update service layer logic

### Testing Modbus Connection

Use the provided test utility:

```bash
cd backend
python test_modbus.py
```

## Troubleshooting

### Backend Issues

**Database Connection Failed:**
- Check PostgreSQL is running
- Verify credentials in `.env`
- Ensure database exists

**Modbus Communication Error:**
- Check COM port is correct
- Verify baud rate matches device
- Ensure RS485 converter is connected
- Check device slave ID is correct
- Verify device is powered on

**Polling Service Won't Start:**
- Check `.env` configuration
- Verify at least one device is enabled
- Check logs for specific error messages

### Frontend Issues

**Cannot Connect to Backend:**
- Ensure backend is running on port 8000
- Check firewall settings
- Verify network connectivity
- Check browser console for CORS errors

**WebSocket Connection Failed:**
- Backend must be running
- Check network firewall
- Verify WebSocket endpoint: `ws://localhost:8000/api/ws`

**No Data Showing:**
- Check device configuration
- Verify devices are enabled
- Check polling service is running
- Look for errors in browser console

### Common Configuration Issues

**Wrong COM Port:**
- Windows: Use Device Manager to find correct COM port
- Linux: Check `/dev/ttyUSB*` or `/dev/ttyS*`

**Temperature Values Wrong:**
- Check register count (1 vs 2 registers)
- Verify encoding (16-bit vs 32-bit)
- Adjust division factor in `modbus_service.py`

**Slow Performance:**
- Reduce polling interval in `.env`
- Increase buffer threshold in `buffer_service.py`
- Add database indexes
- Reduce number of active devices

## Production Deployment

### Security Considerations

1. **Disable Debug Mode:**
```env
DEBUG=False
```

2. **Restrict CORS:**
```python
# In main.py, change from:
allow_origins=["*"]
# To specific domains:
allow_origins=["https://yourdomain.com"]
```

3. **Enable HTTPS:**
- Use nginx reverse proxy with SSL
- Obtain SSL certificate (Let's Encrypt)

4. **Database Security:**
- Use strong passwords
- Enable SSL connections
- Restrict network access

### Performance Optimization

1. **Database Connection Pooling:**
```python
# Already configured in database.py
pool_size=10
max_overflow=20
```

2. **Frontend Production Build:**
```bash
cd frontend
npm run build
# Serves optimized static files from dist/
```

3. **Run as Service:**
- Windows: Use NSSM or Windows Service
- Linux: Use systemd service

### Backup Strategy

1. **Database Backups:**
```bash
pg_dump modbus_monitor > backup_$(date +%Y%m%d).sql
```

2. **Configuration Backups:**
- Backup `.env` file
- Backup device configuration

## License

Copyright 2025. All rights reserved.

## Support

For issues and questions:
- Check logs in terminal/console
- Review this README
- Check API documentation at `/docs`
- Verify configuration settings

---

**Version:** 1.0.0
**Last Updated:** November 3, 2025
**Status:** Production Ready