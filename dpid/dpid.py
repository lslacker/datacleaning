
import os
import datawizard
import export2db
import db
import cStringIO
import utils
import datetime

try:
    import logger
    log = logger.getlogger()
except:
    import logging
    log = logging.getlogger()


DEFAULT_TEMPLATE = """
[PREPROCESS TEMPLATE]
DATABASEINPUT=0

[ASCII]
FILENAME=%s
SEPARATOR=TAB
FIELDNAMEFIRST=1
FIXEDLENGTH=0
StartQuoteChar="
EndQuoteChar="
RemoveText="
"""

ACCESSDB_TEMPLATE= """
[PREPROCESS TEMPLATE]
DATABASEINPUT=1

[DATABASE]
DATABASENAME=%s
TABLENAME=%s
"""


class DPID(object):

    def __init__(self, taskid, conn):
        self.taskid = taskid
        self.conn = conn

    def generate_tpl(self, txt_filename, field_list, tpl_filename, src_table=None):
        if txt_filename.endswith('.txt'):
            blink_template = DEFAULT_TEMPLATE % txt_filename
        else:
            blink_template = ACCESSDB_TEMPLATE % (txt_filename, src_table)

        extra_list = []

        while len(field_list) > 7:
            #postcode
            extra_list.insert(0, field_list.pop())

        if extra_list:
            field_list[-1] = field_list[-1]+','+','.join(extra_list)

        for idx, a_field in enumerate(field_list):
            blink_template += "Adr%d=%s\n" % (idx+1, a_field)

        #write to tpl
        out_file = open(tpl_filename, "w")

        # Write all the lines at once:
        out_file.writelines(blink_template)
        out_file.close()

        log.info(blink_template)

    def generate_text_file(self, src_table, filename, cur):
        texter = export2db.textwriter.TextWriter(filename)
        params = """WITH DELIMITER AS '\t' NULL AS '' CSV HEADER"""
        select_query = "SELECT * FROM {0}".format(src_table)
        output = cStringIO.StringIO()
        cur.copy_expert("COPY ({0}) TO STDOUT {1}".format(select_query, params), output)
        texter.write(output)
        texter.save()
        output.close()


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
            FROM dpid_tasks
            WHERE taskid = %(taskid)s
        """, myvars)

        result = cur.fetchone()

        addresses = result.addresses

        suburb = result.suburb
        state = result.state
        postcode = result.postcode
        src_table = result.src_table
        filename = utils.mm_translate(result.dest_file, environment_vars)

        FILEEXT = '.txt'
        txt_filename = filename+FILEEXT
        tpl_filename = filename+'.tpl'

        #1.export table into text file
        self.generate_text_file(src_table, txt_filename, cur)

        #2.export template
        field_list = addresses.split(',')
        field_list.append(suburb)
        field_list.append(state)
        field_list.append(postcode)
        self.generate_tpl(txt_filename, field_list, tpl_filename, src_table)

        #3.run data wizard
        if FILEEXT.endswith('.mdb'):
            temp_array = filename.split('\\')
            temp_array.pop()
            temp_mdb_file = '\\'.join(temp_array) + '\\' + src_table + '_matched.mdb'
        else:
            temp_mdb_file = txt_filename.replace(FILEEXT, '_matched.mdb')

        try:
            os.remove(temp_mdb_file)
        except WindowsError:
            pass

        a_wizard = datawizard.DataWizard()
        a_wizard.run(txt_filename, tpl_filename)

        #4.rename mdb to correct mdb file
        if filename.endswith('.mdb'):
            try:
                os.remove(filename)
            except WindowsError:
                pass
            os.rename(temp_mdb_file, filename)
        else:
            pass
            #we need to import back to table

if __name__ == '__main__':

    startTime = datetime.datetime.now()
    con = db.get_connection()
    app = DPID(474, con)
    app.run()
    con.commit()
    log.info(datetime.datetime.now() - startTime)


