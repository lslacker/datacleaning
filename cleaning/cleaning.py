import datetime
import psycopg2
import psycopg2.extras
import db
import cStringIO
import utils
import re
import os
import json
import rabbit
import time
import dpid
import decor
import multiprocessing
from threading import Thread, RLock, Lock, Condition
import Queue

try:
    import logger
    log = logger.getlogger()
except:
    import logging
    log = logging.getlogger()


def show_table(table_name, cur):
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name=%s", (table_name,))
    rows = cur.fetchall()
    return [row[0] for row in rows]




class Cleaning(object):

    def __init__(self, taskid, conn):
        self.taskid = taskid
        self.conn = conn
        #self.inqueue = Queue.Queue()

    @decor.dpid_address_last
    @decor.dedupe_ssp_in_address
    @decor.fill_ssp_maps
    @decor.check_oseas
    @decor.fill_ssp_fuzzy1
    @decor.fill_ssp_fuzzy
    @decor.fill_state_fuzzy
    @decor.validate_suburb_state_postcode_fuzzy
    @decor.fill_suburb
    @decor.fill_postcode
    @decor.fill_state
    @decor.pre_check_ssp_in_address
    @decor.split_ssp
    @decor.check_street_in_ssp
    @decor.pre_check_ssp
    @decor.pre_check_ssp_within_address
    @decor.dpid_address
    def validate_record(self, addresses, suburb, state, postcode, country, mm_preclean, mm_note, mm_clean_type):
        # format some data before hand
        suburb = suburb.strip().upper()
        state = state.strip().upper()
        postcode = postcode.strip().upper()
        country = country.strip().upper()
        country = country.replace('AUSTRALIA', '')


        #should format country from here, if country is nnot blank, ignore
        return addresses, suburb, state, postcode, country, mm_preclean, mm_note, mm_clean_type

    def clean(self, line):

        fields = line[:-1].split('\t')
        mm_table_type = fields.pop()
        mm_clean_type = fields.pop()
        mm_note = fields.pop()
        mm_preclean = fields.pop()
        country = fields.pop()
        postcode = fields.pop()
        state = fields.pop()
        suburb = fields.pop()
        mm_key = fields.pop(0)
        addresses = fields
        mm_table_type = 'NEW'
        log.info("Cleaning == mm_key={0}".format(mm_key))
        try:
            addresses, suburb, state, postcode, country, mm_preclean, mm_note, mm_clean_type, parsed_result = \
                                                            self.validate_record(addresses, suburb, state, postcode, country,
                                                                            mm_preclean, mm_note, mm_clean_type)
        except:
            pass
            
        return '{0}\t{1}\t{2}\t{3}\t{4}\t{5}\t{6}\t{7}\t{8}\t{9}\n'.format(mm_key, '\t'.join(addresses), suburb,\
                                                                            state, postcode, country, mm_preclean,\
                                                                            mm_note, mm_clean_type, mm_table_type)

    def run(self):
        """
        Run task, dont need to return job_status as previous, let program throw Exception,
        and catch Exception at outer level
        """

        decor.r_lookup = dpid.paflinkr.PaflinkR()
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
            FROM cleaning_tasks
            WHERE taskid = %(taskid)s
        """, myvars)

        result = cur.fetchone()

        #####
        src_table = result['src_table']
        dest_table = result['dest_table']
        addresses = result['addresses']
        suburb = result['suburb']
        state = result['state']
        postcode = result['postcode']
        country = result['country']

        fieldnames = '{0}, {1}, {2}, {3}, {4}'.format(addresses, suburb, state, postcode, country)

        temp_table = '{0}_t'.format(src_table)

        cur.execute("DROP TABLE IF EXISTS {1}; SELECT mm_key, {0} INTO {1} FROM {2}".format(fieldnames, temp_table, src_table))
        cur.execute("""
        ALTER TABLE {0}
        ADD mm_preclean text default '',
        ADD mm_note text default '',
        ADD mm_clean_type text default '',
        ADD mm_table_type text default 'OLD'
        """.format(temp_table))
        #2901
        select_query = "select * from {0} ".format(temp_table)

        out_buffer = cStringIO.StringIO()  #when million of records, what would happen? out of memory

        cur.copy_expert("COPY ({0}) TO STDOUT WITH DELIMITER as '\t' ".format(select_query), out_buffer)
        out_buffer.seek(0)

        '''
        SINGLE
        '''
        try:
            in_buffer = cStringIO.StringIO()
            for line in out_buffer.readlines():
                in_buffer.write(self.clean(line))
            in_buffer.seek(0)
            cur.copy_from(in_buffer, temp_table, sep='\t')
            out_buffer.close()
            in_buffer.close()
            #0:07:21.856000

            '''
            THREAD
            '''

            # # Set up some threads to fetch the enclosures
            # for i in range(50):
            #     worker = Thread(target=self.clean_thread, args=(i,))
            #     worker.setDaemon(True)
            #     worker.start()
            #
            #
            # # Download the feed(s) and put the enclosure URLs into
            # # the queue.
            # for line in out_buffer.readlines():
            #     #log.info('Queuing:' + line)
            #     self.inqueue.put(line)
            # out_buffer.close()
            #
            # # Now wait for the queue to be empty, indicating that we have
            # # processed all of the downloads.
            # log.info('*** Main thread waiting')
            # self.inqueue.join()
            #
            # log.info('*** Done')
            # self.in_buffer.seek(0)
            # cur.copy_from(self.in_buffer, temp_table, sep='\t')
            # out_buffer.close()
            # self.in_buffer.close()
            #
            # #0:07:23.838000 with 5 thread
            # #0:08:20.300000 with 2 thread
            # # out_buffer.close()
            # #THREAD IS MUCH SLOWER THAN SINGLE... DON'T KNOW WHY?



            src_table_fields = show_table(src_table, cur)
            t_table_fields = show_table(temp_table, cur)

            src_table_fields = map(lambda x: 'b.{0}'.format(x) if x in t_table_fields else 'a.{0}'.format(x)
                                   , src_table_fields)
            t_table_fields = [x for x in t_table_fields if 'b.{0}'.format(x) not in src_table_fields]
            t_table_fields.pop()  # remove mm_table_type

            #merge src_table with temp_parse table, to create new table
            final_query = """
            DROP TABLE IF EXISTS {0}
            ;
            SELECT {1}, {2}
            INTO {0}
            FROM {3} a
            INNER JOIN {4} b on a.mm_key = b.mm_key and b.mm_table_type='NEW'

            """.format(dest_table, ','.join(src_table_fields), ','.join(t_table_fields), src_table, temp_table)
            #log.info(final_query)
            print final_query
            cur.execute(final_query)
        except:
            raise
        finally:
            decor.r_lookup.close()

if __name__ == '__main__':
    startTime = datetime.datetime.now()
    conn = db.get_connection()
    app = Cleaning(1349, conn)  #38 or #7
    app.run()
    conn.commit()
    log.info(datetime.datetime.now() - startTime)