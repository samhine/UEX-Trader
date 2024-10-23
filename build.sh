#!/bin/bash
pyinstaller --noconfirm --onedir --windowed --icon ".\resources\uextrader_icon_resized_idL_icon.ico" --add-data ".\resources;resources/"  ".\main.py"
