@echo off
rem Serve the site locally and open it. Double-click this file, or run it from a
rem terminal. Ctrl-C in the window that opens stops the server.
rem
rem Why a server is needed at all: every page is markup plus data, and a browser
rem blocks a local page from reading its own data files. Opening index.html
rem directly still works, but the pages read a mirror of data/ instead and say so.

setlocal
cd /d "%~dp0"

where py >nul 2>nul && (
  py tools\serve.py %*
  goto :eof
)
where python >nul 2>nul && (
  python tools\serve.py %*
  goto :eof
)

echo Python was not found on PATH.
echo Install it from https://www.python.org/downloads/ and tick "Add to PATH",
echo or open the site with any other static server from this folder.
pause
