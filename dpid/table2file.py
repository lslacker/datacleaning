#!/usr/bin/python
# table2file.py

__version__ = 1.0

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

sys.path.append(r'D:\0_works\pyhon_projects\new_cmd')
sys.path.append(r'D:\0_works\pyhon_projects\_lib')
from myutils import mmutils
from database import database
from export import export2text
import dtconfig
import os
import time

class Table2File(object):
    def __init__(self, table_name):
        self.table_name = table_name

    def set_table(self, table_name):
        self.table_name = table_name

    def run(self, dest_file):
        show_column_query = """
            select column_name from information_schema.columns
            where table_name='%s'
            order by ordinal_position
        """ % self.table_name
        results = dtconfig.DB.query(show_column_query)
        header_fields = []

        for result in results:
            header_fields.append(result['column_name'])

        app = export2text.Export2Text(dest_file)
        app.write_header(tuple(header_fields))

        results = dtconfig.DB.select(self.table_name);
        for result in results:
            app.write_row(result)

        app.save()

class Table2Access(object):
    def __init__(self, table_name):
        self.table_name = table_name

    def set_table(self, table_name):
        self.table_name = table_name

    def create_access_db(self, dest_file):
        try:
            os.remove(dest_file)
        except:
            pass
        finally:
            import win32com.client
            cat = win32com.client.Dispatch(r'ADOX.Catalog')
            cat.Create("Provider=Microsoft.Jet.OLEDB.4.0;Data Source=%s" % dest_file)


    def run(self, dest_file):
        #create access database sa dest_file

        self.create_access_db(dest_file)

        show_column_query = """
            select column_name, data_type from information_schema.columns
            where table_name='%s'
            order by ordinal_position
        """ % self.table_name
        results = dtconfig.DB.query(show_column_query)

        create_query = 'CREATE TABLE %s (\n' % self.table_name

        header_fields = []
        for result in results:
            field_name = result['column_name']
            header_fields.append(field_name)
            data_type = result['data_type']
            create_query += "[%s] %s\n," % (field_name, data_type)

        create_query = create_query[:-2] + ')'

        import pyodbc

        con = pyodbc.connect('Driver={Microsoft Access Driver (*.mdb)};Dbq=%s;Uid=;Pwd=;' % dest_file)

        cur = con.cursor()
        try:
            cur.execute("DROP TABLE %s" % self.table_name)
        except pyodbc.ProgrammingError, e:
            print sys.exc_info()[0]

        cur.execute(create_query)

        results = dtconfig.DB.select(self.table_name)

        insert_query = 'INSERT INTO %s values (%s' % (self.table_name, '?,'*len(header_fields))
        insert_query = insert_query[:-1] + ')'

        print insert_query
        rows = []
        for result in results:
            row = []
            for a_header in header_fields:
                row.append(result[a_header])
            rows.append(row)

        cur.executemany(insert_query, rows)

        con.commit()




if __name__ == '__main__':

    app = Table2Access('lu_alfred_clean_final')
    app.create_access_db(r'd:\luan1.mdb')
    app.run(r'd:\luan1.mdb')
