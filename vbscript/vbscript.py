# -*- coding: utf-8 -*-

import os
import export2db
import db
import cStringIO
import utils
import datetime
import psycopg2
#import psycopg2.extras.DictCursor
import re
from win32com.client import Dispatch

try:
    import logger
    log = logger.getlogger()
except:
    import logging
    log = logging.getlogger()


class VBScript(object):
    def __init__(self, taskid, conn):
        self.taskid = taskid
        self.conn = conn

    def run(self):
        """
        Run task, dont need to return job_status as previous, let program throw Exception,
        and catch Exception at outer level
        """
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        myvars = dict(taskid=self.taskid)
        # This should run at outer level

        #cur.execute("""
        #    UPDATE tasks
        #    set error=null, when_start=now(), status='processing'
        #    where id = %(taskid)s
        #""", myvars)
        log.info(self.taskid)
        cur.execute("""SELECT a.key_value from vars_tasks a
        INNER JOIN tasks b on a.jobid = b.jobid
        WHERE b.id=%(taskid)s
        """, myvars)

        environment_vars = cur.fetchall()

        cur.execute("""
            SELECT *
            FROM vbscript_tasks
            WHERE taskid = %(taskid)s
        """, myvars)

        result = cur.fetchone()

        source_code = result['source_code']

        params = utils.mm_translate(result['params'], environment_vars)

        params_list = []

        if params:
            params_list = re.findall(r'["]{3}(.+?)["]{3}', params, re.S)

            new_params_list = []
            for param in params_list:
                try:
                    param.index('\r\n')
                    temp_list = param.split('\r\n')
                    temp_list = map(lambda x: '"'+x+'"', temp_list)
                    new_params_list.append('& vbCr & vbLf &'.join(temp_list))

                except ValueError:
                    new_params_list.append('"%s"' % param)
                params_list = new_params_list


        log.info(params_list)
        main_func = 'Main(%s)' % ','.join(params_list)

        log.info(main_func)
        x = Dispatch("MSScriptControl.ScriptControl")
        x.Language='VBScript'
        x.TimeOut = 300000  # in milli seconds - 5mins
        log.info(source_code)
        x.AddCode(source_code)

        retcode = x.Eval(main_func)

        if retcode > 0:
            raise RuntimeError("Something Wrong")


if __name__ == '__main__':
    startTime = datetime.datetime.now()
    con = db.get_connection()
    app = VBScript(1224, con)
    #0:03:38.474000 with 1,000 for 147,000 recs #using batch update
    #0:00:47.978000 #export to file, bulk import back result--> faster
    app.run()
    con.commit()
    log.info(datetime.datetime.now() - startTime)


