__version__ = 1.0

import datetime
import psycopg2
import psycopg2.extras
import db
import dedupe

try:
    import logger
    log = logger.getlogger()
except:
    import logging
    log = logging.getlogger()


class DeDupeDB(object):
    def __init__(self, taskid, conn):
        self.taskid = taskid
        self.conn = conn
    
    def run(self):

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
            FROM dedupe_tasks
            WHERE taskid = %(taskid)s
        """, myvars)

        result = cur.fetchone()
            
        src_table = result.src_table
        unique_table = result.unique_table
        dupe_table = result.dupe_table
        d_method = result.d_method
        raw_args = result.args

        temp_obj = raw_args.split("\n")

        deduper = dedupe.DeDupe(d_method, src_table, dupe_table, unique_table, temp_obj, self.conn)
        deduper.update_grpkey()
        deduper.dedupe()



if __name__ == '__main__':

    startTime = datetime.datetime.now()
    conn = db.get_connection()
    app = DeDupeDB(335, conn)
    app.run()
    conn.commit()
    log.info(datetime.datetime.now() - startTime)