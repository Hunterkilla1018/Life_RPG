@echo off
setlocal enabledelayedexpansion

echo ===============================
echo   Life RPG Release Script
echo ===============================

REM ---- Ask for version number ----
set /p VERSION=Enter version number (example 1.1.4): 

if "%VERSION%"=="" (
    echo Version cannot be empty.
    pause
    exit /b 1
)

set TAG=v%VERSION%

echo.
echo Releasing version %TAG%
echo -------------------------------

REM ---- Show status ----
git status
echo.

REM ---- Add and commit ----
git add .
git commit -m "Release %TAG%"

REM ---- Delete tag if it already exists ----
git tag -d %TAG% >nul 2>&1
git push --delete origin %TAG% >nul 2>&1

REM ---- Create new tag ----
git tag %TAG%

REM ---- Push everything ----
git push
git push --tags

echo.
echo ===============================
echo   Release %TAG% pushed!
echo ===============================
echo.
echo GitHub Actions will now build LifeRPG.exe
echo Check GitHub -> Actions -> Releases
echo.

pause
