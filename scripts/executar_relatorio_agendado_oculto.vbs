' Executa o relatorio agendado sem abrir janela do Prompt (100%% oculto).
Option Explicit

Dim pastaScript, pastaRaiz, pythonw, runner, comando, shell, fso

Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

pastaScript = fso.GetParentFolderName(WScript.ScriptFullName)
pastaRaiz = fso.GetAbsolutePathName(pastaScript & "\..")
pythonw = pastaRaiz & "\venv\Scripts\pythonw.exe"
runner = pastaRaiz & "\src\Tool\relatorio_agendado_runner.py"

If Not fso.FileExists(pythonw) Then
    WScript.Echo "pythonw.exe nao encontrado. Execute instalar_agendador_relatorio.bat primeiro."
    WScript.Quit 1
End If

comando = """" & pythonw & """ """ & runner & """"
shell.CurrentDirectory = pastaRaiz
' 0 = janela oculta
shell.Run comando, 0, False
