# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Pyrometer Desktop Application
This file defines how to build the standalone executable
"""

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect all hidden imports
hiddenimports = [
    'uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.lifespan',
    'uvicorn.lifespan.on',
    'fastapi',
    'starlette',
    'starlette.routing',
    'starlette.middleware',
    'starlette.middleware.cors',
    'sqlalchemy',
    'sqlalchemy.ext.declarative',
    'sqlalchemy.orm',
    'pydantic',
    'pydantic_settings',
    'pymodbus',
    'pymodbus.client',
    'pymodbus.client.serial',
    'pyserial',
    'serial',
    'serial.tools',
    'serial.tools.list_ports',
    'serial.tools.list_ports_windows',
    'APScheduler',
    'apscheduler.schedulers.asyncio',
    'apscheduler.triggers.cron',
    'websockets',
    'numpy',
    'reportlab',
    'reportlab.pdfgen',
    'reportlab.lib',
    'reportlab.lib.pagesizes',
    'reportlab.lib.styles',
    'reportlab.platypus',
    'webview',
]

# Collect data files
datas = []

# Add frontend build files (from backend/frontend where we copied the built files)
frontend_dir = 'frontend'
if os.path.exists(frontend_dir):
    datas.append((frontend_dir, 'frontend'))
    print(f"[OK] Including frontend files from: {os.path.abspath(frontend_dir)}")
else:
    print(f"[WARNING] Frontend directory not found at: {os.path.abspath(frontend_dir)}")
    print("  Make sure to build frontend and copy to backend/frontend before building exe!")

# Add .env file for configuration
env_file = '.env'
if os.path.exists(env_file):
    datas.append((env_file, '.'))
    print(f"[OK] Including .env file from: {os.path.abspath(env_file)}")
else:
    print(f"[WARNING] .env file not found at: {os.path.abspath(env_file)}")

# Add any additional data files (logos, icons, etc.)
# datas.append(('path/to/icon.ico', '.'))

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PyrometerMonitor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # Disabled UPX to reduce antivirus false positives
    console=False,  # Set to False for GUI app (no console window)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join('..', 'assets', 'icon.ico') if os.path.exists(os.path.join('..', 'assets', 'icon.ico')) else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,  # Disabled UPX to reduce antivirus false positives
    upx_exclude=[],
    name='PyrometerMonitor',
)
