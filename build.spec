# -*- mode: python ; coding: utf-8 -*-
#
# PyInstaller spec — ALS Research Database
# macOS: pyinstaller build.spec  →  dist/ALS Research Database.app
# Windows: pyinstaller build.spec  →  dist/ALS Research Database.exe
#
import sys

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 사용하지 않는 PySide6 모듈 제외
        'PySide6.Qt3DAnimation',
        'PySide6.Qt3DCore',
        'PySide6.Qt3DExtras',
        'PySide6.Qt3DInput',
        'PySide6.Qt3DLogic',
        'PySide6.Qt3DRender',
        'PySide6.QtAxContainer',
        'PySide6.QtBluetooth',
        'PySide6.QtCharts',
        'PySide6.QtDataVisualization',
        'PySide6.QtDesigner',
        'PySide6.QtGraphs',
        'PySide6.QtLocation',
        'PySide6.QtMultimedia',
        'PySide6.QtMultimediaWidgets',
        'PySide6.QtNetwork',
        'PySide6.QtNfc',
        'PySide6.QtOpenGL',
        'PySide6.QtOpenGLWidgets',
        'PySide6.QtPositioning',
        'PySide6.QtPrintSupport',
        'PySide6.QtQml',
        'PySide6.QtQuick',
        'PySide6.QtQuickControls2',
        'PySide6.QtQuickWidgets',
        'PySide6.QtRemoteObjects',
        'PySide6.QtScxml',
        'PySide6.QtSensors',
        'PySide6.QtSerialBus',
        'PySide6.QtSerialPort',
        'PySide6.QtSpatialAudio',
        'PySide6.QtSql',
        'PySide6.QtStateMachine',
        'PySide6.QtSvg',
        'PySide6.QtSvgWidgets',
        'PySide6.QtTest',
        'PySide6.QtUiTools',
        'PySide6.QtWebChannel',
        'PySide6.QtWebEngineCore',
        'PySide6.QtWebEngineQuick',
        'PySide6.QtWebEngineWidgets',
        'PySide6.QtWebSockets',
        'PySide6.QtXml',
        # 불필요한 표준 라이브러리
        'tkinter',
        'unittest',
        'email',
        'html',
        'http',
        'urllib',
        'xmlrpc',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# ── macOS ────────────────────────────────────────────────────────────────────
if sys.platform == 'darwin':
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name='ALS Research Database',
        debug=False,
        bootloader_ignore_signals=False,
        strip=True,
        upx=False,
        console=False,
        disable_windowed_traceback=False,
        codesign_identity=None,   # 코드서명 시: 'Developer ID Application: ...'
        entitlements_file=None,
    )
    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=True,
        upx=False,
        upx_exclude=[],
        name='ALS Research Database',
    )
    app = BUNDLE(
        coll,
        name='ALS Research Database.app',
        icon=None,                # 아이콘 추가 시: 'assets/icon.icns'
        bundle_identifier='kr.ac.als-research-db',
        info_plist={
            'CFBundleDisplayName': 'ALS Research Database',
            'CFBundleShortVersionString': '1.1.0',
            'CFBundleVersion': '1.1.0',
            'NSHighResolutionCapable': True,
            'LSMinimumSystemVersion': '11.0',
        },
    )

# ── Windows ──────────────────────────────────────────────────────────────────
else:
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name='ALS Research Database',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,
        disable_windowed_traceback=False,
        icon=None,                # 아이콘 추가 시: 'assets/icon.ico'
    )
