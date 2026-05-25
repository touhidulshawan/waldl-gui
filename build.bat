@echo off
REM ─────────────────────────────────────────────────────────────
REM  build.bat  —  Build WallhavenDownloader for Windows
REM  Produces: dist\WallhavenDownloader.exe  (single binary)
REM ─────────────────────────────────────────────────────────────

echo =^> Checking Python...
python --version
IF %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python not found. Install from https://python.org
    pause
    exit /b 1
)

echo =^> Creating build venv...
python -m venv .venv-build
IF %ERRORLEVEL% NEQ 0 goto :error

call .venv-build\Scripts\activate.bat

echo =^> Installing dependencies...
pip install --upgrade pip -q
pip install -r requirements.txt pyinstaller -q
IF %ERRORLEVEL% NEQ 0 goto :error

echo =^> Running PyInstaller...
pyinstaller wallhaven.spec ^
    --distpath dist ^
    --workpath build ^
    --noconfirm ^
    --clean
IF %ERRORLEVEL% NEQ 0 goto :error

echo.
echo ====================================================
echo  Build complete!
echo  Executable: %CD%\dist\WallhavenDownloader.exe
echo ====================================================
echo.

REM Create a convenience launcher batch
echo @echo off > run.bat
echo start "" "%%~dp0dist\WallhavenDownloader.exe" >> run.bat

call .venv-build\Scripts\deactivate.bat
pause
exit /b 0

:error
echo.
echo ERROR: Build failed. See output above.
call .venv-build\Scripts\deactivate.bat 2>nul
pause
exit /b 1
