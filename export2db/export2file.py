# -*- coding: utf-8 -*-

import textwriter
import excelwriter
import psycopg2
import psycopg2.extras
import utils
import cStringIO
import datetime
import db

try:
    import logger
    log = logger.getlogger()
except:
    import logging
    log = logging.getlogger()


class Export2File(object):
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
            FROM export_tasks
            WHERE taskid = %(taskid)s
        """, myvars)

        result = cur.fetchone()

        src_table = result.src_table
        filename = utils.mm_translate(result.dest_file, environment_vars)
        field_names = result.field_names
        filter_ = result.filter

        if '.txt' in filename.lower():
            texter = textwriter.TextWriter(filename)
            params = """WITH DELIMITER AS '\t' NULL AS '\N' CSV HEADER ENCODING 'utf-8'"""
        elif '.csv' in filename.lower():
            texter = textwriter.TextWriter(filename)
            params = """WITH DELIMITER AS ',' NULL AS '\N' CSV HEADER QUOTE AS '"' FORCE QUOTE * ENCODING 'utf-8'"""
        elif '.bat' in filename.lower():
            texter = textwriter.TextWriter(filename)
            params = """WITH DELIMITER AS ',' NULL AS '\N' ENCODING 'utf-8'"""
        elif '.xlsx' in filename.lower():
            texter = excelwriter.ExcelWriter(filename)
            params = """WITH DELIMITER AS '\t' NULL AS '\N' CSV HEADER ENCODING 'utf-8'"""
        else:
            raise RuntimeError('Only support .txt, .csv, .bat, and .xlsx')

        select_query = "SELECT {0} FROM {1} {2}".format(field_names, src_table, filter_)
        output = cStringIO.StringIO()
        cur.copy_expert("COPY ({0}) TO STDOUT {1}".format(select_query, params), output)
        texter.write(output)
        texter.save()
        output.close()

if __name__ == '__main__':

    startTime = datetime.datetime.now()
    conn = db.get_connection()
    app = Export2File(1099, conn)
    app.run()
    conn.commit()
    log.info(datetime.datetime.now() - startTime)