@echo off
chcp 65001 >nul
title Text Mapper Pro - Build

echo ========================================
echo   TEXT MAPPER PRO - Build
echo ========================================
echo.

cd /d "%~dp0"

:: Checando Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [X] Python não encontrado!
    echo     Baixe em: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo [OK] Python instalado
python --version

:: Checando PyInstaller
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo.
    echo     PyInstaller não encontrado, instalando...
    pip install pyinstaller
    if errorlevel 1 (
        echo [X] Não foi possível instalar o PyInstaller
        pause
        exit /b 1
    )
    echo [OK] PyInstaller pronto!
) else (
    echo [OK] PyInstaller instalado
)

:: Checando chardet
pip show chardet >nul 2>&1
if errorlevel 1 (
    echo.
    echo     chardet não encontrado, instalando...
    pip install chardet
)

echo.
echo ========================================
echo   Gerando executável...
echo ========================================
echo.

pyinstaller --onefile --windowed --icon=image.ico TEXT_MAPPER_PRO_1.4.1.py

if errorlevel 1 (
    echo.
    echo [X] Erro no build!
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Pronto!
echo ========================================
echo.
echo Arquivo: %~dp0dist\TEXT_MAPPER_PRO_1.4.1.exe
echo.
pause