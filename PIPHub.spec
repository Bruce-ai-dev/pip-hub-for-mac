# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['pip_desktop.py'],
    pathex=[],
    binaries=[],
    datas=[('facebookicon.svg.webp', '.'), ('tiktokicon.webp', '.'), ('youtubeicon.webp', '.'), ('netflexicon.webp', '.'), ('icon-fake', 'icon-fake'), ('chamden.png', '.'), ('conruoi.png', '.'), ('smile.webp', '.'), ('star.png', '.'), ('Donate-nen.png', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PIPHub',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['icon.icns'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PIPHub',
)
app = BUNDLE(
    coll,
    name='PIPHub.app',
    icon='icon.icns',
    bundle_identifier='com.chungbruce.piphub',
    info_plist={
        'NSPrincipalClass': 'NSApplication',
        'NSAppleScriptEnabled': False,
        'NSRequiresAquaSystemAppearance': False,
        'LSEnvironment': {
            'LANG': 'en_US.UTF-8',
            'LC_CTYPE': 'en_US.UTF-8'
        }
    }
)
