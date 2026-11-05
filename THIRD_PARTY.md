# Third-party notices

Stillpin uses unmodified third-party runtimes and libraries. Their individual licenses remain applicable.

| Component | Version used for v1.0.0 | License / official source |
| --- | --- | --- |
| Python | 3.12.10 | PSF license; [Python](https://www.python.org/), notice in licenses/Python_LICENSE.txt |
| Tcl/Tk | 8.6 | Tcl/Tk license; [Tcl/Tk](https://www.tcl-lang.org/), bundled notices and licenses/Tk_license.terms |
| Pillow | 11.1.0 | HPND and component notices; [Pillow](https://github.com/python-pillow/Pillow), licenses/pillow_LICENSE |
| PyMuPDF / MuPDF | 1.27.2.3 distribution | AGPL v3 or Artifex commercial; [PyMuPDF source](https://github.com/pymupdf/PyMuPDF/tree/1.27.2.3), [MuPDF source](https://github.com/ArtifexSoftware/mupdf); licenses/pymupdf_COPYING and LICENSE |
| PyInstaller | 6.22.3 | GPL with bootloader exception; [PyInstaller](https://github.com/pyinstaller/pyinstaller), licenses/pyinstaller_COPYING.txt |

The Windows package contains their runtime files; additional bundled notices remain alongside those files. Source dependency versions are pinned in requirements.txt. Pytest is used only for development tests.

The Stillpin application source and build script corresponding to the release are provided in this repository and the release source archive. No reference content or session data is included in the public release.
