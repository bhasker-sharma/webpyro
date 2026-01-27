# -*- mode: python ; coding: utf-8 -*-
import os

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        # Include .env files for configuration
        ('.env', '.'),
        ('.env.production', '.'),
        # Include static files (logo for PDF reports)
        ('app/static', 'app/static'),
        # NOTE: 'app' package Python code is automatically compiled into .exe - NOT included as source!
    ],
    hiddenimports=[
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
        'pydantic',
        'pydantic_settings',
        'sqlalchemy',
        'sqlalchemy.dialects.postgresql',
        'sqlalchemy.pool',
        'sqlalchemy.ext.declarative',
        'psycopg2',
        'pymodbus',
        'pymodbus.client',
        'serial',
        'serial.tools',
        'serial.tools.list_ports',
        'websockets',
        'numpy',
        'reportlab',
        'reportlab.lib',
        'reportlab.lib.pagesizes',
        'reportlab.lib.colors',
        'reportlab.lib.units',
        'reportlab.lib.enums',
        'reportlab.lib.styles',
        'reportlab.platypus',
        'reportlab.platypus.doctemplate',
        'reportlab.platypus.tables',
        'reportlab.platypus.paragraph',
        'reportlab.platypus.flowables',
        'reportlab.graphics',
        'reportlab.pdfbase',
        'reportlab.pdfbase.pdfmetrics',
        'reportlab.pdfbase.ttfonts',
        'reportlab.rl_config',
        'app',
        'app.api',
        'app.models',
        'app.schemas',
        'app.services',
    ],
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
    name='webpyro_backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Keep console window to see server logs
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # You can add an icon file path here if you have one
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='webpyro_backend',
)
