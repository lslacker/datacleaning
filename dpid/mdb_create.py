#!/usr/bin/env python

#import win32com.client
#
#
#cat = win32com.client.Dispatch(r'ADOX.Catalog')
#cat.Create("Provider=Microsoft.Jet.OLEDB.4.0;Data Source=db.mdb")

import pyodbc

con = pyodbc.connect('Driver={Microsoft Access Driver (*.mdb)};Dbq=db.mdb;Uid=;Pwd=;')


cur = con.cursor()
string = "CREATE TABLE TestTable(symbol varchar(15), leverage double, shares integer, price double)"
cur.execute(string)

con.commit()


