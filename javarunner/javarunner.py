import datetime
import psycopg2
import psycopg2.extras
import db
import utils
import os
import subprocess
import glob


try:
    import logger
    log = logger.getlogger()
except:
    import logging
    log = logging.getlogger()


class JavaRunner(object):
    def __init__(self, taskid, conn):
        self.taskid = taskid
        self.conn = conn

    def run_program_1(self, jar_file, args=''):
        error = None
        try:
            open(jar_file)  # to test if jar file path is correct
            cmd_line = 'java -Xmx1024m -jar %s' % jar_file
            if args:
                cmd_line = cmd_line + ' ' + args
            pipe = subprocess.Popen(cmd_line, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            output, error = pipe.communicate()
            if 'Exception' in output:
                error = output
            else:
                log.info(output)
        except IOError, e:
            error = str(e)
            log.error(error)

        return error

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
            FROM javarunner_tasks
            WHERE taskid = %(taskid)s
        """, myvars)

        result = cur.fetchone()
            
        jar_file = utils.mm_translate(result.dest_file, environment_vars)
        arguments = utils.mm_translate(result.args, environment_vars)

        error_msg = self.run_program_1(jar_file, arguments)

        if error_msg:
            log.error(error_msg)
            raise RuntimeError(error_msg)

if __name__ == '__main__':

    startTime = datetime.datetime.now()
    con = db.get_connection()
    app = JavaRunner(1121, con)
    app.run()
    con.commit()
    log.info(datetime.datetime.now() - startTime)
