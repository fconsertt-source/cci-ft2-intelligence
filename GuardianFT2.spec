# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# ============================================================
# 🔍 اكتشاف مسار Python الأساسي
# ============================================================

python_base = Path(sys.base_prefix)
tcl_root = python_base / "tcl"
tcl_dir = tcl_root / "tcl8.6"
tk_dir = tcl_root / "tk8.6"

if not tcl_dir.exists() or not tk_dir.exists():
    raise SystemExit(
        f"[GuardianFT2] Tcl/Tk not found.\n"
        f"Expected:\n{tcl_dir}\n{tk_dir}"
    )

print(f"[GuardianFT2] Using TCL from: {tcl_dir}")
print(f"[GuardianFT2] Using TK  from: {tk_dir}")

# ============================================================
# 📦 تجميع بيانات tkinter بشكل صريح
# ============================================================

tkinter_datas = collect_data_files("tkinter", include_py_files=False)
tkinter_hidden = collect_submodules("tkinter")

datas = tkinter_datas + [
    (str(tcl_dir), "tcl/tcl8.6"),
    (str(tk_dir), "tcl/tk8.6"),
    ("assets/fonts", "assets/fonts"),
    ("src/shared/fonts", "src/shared/fonts"),
    ("src/shared/locales", "src/shared/locales"),
]

hiddenimports = tkinter_hidden + [
    "_tkinter",
    "reportlab",
    "reportlab.pdfbase.ttfonts",
    "reportlab.platypus",
    "pdfminer",
    "arabic_reshaper",
    "bidi.algorithm",
    "src.application.app_composer",
    "src.infrastructure.adapters.reporting.pdf_strategy",
    "src.infrastructure.adapters.reporting.unified_pdf_generator_wrapper",
]

# ============================================================
# 🧱 إعدادات عامة
# ============================================================

block_cipher = None

entry_script = r"src/presentation/cli/gui_main.py"
app_name = "GuardianFT2"

# ============================================================
# 🚀 Analysis
# ============================================================

a = Analysis(
    [entry_script],
    pathex=[os.getcwd()],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=["./hooks"],
    hooksconfig={},
    runtime_hooks=["runtime_hooks/tkinter_init.py"],
    excludes=[
        "matplotlib",
        "numpy.tests",
        "pytest",
        "IPython",
    ],
    noarchive=False,
)

# ============================================================
# 📦 PYZ
# ============================================================

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# ============================================================
# 🧩 EXE
# ============================================================

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=app_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # GUI app
    disable_windowed_traceback=False,
)

# ============================================================
# 📦 COLLECT
# ============================================================

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name="windows",
)
