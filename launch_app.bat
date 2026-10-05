@echo off
REM Script de lancement pour Windows
REM ================================

echo.
echo 🏗️  Application de Détection de Fissures
echo ========================================
echo.

REM Vérifier que Python est installé
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python non trouvé. Installez Python 3.8+ depuis https://python.org
    pause
    exit /b 1
)

REM Vérifier que nous sommes dans le bon répertoire
if not exist "app.py" (
    echo ❌ Fichier app.py non trouvé. Assurez-vous d'être dans le bon répertoire.
    pause
    exit /b 1
)

REM Lancer l'application
echo 🚀 Lancement de l'application...
echo.
python launch_app.py

REM Pause si erreur
if errorlevel 1 (
    echo.
    echo ❌ Erreur lors du lancement
    pause
)
