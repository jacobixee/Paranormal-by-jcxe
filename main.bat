@echo off

:: Sprawdź, czy Python jest zainstalowany
python --version 2>NUL
if %errorlevel% neq 0 (
    echo Python nie jest zainstalowany na tym urządzeniu. Rozpoczynanie instalacji Pythona...
    :: Tutaj możesz dodać kod instalujący Pythona
    :: Przykład dla Windows 64-bit:
    :: bitsadmin /transfer pythonInstaller https://www.python.org/ftp/python/3.9.7/python-3.9.7-amd64.exe %TEMP%\python-installer.exe
    :: %TEMP%\python-installer.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0

    :: Sprawdź ponownie, czy Python został zainstalowany
    python --version 2>NUL
    if %errorlevel% neq 0 (
        echo Instalacja Pythona nie powiodła się. Spróbuj zainstalować Pythona ręcznie.
        pause
        exit
    ) else (
        echo Python został pomyślnie zainstalowany.
    )
)

:: Sprawdź, czy pip jest zainstalowany
pip --version 2>NUL
if %errorlevel% neq 0 (
    echo pip nie jest zainstalowany na tym urządzeniu. Rozpoczynanie instalacji pipa...
    :: Tutaj możesz dodać kod instalujący pipa
      py -m pip install [options] <requirement specifier> [package-index-options] ...
py -m pip install [options] -r <requirements file> [package-index-options] ...
py -m pip install [options] [-e] <vcs project url> ...
py -m pip install [options] [-e] <local project path> ...
py -m pip install [options] <archive url/path> ...
    :: Przykład: python -m ensurepip

    :: Sprawdź ponownie, czy pip został zainstalowany
    pip --version 2>NUL
    if %errorlevel% neq 0 (
        echo Instalacja pipa nie powiodła się. Spróbuj zainstalować pipa ręcznie.
        pause
        exit
    ) else (
        echo pip został pomyślnie zainstalowany.
    )
)

:: Przeniesienie skryptu do folderu autostartu
cd /d "%~dp0"
copy "%~dp0main.bat" "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"

:: Uruchom skrypt Pythona
start /min "" python.exe main.py

exit
