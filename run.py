# -*- coding: utf-8 -*-
import import2db
import export2db
import db
import cStringIO
import logger
from datetime import datetime


log = logger.getlogger()


def test_xlsx_import(conn):
    fpath = r'N:\jno39038\workingData'
    #fpath = '/home/lslacker/downloads/data_for_testing'
    fn = ['260514_Stream1 Lost.xls']
    reader = import2db.excelreader.ExcelReader(fpath + '\\' + fn[0],
                                           sheet_index=0, has_header=True)
    if reader.bulk2db(conn, 'lu_openuni'):
        conn.commit()
    else:
        log.info("rollbak")
        conn.rollback()
    conn.commit()


def test_text_import(conn):
    fpath = r'N:\jno39038\workingData'
    #fpath = '/home/lslacker/downloads/data_for_testing'
    fn = ['260514_Stream1 Lost.xls']
    reader = import2db.textreader.TextReader(fpath + '\\' + fn[0], delimiter='0', has_header=True)

    if reader.bulk2db(conn, 'lu_test_2', appendseq=True):
        conn.commit()
    else:
        log.info("rollbak")
        conn.rollback()

def test_text_export(conn):
    fpath = r'N:\jno99999\workingData'
    #fpath = '/home/lslacker/downloads/data_for_testing'
    fn = ['luan.txt']
    writer = export2db.textwriter.TextWriter(fpath + '\\' + fn[0])
    output = cStringIO.StringIO()
    cur = conn.cursor()
    cur.copy_expert("COPY lu_new_clean TO STDOUT WITH DELIMITER as '\t' ", output)
    output.seek(0)
    writer.write(output)

    conn.commit()
    output.close()

def test_xlsx_export(conn):
    fpath = r'N:\jno39038\workingData'
    #fpath = '/home/lslacker/downloads/data_for_testing'
    fn = ['260514_Stream1 Lost.xls']
    writer = export2db.excelwriter.ExcelWriter(fpath + '\\' + fn[0])
    output = cStringIO.StringIO()
    cur = conn.cursor()
    cur.copy_expert("COPY lu_adma TO STDOUT WITH DELIMITER as '\t' CSV HEADER", output)
    output.seek(0)
    writer.write(output, 'lu_adma')

    conn.commit()
    output.close()

if __name__ == '__main__':
    startTime = datetime.now()
    conn = db.get_connection()
    #test_text_import(conn)
    test_xlsx_import(conn)
    #test_text_export(conn)
    #test_xlsx_export(conn)
    conn.commit()
    log.info(datetime.now() - startTime)
