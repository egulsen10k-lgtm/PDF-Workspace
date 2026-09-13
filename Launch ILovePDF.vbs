' Double-click this file on Windows. Starts the app with no Command Prompt window.
Option Explicit
Dim fso, sh, root, py, launcher
Set fso = CreateObject("Scripting.FileSystemObject")
Set sh  = CreateObject("WScript.Shell")
root = fso.GetParentFolderName(fso.GetParentFolderName(WScript.ScriptFullName))
launcher = root & "\desktop\launcher.py"

If fso.FileExists(root & "\venv\Scripts\pythonw.exe") Then
  py = root & "\venv\Scripts\pythonw.exe"
ElseIf fso.FileExists(root & "\venv\Scripts\python.exe") Then
  py = root & "\venv\Scripts\python.exe"
Else
  py = "pythonw.exe"
End If

sh.CurrentDirectory = root
sh.Run """" & py & """ """ & launcher & """", 0, False
