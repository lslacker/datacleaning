
import os
import pyodbc
import db
import cStringIO
import utils
import datetime
import subprocess
import re
import shutil
import codecs

try:
    import logger
    log = logger.getlogger()
except:
    import logging
    log = logging.getlogger()

BASE_DIR = os.path.dirname(__file__)

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
Dt Match Type=Error
Dt Sort Plan No=BSPKey
Dt PPSP=PrintPost
Dt Barcode=Barcode
Dt DPID=DPID
Dt PP Sort Ind=Dt Metro or Country

[Options]
Barcode Size=
Barcode Encoding Method=
Input File Delimiter=Tab
Input File Text Qualifier=
Output File Delimiter=
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
        #texter = export2db.textwriter.TextWriter(filename)
        params = """WITH DELIMITER AS '\t' NULL AS '\N' CSV HEADER"""
        #params = """WITH DELIMITER AS ',' NULL AS '' CSV HEADER QUOTE '"'"""
        select_query = "SELECT * FROM {0}".format(src_table)
        output = cStringIO.StringIO()
        with open(filename, 'w') as f:
            cur.copy_expert("COPY ({0}) TO STDOUT {1}".format(select_query, params), f)
        #cur.copy_to(output, src_table, sep='\t', null='\\N', columns=None)
        #texter.write(output)
        #texter.save()
        # output.seek(0)
        # with open(filename, 'w') as f:
        # #with codecs.open(filename, mode="w", encoding="utf-8") as f:
        #     contents = output.getvalue()
        #     for line in re.split(r"[~\r\n]+", contents):
        #         if line:
        #             temp = line.split("\t")
        #             #temp = map(lambda x: x if x.startswith('"') and x.endswith('"') else '"{}"'.format(x), temp)
        #             temp = map(lambda x: '' if x.startswith('"') and x.endswith('"') and len(x) == 2 else x, temp)
        #             f.write("{}\n".format("\t".join(temp)))
        #
        # output.close()


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
        output = txt_filename.replace('.mdb', '')
        CMDLINE1 = '"C:\Program Files\DataTools\DtFpcDpid.exe" "%s", "%s", "%s"'
        print CMDLINE1 % (txt_filename, txt_filename.replace('.mdb', ''), tpl_filename)
        p = subprocess.Popen(CMDLINE1 % (txt_filename, output, tpl_filename), shell=True,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        for line in p.stdout.readlines():
            print line,
        retval = p.wait()

        # retval always returns 0 regardless
        # read this file txt_filename.replace('.mdb', '') into access db???
        access_filename = txt_filename.replace('.txt', '')
        shutil.copy(os.path.join(BASE_DIR, 'template.mdb'), access_filename)

        #print access_filename
        connection_string = 'Driver={Microsoft Access Driver (*.mdb)};Dbq=%s;Uid=;Pwd=;' % access_filename
        conn = pyodbc.connect(connection_string, autocommit=True)
        cursor = conn.cursor()

        with open(output, 'r') as f:
            # createQuery = 'create table MailMerge1 (\n'
            new_header = f.readline()[:-1].split(',')

            # for aField in new_header:
            #     createQuery = createQuery + ' %s text,\n' % aField
            #
            # createQuery = createQuery[:-2] + ')'
            # #print createQuery
            # cursor.execute(createQuery)
            #
            # insertQuery = "insert into %s values (%s" % ('MailMerge1', "?,"*(len(new_header)))
            # insertQuery = insertQuery[:-1]+')'
            #
            # for line in f.readlines():
            #     row = line[:-1].split('\t')
            #     row = map(lambda x: x[1:-1] if x.startswith('"') and x.endswith('"') else x, row)
            #     #print row
            #     cursor.execute(insertQuery, row)

        cursor.execute('''
        SELECT *
        into MailMerge1
        from [Text;FMT=Delimited;HDR=YES;DATABASE={0}].[{1}]'''.format(os.path.dirname(output), os.path.basename(output)))
        for a_header in new_header:
            cursor.execute("UPDATE MailMerge1 set {0}='' where {0} is null".format(a_header))
        # now make access database the same output as blink
        cursor.execute("""UPDATE MailMerge1 SET PrintPost = '0' where PrintPost = '' or PrintPost is null""")
        #cursor.execute("""ALTER TABLE MailMerge1 alter column PrintPost Long""")
        cursor.execute("""UPDATE MailMerge1 set [BSPKey]='0' WHERE [BSPKey] is null""")
        cursor.execute("""UPDATE MailMerge1 set [BSPKey]='1'+[BSPKey] WHERE Val([BSPKey])=1""")
        cursor.execute("""UPDATE MailMerge1 set [BSPKey]='2'+[BSPKey] WHERE Val([BSPKey]) between 3 and 21""")
        cursor.execute("""UPDATE MailMerge1 set [BSPKey]='3'+[BSPKey] WHERE Val([BSPKey]) between 22 and 34""")
        cursor.execute("""UPDATE MailMerge1 set [BSPKey]='4'+[BSPKey] WHERE (Val([BSPKey]) between 35 and 44) or Val([BSPKey])=2""")
        cursor.execute("""UPDATE MailMerge1 set [BSPKey]='5'+[BSPKey] WHERE (Val([BSPKey]) between 45 and 48)""")
        cursor.execute("""UPDATE MailMerge1 set [BSPKey]='6'+[BSPKey] WHERE (Val([BSPKey]) between 49 and 53)""")
        cursor.execute("""UPDATE MailMerge1 set [BSPKey]='7'+[BSPKey] WHERE (Val([BSPKey])=54)""")
        cursor.execute("""UPDATE MailMerge1 set [BSPKey]='0999' WHERE (Val([BSPKey])=0)""")
        cursor.execute("""UPDATE MailMerge1 set [BSPKey]=LEFT([BSPKey],1) + '999' WHERE Barcode='' or Barcode is null""")

        # now add extra field to match blink (corrected add, correct field)
        t_address = [x for x in field_list if x]
        #print t_address
        idx = 1
        blink_fields = []
        for t in t_address:
            cursor.execute("""ALTER TABLE MailMerge1 add column "Corrected Add{}" text(40)""".format(idx))
            blink_fields.append("[Corrected Add{}]".format(idx))
            idx += 1

        for i in range(3):
            cursor.execute("""ALTER TABLE MailMerge1 add column "Corrected Field{}" text(40)""".format(idx))
            blink_fields.append("[Corrected Field{}]".format(idx))
            idx += 1

        cursor.execute("""ALTER TABLE MailMerge1 add column "Field Corrected" text(40)""")
        blink_fields.append("[Field Corrected]")

        # now re-arrange fields in table
        # remove BSPKey, PrintPost, Barcode in new_header
        new_header = ['[{}]'.format(x[1:-1]) for x in new_header]  # remove double quote
        new_header.remove('[BSPKey]')
        new_header.remove('[PrintPost]')
        new_header.remove('[Barcode]')
        new_header.remove('[DPID]')
        new_header.remove('[Error]')

        dtool_fields = [x for x in new_header if x.startswith('[Dt ')]
        balance_fields = [x for x in new_header if not x.startswith('[Dt ')]

        query = 'SELECT BSPKey, PrintPost, Barcode, {0}, DPID, Error, {1}, {2} INTO MailMerge from MailMerge1'

        cursor.execute(query.format(','.join(balance_fields), ','.join(blink_fields), ','.join(dtool_fields)))

        cursor.execute('drop table MailMerge1')

        conn.commit()
        cursor.close()
        conn.close()

        # now delete temp file
        os.remove(output)
        os.remove(txt_filename)
        os.remove(tpl_filename)


if __name__ == '__main__':
    startTime = datetime.datetime.now()
    con = db.get_connection()
    #347
    app = DPID(359, con)  # 474, 1360, <--------- please change taskid number here 474 Hertz, 1360 Holden, what is your taskid number?
    app.run()
    con.commit()
    log.info(datetime.datetime.now() - startTime)

