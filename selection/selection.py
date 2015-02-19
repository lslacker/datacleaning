
import db
import utils
import datetime

try:
    import logger
    log = logger.getlogger()
except:
    import logging
    log = logging.getlogger()

class Selection(object):
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
            FROM selection_tasks
            WHERE taskid = %(taskid)s
        """, myvars)

        result = cur.fetchone()

        # Basic param binding
        # Uhm, is it good enough?
        # Keep thing simple :-)
        sql_query = utils.mm_translate(result.sql_query, environment_vars)
            
        cur.execute(sql_query)

        log.info(cur.rowcount)

if __name__ == '__main__':

    startTime = datetime.datetime.now()
    con = db.get_connection()
    app = Selection(1377, con)
    app.run()
    con.commit()
    log.info(datetime.datetime.now() - startTime)