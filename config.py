# -*- coding: utf-8 -*-
import os

basedir = os.path.abspath(os.path.dirname(__file__))


DATABASE_CONF = {'DATABASE': 'jobs',
                 'HOSTNAME': '10.0.6.12',
                 'USERNAME': 'joboperators',
                 'PASSWORD': 'abc123'}

CONNECTION_STRING = "dbname=%(DATABASE)s user=%(USERNAME)s \
                     host=%(HOSTNAME)s password=%(PASSWORD)s" % DATABASE_CONF


keyworks = []

with open(basedir + '/import2db/postgresql_keyworks.txt') as f:
    keyworks = f.readlines()
