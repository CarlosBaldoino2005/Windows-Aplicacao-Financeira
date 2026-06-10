@echo off
REM OPCIONAL — nao usado por gerar_apk.bat (celular usa API Render).
REM Apenas para build manual com API local no celular, se precisar:
REM   flutter build apk --dart-define=API_BASE_URL=%API_CELULAR_URL%
set API_CELULAR_URL=http://192.168.0.10:8000
