@echo off
chcp 65001 >nul
title SIGRH — Importar Banco de Horas FOPA
cd /d "%~dp0"
echo.
echo PDFs em: C:\Users\hmauricio\Desktop\RH\BANCO_HORAS
echo.
python importar_banco_horas_fopa.py %*
echo.
pause
