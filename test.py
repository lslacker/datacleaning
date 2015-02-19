__author__ = 'lslacker'
 # -*- coding: utf-8 -*-
import csv
import db
import pickle
import re
import sys
import psycopg2

# ALTER TABLE import_tasks
# DROP CONSTRAINT import_tasks_taskid_fkey,
# ADD CONSTRAINT pref_scores_gid_fkey
#    FOREIGN KEY (gid)
#    REFERENCES pref_games(gid)
#    ON DELETE CASCADE;
conn = db.get_connection()

cur = conn.cursor()

# cur.execute("select * from celery_taskmeta")
# rows = cur.fetchall()
# for row in rows:
#     a = pickle.loads(row[3])
#     print a

TEMPLATE = """ALTER TABLE {0}
DROP CONSTRAINT {0}_taskid_fkey,
ADD CONSTRAINT {0}_taskid_fkey
   FOREIGN KEY (taskid)
   REFERENCES tasks(id)
   ON DELETE CASCADE;
"""

TEMPLATE1 = """ALTER TABLE {0}
ADD CONSTRAINT {0}_taskid_fkey
   FOREIGN KEY (taskid)
   REFERENCES tasks(id)
   ON DELETE CASCADE;
"""

cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'  and table_name like '%_tasks' ")
rows = cur.fetchall()
cur.close()
error = False
query = ""
cur = conn.cursor()

for row in rows:
    table_name = row[0]

    try:
        query = TEMPLATE.format(table_name)
        print query
        cur.execute(query)

    except psycopg2.ProgrammingError:
        conn.rollback()
        err_mess = sys.exc_info()[1]
        if re.match(r'constraint .+? does not exist', err_mess.message, re.I):
            query = TEMPLATE1.format(table_name)
            print query
            cur.execute(query)
    except:
        conn.rollback()
        error = True

if not error:
    conn.commit()
cur.close()

conn.close()


