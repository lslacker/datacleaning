import datetime
import psycopg2
import psycopg2.extras
import db
import utils
import os
import glob

try:
    import logger
    log = logger.getlogger()
except:
    import logging
    log = logging.getlogger()


class Casing(object):
    def __init__(self, taskid, conn):
        self.taskid = taskid
        self.conn = conn

    def to_query(self, fieldstr, fieldtype):
        result = ''
        if fieldstr:
            field_list = fieldstr.split(',')
            for field in field_list:
                result += "{0}=titlecase({0}, '{1}'),".format(field, fieldtype)
        return result


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
            FROM titlecase_tasks
            WHERE taskid = %(taskid)s
        """, myvars)

        result = cur.fetchone()

        src_table = result.src_table
        address = result.address
        name = result.name
        company = result.company
        position = result.position

        query = "UPDATE {0} SET ".format(src_table)

        query += self.to_query(address, 'ADDRESS')
        query += self.to_query(name, 'NAME')
        query += self.to_query(company, 'COMPANY')
        query += self.to_query(position, 'POSITION')

        if query.endswith(','):
            query = query[:-1]
        log.info(query)

        cur.execute(query)


if __name__ == '__main__':
    startTime = datetime.datetime.now()
    conn = db.get_connection()
    app = Casing(247, conn)
    # import blueillusion 147,000 in
    app.run()
    conn.commit()
    log.info(datetime.datetime.now() - startTime)

