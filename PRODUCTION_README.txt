================================================================================
                          MULTI TEMPERATURE MONITOR
                    IRQ Pyrometer Monitoring System
                  Toshniwal Industries Private Limited
================================================================================

QUICK START GUIDE FOR PRODUCTION DEPLOYMENT

================================================================================
WHAT'S INCLUDED
================================================================================

This package contains:
- MULTI TEMPERATURE Monitor Software (Backend + Frontend)
- User Guide (USER_GUIDE.txt) - For customers
- Installation Guide (INSTALLATION_GUIDE.txt) - For engineers
- Production deployment scripts

================================================================================
FOR ENGINEERS - FIRST-TIME SETUP
================================================================================

If this is the FIRST TIME installing on a new computer:
→ See INSTALLATION_GUIDE.txt for detailed setup instructions

You need to:
1. Install PostgreSQL database
2. Install Python 3.11+
3. Create database "modbus_monitor"
4. Configure .env file
5. Configure Windows Firewall

================================================================================
FOR CUSTOMERS - DAILY OPERATION
================================================================================

If the software is already installed and configured:
→ See USER_GUIDE.txt for operation instructions

Quick start:
1. Run PRODUCTION-START-MINIMAL.bat (as Administrator)
2. Open browser: http://localhost
3. Monitor your IRQ Pyrometers

================================================================================
SYSTEM REQUIREMENTS
================================================================================

REQUIRED:
- Windows 10/11 (64-bit)
- PostgreSQL 14 or later (Database)
- Python 3.11 or later (Frontend server)
- Administrator rights (for port 80)
- RS485 to USB adapter (for IRQ Pyrometers)

NETWORK:
- Port 80: Frontend web interface
- Port 8000: Backend API server
- Both must be allowed in Windows Firewall

================================================================================
STARTING THE SOFTWARE
================================================================================

METHOD 1: Using Batch File (Recommended)
   - Right-click: PRODUCTION-START-MINIMAL.bat
   - Select: "Run as administrator"
   - Click "Yes" when prompted
   - Wait for both servers to start (5-10 seconds)

METHOD 2: Manual Start
   Backend:
   - Navigate to: backend\dist\webpyro_backend\
   - Run: webpyro_backend.exe

   Frontend:
   - Navigate to: frontend\dist\
   - Run: python -m http.server 80

⚠️ IMPORTANT: Always run as Administrator (required for port 80)

================================================================================
ACCESSING THE SOFTWARE
================================================================================

From Server Computer:
   http://localhost
   or
   http://COMPUTERNAME

From Other Computers (Network):
   http://COMPUTERNAME
   or
   http://SERVER-IP-ADDRESS

To Find Server IP:
   - Open Command Prompt
   - Type: ipconfig
   - Look for "IPv4 Address"
   - Example: 192.168.1.100

================================================================================
STOPPING THE SOFTWARE
================================================================================

METHOD 1: Using Batch File (Recommended)
   - Double-click: PRODUCTION-STOP.bat
   - Both servers will stop gracefully

METHOD 2: Manual Stop
   - Close Backend Server window
   - Close Frontend Server window
   - Or press Ctrl+C in each window

================================================================================
CONFIGURATION FILES
================================================================================

Main Configuration:
   Location: backend\dist\webpyro_backend\.env
   (Or: backend\.env for development)

Key Settings:
   DATABASE_URL          - PostgreSQL connection string
   APP_NAME              - Application name
   CONFIG_PIN            - 4-digit device configuration PIN
   DATA_RETENTION_DAYS   - How long to keep data (days)
   LOG_RETENTION_DAYS    - How long to keep logs (days)
   MODBUS_POLL_INTERVAL  - Polling frequency (seconds)

⚠️ IMPORTANT: Restart backend after changing .env settings!

================================================================================
FOLDER STRUCTURE
================================================================================

webpyro/
├── PRODUCTION-START-MINIMAL.bat    ← Start here!
├── PRODUCTION-STOP.bat             ← Stop servers
├── USER_GUIDE.txt                  ← Customer operation guide
├── INSTALLATION_GUIDE.txt          ← Engineer setup guide
├── PRODUCTION_README.txt           ← This file
│
├── backend/
│   ├── dist/webpyro_backend/       ← Production backend
│   │   ├── webpyro_backend.exe     ← Backend executable
│   │   ├── .env                    ← Main configuration
│   │   └── logs/                   ← Application logs
│   │
│   └── [development files]
│
└── frontend/
    ├── dist/                       ← Production frontend
    │   ├── index.html              ← Web interface
    │   └── assets/                 ← CSS, JS, images
    │
    └── [development files]

================================================================================
TROUBLESHOOTING
================================================================================

PROBLEM: "Port 80 already in use"
SOLUTION:
   - Close Skype (uses port 80)
   - Stop IIS service if installed
   - Run as Administrator
   - Check for other web servers

PROBLEM: "Database connection failed"
SOLUTION:
   - Check PostgreSQL service is running (services.msc)
   - Verify DATABASE_URL in .env file
   - Ensure database "modbus_monitor" exists
   - Test connection using pgAdmin

PROBLEM: Backend won't start
SOLUTION:
   - Check .env file exists
   - Verify database is running
   - Check port 8000 is available
   - Review logs in: backend\logs\

PROBLEM: Can't access from network
SOLUTION:
   - Run configure-firewall.bat as Administrator
   - Check both computers on same network
   - Use IP address instead of computer name
   - Verify firewall allows ports 80 and 8000

PROBLEM: IRQ Pyrometer shows "Error"
SOLUTION:
   - Check device is powered on
   - Verify RS485 cable connected
   - Check COM port in Device Manager
   - Verify Instrument ID matches device
   - Ensure baud rate matches device (usually 9600)

================================================================================
DATA RETENTION & LOGS
================================================================================

Database Data:
   - Retention period: Configurable (default: 2 days)
   - Old data automatically deleted
   - Export important data to PDF/CSV before deletion

Log Files:
   - Location: backend\dist\webpyro_backend\logs\DD-MM-YYYY\
   - Retention period: Configurable (default: 2 days)
   - Organized by date folders
   - Automatic cleanup of old logs

Log Types:
   - app.log: General application logs
   - errors.log: All errors
   - modbus.log: IRQ Pyrometer communication
   - database.log: Database operations
   - api.log: API requests
   - websocket.log: Real-time connections
   - retention.log: Data cleanup operations

================================================================================
SECURITY NOTES
================================================================================

✓ Change CONFIG_PIN in .env file (default: 1234)
✓ Use strong PostgreSQL password
✓ Firewall configured for local network only
✓ No data sent to internet
✓ All data stays on local computer/network
✓ PIN-protected device configuration

✗ DO NOT expose to public internet
✗ DO NOT use default CONFIG_PIN in production
✗ DO NOT share database password

================================================================================
SYSTEM SPECIFICATIONS
================================================================================

Software:
   Name: MULTI TEMPERATURE Monitor
   Version: 2.0
   Type: IRQ Pyrometer Monitoring System
   Built: December 2025
   Developer: Toshniwal Industries Private Limited

Technology:
   Backend: Python (FastAPI, SQLAlchemy, Pymodbus)
   Frontend: React (Vite, Recharts, TailwindCSS)
   Database: PostgreSQL
   Communication: Modbus RTU/RS485, WebSocket

Supported Devices:
   - IRQ Pyrometers (Modbus RTU/RS485)
   - Baud Rate: 300-115200 (default: 9600)
   - Device IDs: 1-16
   - Maximum Devices: 16 simultaneous
   - Protocol: Modbus RTU

Features:
   ✓ Real-time temperature monitoring
   ✓ WebSocket live updates (no refresh needed)
   ✓ Multi-device support (up to 16)
   ✓ Temperature graphing with zoom
   ✓ PDF export with company header
   ✓ CSV export for Excel
   ✓ Automatic data retention
   ✓ Date-based log management
   ✓ Network access support
   ✓ PIN-protected configuration

================================================================================
SUPPORT & DOCUMENTATION
================================================================================

User Documentation:
   - USER_GUIDE.txt: Daily operation instructions
   - INSTALLATION_GUIDE.txt: First-time setup guide
   - PRODUCTION_README.txt: This file

Technical Support:
   Toshniwal Industries Private Limited
   Technical Support Team

Check Logs:
   - Location: backend\dist\webpyro_backend\logs\
   - Current date folder: DD-MM-YYYY
   - errors.log for error messages

API Documentation:
   - URL: http://localhost:8000/docs
   - Interactive API testing available

================================================================================
VERSION INFORMATION
================================================================================

Current Version: 2.0
Release Date: December 2025
Build Type: Production

Changes in v2.0:
- Date-based log folder organization
- Automatic log retention management
- Enhanced data retention system
- Improved error handling and logging
- WebSocket real-time updates
- Enhanced PDF export with company branding
- Multi-device graph support
- Responsive mobile design
- Network access optimization

================================================================================
IMPORTANT REMINDERS
================================================================================

BEFORE DEPLOYMENT:
□ PostgreSQL installed and running
□ Database "modbus_monitor" created
□ .env file configured with correct DATABASE_URL
□ CONFIG_PIN changed from default
□ Firewall rules configured (run configure-firewall.bat)
□ Python 3.11+ installed
□ RS485 adapters installed and drivers loaded

AFTER DEPLOYMENT:
□ Test local access (http://localhost)
□ Test network access from other computers
□ Configure IRQ Pyrometer devices
□ Verify temperature readings appear
□ Test PDF/CSV export functionality
□ Schedule regular data backups
□ Document network IP addresses
□ Train users on operation

MAINTENANCE:
□ Export important data regularly (PDF/CSV)
□ Backup PostgreSQL database weekly
□ Monitor disk space (logs folder)
□ Check for communication errors in logs
□ Test disaster recovery procedures
□ Keep spare RS485 adapters

================================================================================
                           PRODUCTION READY!

     For operation instructions, see: USER_GUIDE.txt
     For setup instructions, see: INSTALLATION_GUIDE.txt
================================================================================

Developed by: Toshniwal Industries Private Limited
Version: 2.0 | December 2025

For technical support, contact Toshniwal Industries Technical Support Team
================================================================================
