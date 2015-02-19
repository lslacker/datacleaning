#!/usr/bin/python
# text2db.py
import utils
import re
import datetime
import db
import psycopg2
import psycopg2.extras

__version__ = 1.0

try:
    import logger
    log = logger.getlogger()
except:
    import logging
    log = logging.getlogger()


class StarTrack(object):

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

        cur.execute("""select a.* from startrack_tasks a
            inner join courier_file_format b
                  on a.field_name = b.field_name
            where a.taskid = %(taskid)s
            order by b.id
            """ % myvars)

        results = list(cur.fetchall())

        src_table = results[0].src_table
        dest_file = utils.mm_translate(results[0].dest_file, environment_vars)

        writer = open(dest_file, 'w')

        cur1 = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur1.execute('select * from {0} order by mm_origseq::int'.format(src_table))

        data_rows = cur1.fetchall()


        now = datetime.datetime.now()
        fn = now.strftime("%y%m%d%H%M%S")
        writer.write("00| 6.00|%s\n" % fn)

        for data_row in list(data_rows):
            a_line = []

            for result in results:

                field_value = result.field_value
                field_name = result.field_name
                max_length = result.field_length

                temp_obj = re.match(r'[$]F[{](.+?)[}]', field_value, re.I)
                if temp_obj:
                    temp_field_value = temp_obj.group(1)
                    try:
                        field_value = (data_row[temp_field_value])

                        if field_name == 'Weight':
                            try:
                                field_value = float(field_value)
                                field_value = '%.0f' % round(field_value,0)
                            except ValueError:
                                pass
                    except KeyError:
                        all_vars = re.split(r'[*/+-]+', temp_field_value)
                        for each_var in all_vars:
                            try:
                                temp_ = str(float(data_row[each_var]))
                                temp_field_value = temp_field_value.replace(each_var, temp_)
                            except KeyError:
                                pass


                        temp_field_value = eval(temp_field_value)
                        if field_name == 'TotalCubic':
                            temp_field_value = round(temp_field_value,3)*1000

                        field_value = '%.0f' % temp_field_value
                else:
                    field_value = utils.mm_translate(field_value, environment_vars)

                buffer_str = (' '*max_length)

                if isinstance(field_value,int):
                    field_value = str(field_value)

                final_field = str(field_value) + buffer_str

                final_field = final_field[:max_length]

                a_line.append(final_field)

            writer.write('|'.join(a_line))
            writer.write('\n')

        writer.close()

if __name__ == '__main__':

    startTime = datetime.datetime.now()
    conn = db.get_connection()
    app = StarTrack(1236, conn)
    app.run()
    conn.commit()
    log.info(datetime.datetime.now() - startTime)