"""Ponto de entrada do executável eqpress-nucleo (PyInstaller): o mesmo que `python -m eqpress`."""
import sys

from eqpress.__main__ import main

if __name__ == "__main__":
    sys.exit(main())
