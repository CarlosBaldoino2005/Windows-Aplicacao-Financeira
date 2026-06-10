@echo off
setlocal EnableDelayedExpansion

REM Libera a porta 8000 no firewall do Windows para o celular na mesma Wi-Fi.
REM Execute uma vez: clique direito - Executar como administrador.

net session >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERRO: execute como Administrador.
    echo Clique direito em liberar_api_rede.bat -^> Executar como administrador
    echo.
    pause
    exit /b 1
)

netsh advfirewall firewall delete rule name="Financeiro API TCP 8000" >nul 2>&1
netsh advfirewall firewall add rule name="Financeiro API TCP 8000" dir=in action=allow protocol=TCP localport=8000 profile=private
if errorlevel 1 (
    echo Falha ao criar regra de firewall.
    pause
    exit /b 1
)

echo.
echo Firewall: porta 8000 liberada na rede privada ^(Wi-Fi de casa^).
echo.
echo IPs para o celular ^(teste no navegador do aparelho^):
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    set "_ip=%%a"
    set "_ip=!_ip:~1!"
    echo   http://!_ip!:8000/api/saude
)
echo.
echo Depois: executar_api.bat aberto + app Financeiro no celular.
echo.
pause
