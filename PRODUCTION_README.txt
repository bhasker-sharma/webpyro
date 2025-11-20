========================================
WEB PYROMETER - PRODUCTION DEPLOYMENT
========================================

QUICK START GUIDE
-----------------

REQUIREMENTS:
- Windows 10/11
- PostgreSQL installed and running
- Administrator rights (for port 80)
- NO Python or Node.js needed!

INSTALLATION STEPS:
-------------------

1. CONFIGURE DATABASE:
   - Open: backend\dist\webpyro_backend\.env
   - Update DATABASE_URL with your PostgreSQL details
   - Format: postgresql://username:password@localhost:5432/database_name
   - Example: postgresql://postgres:admin@123@localhost:5432/modbus_monitor

2. CONFIGURE FIREWALL (if needed):
   - Allow port 80 (frontend)
   - Allow port 8000 (backend)
   - Run Windows Firewall with Advanced Security:
     * New Inbound Rule -> Port -> TCP -> 80,8000 -> Allow

3. START THE SYSTEM:
   - Right-click: PRODUCTION-START-MINIMAL.bat
   - Select: "Run as administrator"
   - Two windows will open (Backend & Frontend)
   - Keep both windows open while running

4. ACCESS THE SYSTEM:
   - Same computer: http://localhost
   - From network: http://COMPUTER-NAME
   - Or use IP: http://192.168.x.x

STOPPING THE SYSTEM:
--------------------
- Option 1: Run PRODUCTION-STOP.bat
- Option 2: Close both server windows

TROUBLESHOOTING:
----------------

Backend won't start:
- Check .env file exists
- Verify database is running
- Check port 8000 is free

Frontend won't start:
- Check if running as administrator
- Verify port 80 is free
- Check frontend\dist folder exists

Can't access from network:
- Check Windows Firewall
- Verify computer name/IP
- Both computers on same network?

FOLDER STRUCTURE:
-----------------
WebPyrometer_Production/
├── PRODUCTION-START-MINIMAL.bat  (Start here!)
├── PRODUCTION-STOP.bat
├── backend/dist/webpyro_backend/ (Backend executable + config)
└── frontend/dist/                (Web interface)

IMPORTANT FILES:
----------------
- backend/dist/webpyro_backend/.env          (Main configuration)
- backend/dist/webpyro_backend/.env.production (Production settings)

SUPPORT:
--------
For user guide, see USER_GUIDE.txt

========================================
Version: 1.0
Built: 2025
========================================
