@echo off
REM Build Job Tracker Windows executable
echo Installing build dependencies...
pip install -r requirements.txt -r requirements-build.txt
echo.
echo Building executable...
pyinstaller jobtracker.spec
echo.
echo Done. Executable: dist\JobTracker.exe
