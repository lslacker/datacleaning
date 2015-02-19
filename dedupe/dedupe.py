#!/usr/bin/env python
import datetime
import psycopg2
import psycopg2.extras
import db
import re

try:
    import logger
    log = logger.getlogger()
except:
    import logging
    log = logging.getlogger()


EXTRA_FIELDS = ['mm_grpkey', 'mm_method', 'mm_groupid', 'mm_retain']

class DeDupe(object):

    def __init__(self, method, src_table, dupe_table, unique_table, args, conn):
        self.src_table = src_table
        self.dupe_table = dupe_table
        self.unique_table = unique_table
        self.method = method
        self.fields = args

        # now checking what field does have null_not_null
        self.null_not_null = [x for x in self.fields if 'null_not_null' in x]
        self.null_not_null = [x.replace(',null_not_null', '') for x in self.null_not_null]
        log.info(self.null_not_null)
        # remove null_not_null
        self.fields_without_null_not_null = [x for x in self.fields if 'null_not_null' not in x]
        self.fields = [x.replace(',null_not_null', '') for x in self.fields]

        self.cur = conn.cursor()

        self.regenerate_unique_table()

        # get column names of src table
        self.cur.execute("""select column_name, data_type from information_schema.columns
            where table_name=%s
            order by ordinal_position
        """, (self.src_table,))
        results = self.cur.fetchall()
        self.base_header = []
        for result in results:
            self.base_header.append(result.column_name)

        self.priority = 'pr' in self.base_header

    def regenerate_unique_table(self):
        #previous source table
        #previous dupe table
        if re.search(r'^(.+[_])(o)(\d+)$', self.src_table, re.I):
            #aa_readings_o1
            method = re.search(r'^(.+[_])(o)(\d+)$', self.src_table, re.I).group(3)
            previous_method = '%d' % (int(method) - 1)
            prefix_2 = re.search(r'^(.+[_])(o)(\d+)$', self.src_table, re.I).group(2)
            prefix_1 = re.search(r'^(.+[_])(o)(\d+)$', self.src_table, re.I).group(1)

            if int(method) > 1:
                #start regenerate unique table for this
                previous_unique_table = prefix_1 + 'o' + previous_method
                dupes_table = prefix_1 + 'd' + str(method)

                self.cur.execute("""
                DROP TABLE IF EXISTS {0};
                select *
                into {0}
                from {1}
                where mm_key not in (select mm_key from {2} where mm_retain > 1)
                """.format(self.src_table, previous_unique_table, dupes_table))
            else:
                pass

    def update_grpkey(self):
        log.info('Updating Group Key')
        
        if 'mm_grpkey' not in self.base_header:
            self.cur.execute('alter table {0} add mm_grpkey text'.format(self.src_table))
         
        grpkey_query = '''update {0}
        set mm_grpkey = upper({1})
        '''.format(self.src_table, ('||'.join(self.fields)))
        log.info(grpkey_query)
        self.cur.execute(grpkey_query)
    def dedupe(self):
        log.info('Doing dedupe')

        # remote tables if existed
        self.cur.execute("""
        DROP TABLE IF EXISTS {0};
        DROP TABLE IF EXISTS {1};

        alter table {2}
        drop column IF EXISTS mm_method;
        

        alter table {2}
        drop column IF EXISTS mm_retain;
        """.format(self.dupe_table, self.unique_table, self.src_table))


        tempQuery = '''select *
            ,'%s'::text as mm_method
            ,rank() OVER (PARTITION BY mm_grpkey order by pr, dpi desc, mm_key) AS mm_retain
            into %s
            from %s
            where mm_grpkey <>''
            ''' % (self.method, self.unique_table, self.src_table)

        if not self.priority:
            tempQuery = '''select *
            ,'%s'::text as mm_method
            ,rank() OVER (PARTITION BY mm_grpkey order by dpi desc, mm_key) AS mm_retain
            into %s
            from %s
            where mm_grpkey <> ''
            ''' % (self.method, self.unique_table, self.src_table)
        log.info(tempQuery)
        self.cur.execute(tempQuery)

        uniqueQuery = '''select * 
                into %s
                from %s
                where mm_grpkey in (
                select mm_grpkey
                from %s
                where mm_retain > 1
                )
                      ''' % (self.dupe_table, self.unique_table, self.unique_table)
        log.info(uniqueQuery)
        self.cur.execute(uniqueQuery)
        
        self.cur.execute('DROP TABLE IF EXISTS %s' % self.unique_table)
        
        deleteQuery = '''select *
                         into %s
                         from %s
                         where mm_key not in (select mm_key from %s where mm_retain > 1)
                        
                      ''' % (self.unique_table, self.src_table, self.dupe_table)
        log.info(deleteQuery)
        self.cur.execute(deleteQuery)
