"""Build a single-file portable Windows bundle with project-local caches."""
from pathlib import Path
import os
import shutil
import sys

ROOT = Path(__file__).resolve().parent
if sys.platform != 'win32':
    raise SystemExit('Build Stillpin on Windows x64 with Python 3.12 and Tcl/Tk.')
work = ROOT / 'work'
work.mkdir(exist_ok=True)
os.environ['TEMP'] = str(work)
os.environ['TMP'] = str(work)
os.environ['PYINSTALLER_CONFIG_DIR'] = str(work / 'pyinstaller-cache')
import PyInstaller.__main__

PyInstaller.__main__.run([
    '--noconfirm', '--windowed', '--onefile', '--name', 'Stillpin',
    '--icon', str(ROOT / 'assets' / 'Stillpin.ico'),
    '--add-data', str(ROOT / 'assets') + os.pathsep + 'assets',
    '--distpath', str(ROOT / 'dist'), '--workpath', str(work / 'build'),
    '--specpath', str(work), '--paths', str(ROOT / 'src'),
    '--exclude-module', 'matplotlib', '--exclude-module', 'pandas',
    '--exclude-module', 'numpy', '--exclude-module', 'scipy',
    '--exclude-module', 'PyQt5', '--exclude-module', 'PySide6',
    str(ROOT / 'src' / 'app.py'),
])
