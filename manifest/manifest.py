import datetime
import psycopg2
import psycopg2.extras
import db
import utils
import jpype
import re
import os
import glob

try:
    import logger
    log = logger.getlogger()
except:
    import logging
    log = logging.getlogger()


class ManifestExporter(object):
    def __init__(self, taskid, conn):
        self.taskid = taskid
        self.conn = conn

    
    def run(self, jpype):
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
            FROM manifest_tasks
            WHERE taskid = %(taskid)s
        """, myvars)

        result = cur.fetchone()
                                             
        filename = utils.mm_translate(result.src_file, environment_vars)
        _directory = '\\'.join(re.split(r'\\', filename)[:-1]) + '\\'
        filename = re.split(r'\\', filename).pop()
        job = long(utils.mm_translate(result.job, environment_vars))
        try:
            weight = long(utils.mm_translate(result.weight, environment_vars))
        except ValueError:
            weight = 0L

        manifest = result.manifest != ''
        minimum = result.minimum != ''
        excel = result.excel != ''
        return_mail = result.return_mail != ''
        split = result.split != ''
        sort_method = int(result.sort_method)


        Exporter = jpype.JClass('Exporter')  # get the class
        exporter = Exporter(_directory + "\\", filename, job, manifest, return_mail, split, sort_method, weight, minimum
                            , excel)
        exporter.run()
        error = exporter.getSummary()

        if error:
            raise RuntimeError(error)

if __name__ == '__main__':
    jarpath = r'D:\0_works\pycharm_projects\datacleaning\javarunner\ManifestExporterWrapper'
    jpype.startJVM(jpype.getDefaultJVMPath(), "-Djava.ext.dirs=%s" % jarpath)
    startTime = datetime.datetime.now()
    conn = db.get_connection()
    app = ManifestExporter(475, conn)
    app.run(jpype)
    conn.commit()
    jpype.shutdownJVM()
    log.info(datetime.datetime.now() - startTime)

