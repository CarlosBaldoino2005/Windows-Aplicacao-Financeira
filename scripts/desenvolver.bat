@echo off
REM Script de desenvolvimento - Financeiro
REM Duplo clique ou: scripts\desenvolver.bat

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0desenvolver.ps1" %*
pause
