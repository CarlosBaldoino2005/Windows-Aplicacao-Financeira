@echo off
cd /d "%~dp0.."
set PYTHONPATH=%CD%
venv\Scripts\python.exe -c "from src.Tool.relatorio_agendado_executor import executar_ciclo_relatorio_agendado; r=executar_ciclo_relatorio_agendado(); print('executado:', r.executado); print('mensagem:', r.mensagem); print('pdf:', r.caminho_pdf)"
pause
