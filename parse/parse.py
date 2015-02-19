import db
import datetime
import cStringIO
import addressparser

try:
    import logger
    log = logger.getlogger()
except:
    import logging
    log = logging.getlogger()


class Parse(object):
    def __init__(self, taskid, conn):
        self.taskid = taskid
        self.inStr = ['ADR']
        self.outStr = ['FUT', 'FUN', 'BLT', 'BLN', 'BG1', 'BG2', 'ALN',
                       'TN1', 'TS1', 'TN2', 'TS2', 'THN', 'THT', 'TTS',
                       'PDT', 'PDP', 'PDN', 'PDS', 'LOC', 'STT', 'PCD',
                       'LC2', 'CLC', 'CPC', 'CTN', 'CTT', 'CTS', 'CAD',
                       'BAR', 'BSP', 'PSP', 'PSC', 'AFF', 'PRI', 'CHG',
                       'ERR', 'ERP', 'UNK', 'DPI']
        self.conn = conn
    
    def run(self, table_task='parse_tasks'):
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
            FROM {0}
            WHERE taskid = %(taskid)s
        """.format(table_task), myvars)

        result = cur.fetchone()
            
        src_table = result.src_table
        dest_table = result.dest_table
        addresses = result.addresses
        suburb = result.suburb
        state = result.state
        postcode = result.postcode
        country = result.country

        blink = addressparser.blinkwrapper.BlinkWrapper()

        if blink.setInTemplate(self.inStr, '|') > 0:
            raise RuntimeError("Input Template Invalid")
        if blink.setOutTemplate(self.outStr, '|') > 0:
            raise RuntimeError("Output Template Invalid")

        #create temp parsed table first
        t_dest_table = '_{0}'.format(dest_table)
        create_query = "DROP TABLE IF EXISTS {0}; CREATE TABLE {0} (mm_key int,"

        for a in self.outStr:
            create_query += "{0} text default '',".format(a.lower())
        create_query = create_query[:-1].format(t_dest_table) + ')'
        log.info(create_query)
        cur.execute(create_query)

        #add unique constraint
        cur.execute('''
        DROP INDEX IF EXISTS {0}_mm_key_idx; CREATE INDEX {0}_mm_key_idx ON {0} (mm_key);
        '''.format(t_dest_table))

        cur.execute('''
        DROP INDEX IF EXISTS {0}_mm_key_idx; CREATE INDEX {0}_mm_key_idx ON {0} (mm_key);
        '''.format(src_table))
        out_buffer = cStringIO.StringIO()
        in_buffer = cStringIO.StringIO()
        select_query = "select mm_key, {0},{1},{2},{3} from {4}".format(addresses, suburb, state,
                                                                        postcode, src_table)
        log.info(select_query)
        cur.copy_expert("COPY ({0}) TO STDOUT WITH DELIMITER as '\t' ".format(select_query), out_buffer)
        out_buffer.seek(0)

        for result in out_buffer.readlines():
            #log.info(result)

            result = result[:-1]
            fields = result.split('\t')
            mm_key = fields.pop(0)
            _t = blink.searchAMASRaw(' '.join(fields))
            line = "{0}|{1}\n".format(mm_key, _t)
            log.info(line)
            in_buffer.write(line)

        in_buffer.seek(0)


        cur.copy_from(in_buffer, t_dest_table, sep='|')

        #new_output.seek(0)
        out_buffer.close()
        in_buffer.close()

        #merge src_table with temp_parse table, to create new table
        final_query = """
        DROP TABLE IF EXISTS {0}
        ;
        SELECT a.*, {1}
        INTO {0}
        FROM {2} a
        INNER JOIN {3} b on a.mm_key = b.mm_key
        ;
        DROP TABLE {3}
        """.format(dest_table, ','.join(self.outStr), src_table, t_dest_table)
        log.info(final_query)
        cur.execute(final_query)


if __name__ == '__main__':
    startTime = datetime.datetime.now()
    con = db.get_connection()
    app = Parse(1022, con)
    app.run()
    con.commit()
    log.info(datetime.datetime.now() - startTime)