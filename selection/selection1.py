#!/usr/bin/env python
import sqlite3
import sys

def execute_query(dbname, query_txt_file, isFile=True):
    content=[]
    if isFile == True:
        f = open(query_txt_file, 'r')
        content = f.readlines()
        f.close()
    else:
        content.append(query_txt_file+' ')
    query = ''
    queries=[]
    for eachStatement in content:
        
        if eachStatement.startswith(';'):
            if query != '':
                queries.append(query)
            query = ''
        else:
            query = query + '\n'+eachStatement[:-1]
    if query != '':
        queries.append(query)
    print dbname
    print query_txt_file
    connection = sqlite3.connect(dbname)
    connection.isolation_level='DEFERRED'
    cursor = connection.cursor()
    
    
    try:
        for index, query in enumerate(queries):
            print 'Executing Query %d=%s' % (index+1, query)
            cursor.execute(query)
    except sqlite3.OperationalError:
        connection.rollback()
        sys.exit("Something wrong with this %s" % query)
    
    
    cursor.close()
    connection.commit()
    connection.close()

if __name__ == '__main__':
    if len(sys.argv) < 3:
        sys.exit("3 arguments: dbname, query")
    
    dbname = sys.argv[1]
    query_txt_file = sys.argv[2]
    
    execute_query(dbname, query_txt_file,False)
    
    