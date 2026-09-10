# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files

root = Path(SPECPATH).parent

datas = [
    (str(root / "desktop" / "index.html"), "desktop"),
    (str(root / "toolkit" / "schemas"), "toolkit/schemas"),
]
for phase in (root / "toolkit").glob("phase-*"):
    datas.append((str(phase), str(Path("toolkit") / phase.name)))

a = Analysis(
    [str(root / "desktop" / "server.py")],
    pathex=[str(root)],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name="ContentSkillsFramework", debug=False, bootloader_ignore_signals=False, strip=False, upx=True, console=False)
