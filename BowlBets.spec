# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Add all Python source files
a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('USER_GUIDE.md', '.'),  # Include user guide in root of bundle
    ],
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'requests',
        'dateutil',
        'sqlite3',
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='LineLock',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window (GUI app)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# For macOS, create an .app bundle
app = BUNDLE(
    exe,
    name='LineLock.app',
    icon=None,  # macOS requires .icns format, not .ico
    bundle_identifier='com.linelock.app',
    info_plist={
        'NSHighResolutionCapable': 'True',
        'CFBundleName': 'LineLock',
        'CFBundleDisplayName': 'LineLock',
        'CFBundleVersion': '2.0.0',
        'CFBundleShortVersionString': '2.0',
        'NSHumanReadableCopyright': '© 2025 LineLock',
    },
)
