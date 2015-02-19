# -*- coding: utf-8 -*-

import os
import export2db
import db
import cStringIO
import utils
import datetime
import psycopg2
#import psycopg2.extras.DictCursor
import addressparser

try:
    import logger
    log = logger.getlogger()
except:
    import logging
    log = logging.getlogger()

    
class Barcode(object):
    def __init__(self, taskid, conn):
        self.taskid = taskid
        self.blink= addressparser.blinkwrapper.BlinkWrapper()
        self.blink.setInTemplate(['DPI','FCC','CET','CUS'])
        self.blink.setOutTemplate(['BAR'])
        self.conn = conn
        
    def __del__(self):
        self.blink.cleanUp()
        
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

        cur.execute("""SELECT a.key_value from vars_tasks a
        INNER JOIN tasks b on a.jobid = b.jobid
        WHERE b.id=%(taskid)s
        """, myvars)

        environment_vars = cur.fetchall()

        cur.execute("""
            SELECT *
            FROM barcode_tasks
            WHERE taskid = %(taskid)s
        """, myvars)

        result = cur.fetchone()
            
        src_table = result['src_table']
        barcode_type = result['barcode_type']
        custno = result['custno']

        if barcode_type == '59|N':
            max_length = 8
        elif barcode_type == '59|C':
            max_length = 5
        elif barcode_type == '62|N':
            max_length = 15
        else:
            max_length = 10

        cur.execute("""
            select max(length({0})) as data_max_length
            from {1}
        """.format(custno, src_table))

        data_max_length = cur.fetchone()['data_max_length']

        if data_max_length > max_length:
            log.error("CustNo field > %d" % max_length)
            raise RuntimeError("CustNo field > %d" % max_length)

        #create temp parsed table first
        t_dest_table = '_{0}'.format(src_table)
        create_query = "DROP TABLE IF EXISTS {0}; CREATE TABLE {0} (mm_key int,barcode text)".format(t_dest_table)
        log.info(cur.mogrify(create_query))
        cur.execute(create_query)
        out_buffer = cStringIO.StringIO()  #when million of records, what would happen? out of memory
        in_buffer = cStringIO.StringIO()

        select_query = "select mm_key, {0}, dpid from {1}".format(custno, src_table)

        cur.copy_expert("COPY ({0}) TO STDOUT WITH DELIMITER as '\t' ".format(select_query), out_buffer)
        out_buffer.seek(0)

        for result in out_buffer.readlines():
            result = result[:-1]
            mm_key, tobeencoded, dpid = result.split('\t')

            if dpid == '' or dpid == ' ' or dpid == '0':
                dpid = '0'*8

            query = "{0}|{1}|{2}".format(dpid, barcode_type, tobeencoded)
            new_barcode = self.blink.getBarcode(query)
            in_buffer.write("{0}|{1}\n".format(mm_key, new_barcode))

        in_buffer.seek(0)
        cur.copy_from(in_buffer, t_dest_table, sep='|')

        out_buffer.close()
        in_buffer.close()

        #merge src_table with temp_parse table, to create new table
        final_query = """
        UPDATE {0} a
        set barcode=b.barcode
        FROM {1} b
        WHERE b.mm_key = a.mm_key
        ;
        DROP TABLE IF EXISTS {1}
        """.format(src_table, t_dest_table)

        cur.execute(final_query)

if __name__ == '__main__':
    startTime = datetime.datetime.now()
    con = db.get_connection()
    app = Barcode(665, con)
    #0:03:38.474000 with 1,000 for 147,000 recs #using batch update
    #0:00:47.978000 #export to file, bulk import back result--> faster
    app.run()
    con.commit()
    log.info(datetime.datetime.now() - startTime)

