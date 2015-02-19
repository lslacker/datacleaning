__author__ = 'luan'

import db
from celery import Celery
from celery import Task
import traceback
import sys
import datetime
import math
import re
import jpype

app = Celery('daemon',
             broker='amqp://guest@localhost//',
             backend='db+postgresql://joboperators:abc123@10.0.6.12/register',
             )

# Optional configuration, see the application user guide.
app.conf.update(
    CELERY_TASK_RESULT_EXPIRES=3600,
)

jarpath = r'D:\0_works\pycharm_projects\datacleaning\javarunner\ManifestExporterWrapper'
jpype.startJVM(jpype.getDefaultJVMPath(), "-Djava.ext.dirs=%s" % jarpath)


class DatabaseTask(Task):
    abstract = True
    _conn = None

    @property
    def conn(self):
        if self._conn is None:
            self._conn = db.get_connection()
        return self._conn

@app.task(base=DatabaseTask)
def run_tasks(jobid, userid):
    """thread worker function"""


    cur = run_tasks.conn.cursor()
    cur.execute("""
    INSERT INTO jobs_lock(jobid, userid, celery_id, status) values (%s, %s, %s, 'running')
    """, (jobid, userid, run_tasks.request.id))

    run_tasks.conn.commit()

    cur.execute("""
    SELECT * FROM tasks
    WHERE jobid = %s and status=%s
    ORDER BY canonical_order
    """, (jobid, 'waiting'))

    tasks = cur.fetchall()
    print 'no of tasks: ', len(tasks)
    is_error = False
    for task in tasks:
        startTime = datetime.datetime.now()
        cur.execute("SELECT * FROM tasktype WHERE task_type=%s", (task.task_type,))
        python_class = cur.fetchone().python_class
        print python_class
        module, submodule, classname = re.split('[.]', python_class)

        if module == 'export':
            module = 'export2db'
        if module == 'dedupedb':
            module = 'dedupe'
        m = __import__(module)
        func = getattr(m, submodule)
        Class = getattr(func, classname)
        cur.execute("""
            UPDATE tasks
            SET error=%s, status=%s, when_start=now()
            WHERE id=%s
            """, ('', 'processing', task.id))
        run_tasks.conn.commit()
        try:

            kclass = Class(task.id, run_tasks.conn)
            if module == 'manifest':
                # For some reason, when task is run via celery, variable jpype can not be initiased within run method
                # at module level, it has to be initialised here at global and pass as params via method call
                a = kclass.run(jpype)
            else:
                a = kclass.run()
            cur.execute("""
            UPDATE tasks
            SET error=%s, status=%s
            WHERE id=%s
            """, (a, 'done', task.id))
        except:
            run_tasks.conn.rollback()
            is_error = True
            exc_type, exc_value, exc_traceback = sys.exc_info()
            message = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
            print message

            cur.execute("""
            UPDATE tasks
            SET error=%s, status=%s
            WHERE id=%s
            """, (message, 'error', task.id))

        finally:
            duration = int(math.ceil((datetime.datetime.now() - startTime).total_seconds()))

            cur.execute("""
            UPDATE tasks
            SET duration=%s
            WHERE id=%s
            """, (duration, task.id))

            if is_error and task.continue_on_error == 0:
                break

    if is_error:
        status = 'error'
    else:
        status = 'done'

    cur.execute("""
    UPDATE jobs_lock
    set status=%s
    WHERE jobid=%s and status='running'
    """, (status, jobid))

    #notify user
    cur.execute("""
    INSERT INTO sys_message(message, sender, receiver) VALUES (%s, %s, %s)
    """, ('JobID {0} has completed with status {1}'.format(str(jobid), status), 'celery', userid))

    run_tasks.conn.commit()
    #run_tasks.conn.close()

    return 1

#jpype.shutdownJVM()
if __name__ == "__main__":

    from tasks import run_tasks

    result = run_tasks.delay(5, 1)

    while not result.ready():
        pass

    print 'Done'