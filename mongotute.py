__author__ = 'luan'

import config
import logger
import re
import psycopg2.extras
from sys import exit
import pymongo
import codecs


log = logger.getlogger()
pcdb = r'C:\Program Files\PrintSoft\Blink\loc_st_pc.txt'
# Connection to Mongo DB

def get_connection(database='mydb'):
    try:
        conn = pymongo.MongoClient()

        return conn
    except pymongo.errors.ConnectionFailure, e:
        log.error("Could not connect to MongoDB: %s" % e)
        exit(1)

def import_country(tb):
    tb.remove()
    #country_file = r'C:\Documents and Settings\luan\My Documents\Downloads\GeoLite2-Country-CSV_20140401\GeoLite2-Country-Locations.csv'
    country_file = r'C:\Documents and Settings\luan\My Documents\Downloads\readme.txt'
    f = codecs.open(country_file, encoding='utf-8', mode='r', errors='replace')
    #f = open(country_file)
    header = f.readline()
    line = f.readline()
    while len(line) > 0:
        tmp = line.split('\t')
        log.info(tmp)
        country_code = tmp[2].upper()
        country_name = tmp[0].upper()
        a = {
            'country_code': country_code,
            'country_name': country_name
        }
        tb.insert(a)
        line = f.readline()
    f.close()
    a = {
            'country_code': 'NZ',
            'country_name': 'NEW ZEALAND'
    }
    tb.insert(a)
    tb.create_index("country_code", 1)
    tb.create_index("country_name", 1)
if __name__ == '__main__':
    conn = get_connection()
    db = conn.mydb
    tb = db.countries
    #import_country(tb)

    #tb.create_index("query", 1)
    #tb.create_index("postcode", 1)
    #tb.create_index("state", 1)
    # resultset = tb.find()
    # for result in resultset:
    #    log.info(result)
    # tb.remove()
    # reader = open(pcdb, 'r')
    # for line in reader.readlines():
    #     suburb, state, postcode, blank = re.split(r'[|]', line[:-1])
    #     a = {}
    #     a['suburb'] = suburb
    #     a['state'] = state
    #     a['postcode'] = postcode
    #     tb.insert(a)
    # reader.close()
    # a = {'suburb': 'WYNDHAM VALE', 'state': 'VIC'}
    # records = tb.find(a)
    #
    # for record in records:
    #
    #     print record['suburb'], record['state'], record['postcode']

