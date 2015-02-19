from win32com.client import Dispatch
x = Dispatch("MSScriptControl.ScriptControl")
x.Language='VBScript'
x.AddCode("""
Function Main(filename)
Dim Stuff, myFSO, WriteStuff, dateStamp
dateStamp = Date()

'Write information to Text File
Stuff = "Whatever you want written" & dateStamp

Set myFSO = CreateObject("Scripting.FileSystemObject")
Set WriteStuff = myFSO.OpenTextFile("d:/"&filename, 8, True)
WriteStuff.WriteLine(Stuff)
WriteStuff.Close
SET WriteStuff = NOTHING
SET myFSO = NOTHING
Main = 0
End Function

""")

a= x.Eval('Main("bla.txt")')
if a == 0:
    print 'correct'
else:
    print 'incorrent'

