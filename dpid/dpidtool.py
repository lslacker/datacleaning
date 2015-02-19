
import os
import export2db
import db
import cStringIO
import utils
import datetime
import subprocess

try:
    import logger
    log = logger.getlogger()
except:
    import logging
    log = logging.getlogger()


DEFAULT_TEMPLATE = """[Input Fields]
Address Line 1={0}
Address Line 2={1}
Address Line 3={2}
Address Line 4={3}
Locality=%s
State=%s
Postcode=%s
Customer Info=

[Output Fields]
Dt Address Line=
Dt Locality=
Dt State=
Dt Postcode=
Dt Sort Plan No=
Dt Barcode=Barcode

[Options]
Barcode Size=
Barcode Encoding Method=
Input File Delimiter=Tab
Input File Text Qualifier=
Output File Delimiter=Tab
Result Totals File Name="""


class DPID(object):

    def __init__(self, taskid, conn):
        self.taskid = taskid
        self.conn = conn

    def generate_tpl(self, field_list, tpl_filename, src_table=None):

        extra_list = []

        postcode = field_list.pop()
        state = field_list.pop()
        suburb = field_list.pop()

        # ignore address line > 4
        while len(field_list) > 4:
            #postcode
            extra_list.insert(0, field_list.pop())
        while len(field_list) < 4:
            field_list.append('')
        blink_template = DEFAULT_TEMPLATE.format(*field_list)
        blink_template = blink_template % (suburb, state, postcode)

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
        self.generate_tpl(field_list, tpl_filename, src_table)

        #3.run
        CMDLINE1 = '"C:\Program Files\DataTools\DtFpcDpid.exe" "%s", "%s", "%s"'
        print CMDLINE1 % (txt_filename, txt_filename.replace('.mdb', ''), tpl_filename)
        p = subprocess.Popen(CMDLINE1 % (txt_filename, txt_filename.replace('.mdb', ''), tpl_filename), shell=True,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        for line in p.stdout.readlines():
            print line,
        retval = p.wait()
        print retval

if __name__ == '__main__':

    startTime = datetime.datetime.now()
    con = db.get_connection()
    app = DPID(1360, con)
    app.run()
    con.commit()
    log.info(datetime.datetime.now() - startTime)


