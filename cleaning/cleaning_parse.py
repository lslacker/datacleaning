
import re
import sys
#reload(sys)
#sys.setdefaultencoding('utf-8')
#print sys.getdefaultencoding()
#sys.path.append(r'Z:\melmailing\_lib')
sys.path.append(r'D:\0_works\pyhon_projects\_lib')
from luan import addressparser
from blink import blinkwrapper
import difflib
import sys
import time
#sys.path.append(r'Z:\melmailing\_lib')
sys.path.append(r'D:\0_works\pyhon_projects\_lib')
import dtconfig
import cStringIO
import csv
import psycopg2

DATABASE_CONF = {'DATABASE': 'jobs',
                 'HOSTNAME': '10.0.6.12',
                 'USERNAME': 'joboperators',
                 'PASSWORD': 'abc123'}

CONNECTION_STRING = "dbname=%(DATABASE)s user=%(USERNAME)s \
                     host=%(HOSTNAME)s password=%(PASSWORD)s" % DATABASE_CONF
                     
def get_connection():
    try:
        conn = psycopg2.connect(CONNECTION_STRING)
    except:
        log.error("I am unable to connect to the database")
        exit(1)
    return conn

class Parse(object):
    def __init__(self, inStr=['ADR']
                     , outStr=['FUT', 'FUN', 'BLT', 'BLN', 'BG1', 'BG2', 'ALN',
                              'TN1', 'TS1', 'TN2', 'TS2', 'THN', 'THT', 'TTS',
                              'PDT', 'PDP', 'PDN', 'PDS', 'LOC', 'STT', 'PCD',
                              'LC2', 'CLC', 'CPC', 'CTN', 'CTT', 'CTS', 'CAD',
                              'BAR', 'BSP', 'PSP', 'PSC', 'DPI', 'PRI', 'CHG',
                              'ERR', 'ERP', 'UNK', 'AFF']):
        self.inStr = inStr
        self.outStr = outStr

    def parse(self, src_table, addresses, suburb, state, postcode, country):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("select column_name from information_schema.columns where table_name = %(src_table)s", locals())

        headers = []
        indexes = []
        rows = cursor.fetchall()
        for row in rows:
            headers.append(row[0])

        for idx, header in enumerate(headers):
            for address in addresses.split(','):
                if header == address:
                    indexes.append(idx)
            if header == suburb:
                indexes.append(idx)

            if header == state:
                indexes.append(idx)

            if header == postcode:
                indexes.append(idx)

        parsed_table = src_table + '_parsed'

        blink = blinkwrapper.BlinkWrapper()
        if blink.setInTemplate(self.inStr, '|') > 0: raise Exception("Input Template Invalid")
        if blink.setOutTemplate(self.outStr, '|') > 0: raise Exception("Output Template Invalid")

        #create parsed table first
        extra_columns = map(lambda x: "''::text as "+x.lower(), self.outStr)
        extra_columns = ",".join(extra_columns)
        create_query = """
            drop table if exists %s;

            select *, ''::text as mm_note, %s
            into %s
            from %s limit 1;

            truncate table %s;

            alter table %s
            add CONSTRAINT fn_%s_pk PRIMARY KEY (mm_key);

        """ % (parsed_table, extra_columns, parsed_table, src_table, parsed_table, parsed_table, parsed_table)

        cursor.execute(create_query)

        output = cStringIO.StringIO()

        cursor.copy_to(output, src_table, sep="\t")
        output.seek(0)
        #lines = output.getvalue().splitlines()
        temp_result = ''
        new_output = cStringIO.StringIO()
        #new_output = open('hhh.txt' ,'rw')
        i = 1
        for result in output.readlines():
            result = result[:-1]
            temp = result.split('\t')
            mm_address = ''
            for idx in indexes:
                mm_address = mm_address + temp[idx] + ' '

            parsed_address = blink.searchAMASRaw(mm_address)
            tmp_array = csv.reader([parsed_address], delimiter='|').next()
            while len(tmp_array) < len(self.outStr):
                tmp_array.append('')
            #print '<'+result + '\t' + 'n' + '\t' + '\t'.join(tmp_array) + '\n'+'>'
            new_output.write(result + '\t' + '' + '\t' + '\t'.join(tmp_array) + '\n')
            
            if i == 100:
                i = 0
                new_output.seek(0)
                cursor.copy_from(new_output, parsed_table, sep='\t')
                new_output.close()
                new_output = cStringIO.StringIO()

            i += 1
        
        #new_output = cStringIO.StringIO(temp_result[:-1])
        new_output.seek(0)
        cursor.copy_from(new_output, parsed_table, sep='\t')
        conn.commit()
        output.close()
        new_output.close()
        #then, update parsed fields
if __name__ == '__main__':

    #app = CleanDPID('lu_snowgum_preclean_parsed',"address_line_1","address_line_2","address_line_3","postcode","country")
    #app = CleanDPID('lu_saddle_preclean_parsed',"address,address2","city","state","postcode","country")
    import time
    t0 = time.time()
    app = Parse()
    app.parse('lu_openuni_preclean',"address1,address2,address3","suburb","state","postcode","country")
    print int(time.time() - t0)
