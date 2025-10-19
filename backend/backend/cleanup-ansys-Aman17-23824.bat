@echo off
set LOCALHOST=%COMPUTERNAME%
if /i "%LOCALHOST%"=="Aman17" (taskkill /f /pid 27008)
if /i "%LOCALHOST%"=="Aman17" (taskkill /f /pid 30832)
if /i "%LOCALHOST%"=="Aman17" (taskkill /f /pid 3728)
if /i "%LOCALHOST%"=="Aman17" (taskkill /f /pid 23824)

del /F cleanup-ansys-Aman17-23824.bat
