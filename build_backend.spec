# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['backend/server.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('backend/.env', '.'),
        ('backend/credentials.json', '.'),
        ('backend/token.json', '.'),
        ('backend/database', 'database'),
        ('backend/voice_engine', 'voice_engine'),
        ('backend/automation', 'automation'),
        ('backend/llm', 'llm'),
        ('backend/scripts', 'scripts')
    ],
    hiddenimports=[
        'engineio.async_drivers.asgi',
        'socketio',
        'fastapi',
        'uvicorn',
        'sqlalchemy',
        'google.auth',
        'googleapiclient',
        'pyaudio',
        'numpy',
        'openwakeword',
        'speech_recognition',
        'pyttsx3',
        'groq'
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
    name='backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='backend',
)
