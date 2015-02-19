# -*- coding: utf-8 -*-

import datetime
import re
import db
import utils
import os
import glob
import excelreader
import textreader

try:
    import logger
    log = logger.getlogger()
except:
    import logging
    log = logging.getlogger()


class Text2DB(object):
    """Read all parameters from database,
        run sql query, and write resultset to text file
        default to tab delimited file format

        Keyword arguments:
        taskid -- int -- task number

    """

    def __init__(self, taskid, conn):
        self.taskid = taskid
        self.conn = conn

    def run(self):
        """
        Run task, dont need to return job_status as previous, let program throw Exception,
        and catch Exception at outer level
        """
        cur = self.conn.cursor()
        myvars = dict(taskid=self.taskid)
        # This should run at outer level

        #cur.execute("""
        #    UPDATE tasks
        #    set error=null, when_start=now(), status='processing'
        #    where id = %(taskid)s
        #""", myvars)

        cur.execute("""SELECT a.key_value from vars_tasks a
        INNER JOIN tasks b on a.jobid = b.jobid
        WHERE b.id=%(taskid)s
        """, myvars)

        environment_vars = cur.fetchall()

        cur.execute("""
            SELECT *
            FROM import_tasks
            WHERE taskid = %(taskid)s
        """, myvars)

        result = cur.fetchone()


        delimiter = result.delimited_or_sheet_index
        tablename = utils.lm_simplify(0, result.table_name)

        appendToTable = result.append
        field_names = result.field_names

        headers = field_names.split(',')
        #headers = [x for x in headers if x not in ['mm_key', 'mm_origseq', 'mm_fn', 'mm_sheet_index']]

        # Allow mm_origseq, mm_sheet_index and mm_fn not in orders
        headers = [x for x in headers if x not in ['mm_key']]
        #--- Overule appendSeq, if mm_origseq, mm_fn, or mm_sheet_index already exists
        overrule = 'mm_origseq' in headers \
            or 'mm_fn' in headers \
            or 'mm_sheet_index' in headers
        # Support wild card, using glob
        original_data_files = utils.mm_translate(result.original_data_file, environment_vars)

        filelist = glob.glob(original_data_files)
        if not filelist:
            filelist = [original_data_files]

        for original_data_file in filelist:
            log.info(original_data_file)
            basename = os.path.basename(original_data_file)
            pathname = os.path.dirname(original_data_file)
            filename = os.path.join(pathname, basename)
            #if '.xls' in filename.lower() or '.xlsx' in filename.lower():
            if filename.lower().endswith('.xls') or filename.lower().endswith('.xlsx'):
                texter = excelreader.ExcelReader(filename, sheet_index=int(delimiter), has_header=True)
            else:
                if '\\t' in delimiter:
                    delimiter = delimiter.decode('string_escape')
                texter = textreader.TextReader(filename, delimiter=delimiter, has_header=True)

            # each file import seperately to temp table
            t_tablename = '_' + tablename

            # Bulk insert into temp table first
            texter.bulk2db(self.conn, t_tablename, appendseq=True, append=False)

            # Take into account mm_key, and selected field names
            # drop table if exists
            # re-create new sequence for primary key
            create_table_query = """
            DROP TABLE IF EXISTS {0}
            ;
            DROP SEQUENCE IF EXISTS {0}_seq
            ;
            CREATE SEQUENCE {0}_seq
            ;
            CREATE TABLE {0} (
                  mm_key int not null
            """.format(tablename)

            if not overrule:
                create_table_query += """
                 ,mm_origseq int not null
                 ,mm_fn text not null
                 ,mm_sheet_index text not null
            """

            select_table_query = "INSERT INTO {0} \
                                 SELECT nextval('{0}_seq'), "
            if not overrule:
                select_table_query += "mm_origseq, mm_fn, mm_sheet_index, "

            select_field_query1 = ''
            select_field_query2 = ''
            for header_field in headers:
                if header_field.startswith('[') and header_field.endswith(']'):
                    header_field = header_field[1:-1]
                    select_field_query2 += "''::text,"
                elif ' as ' in header_field:
                    select_field_query2 += "{0},".format(header_field)
                    original_field, new_field = header_field.split(' as ')
                    select_field_query1 += "{0},".format(new_field)
                    header_field = new_field
                else:
                    select_field_query1 += "{0},".format(header_field)
                    select_field_query2 += "{0},".format(header_field)


                header_field = utils.lm_simplify(0, header_field)

                create_table_query += ",{0} text default ''\n".format(header_field)

            # check for alias

            select_table_query = select_table_query + select_field_query2[:-1] + " FROM {1}"

            #select_table_query = select_table_query.format(tablename, t_tablename, select_field_query1[:-1])
            select_table_query = select_table_query.format(tablename, t_tablename)

            create_table_query += """
            ,CONSTRAINT fn_{0}_pk PRIMARY KEY (mm_key)

            )""".format(tablename)
            # ,CONSTRAINT fn_{0}_uk UNIQUE (mm_origseq, mm_fn, mm_sheet_index)
            # if appendtoTable, dont re-create table structure
            if not appendToTable:
                cur.execute(create_table_query)

            log.info(select_table_query)
            cur.execute(select_table_query)

            # if multiple files, automatically append
            appendToTable = True

            #drop temp table
            cur.execute("drop table if exists {0}".format(t_tablename))

if __name__ == '__main__':

    startTime = datetime.datetime.now()
    conn = db.get_connection()
    app = Text2DB(1058, conn)    #1174 is
    # import blueillusion 147,000 in 0:01:00.507000
    # 0:00:41.549000
    # 0:00:22.072000

    app.run()

    conn.commit()
    log.info(datetime.datetime.now() - startTime)