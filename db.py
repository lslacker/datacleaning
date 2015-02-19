# -*- coding: utf-8 -*-
import config
import logger
import psycopg2
import psycopg2.extras
from sys import exit

log = logger.getlogger()


def get_connection():
    try:
        conn = psycopg2.connect(config.CONNECTION_STRING, connection_factory=psycopg2.extras.NamedTupleConnection)
    except:
        log.error("I am unable to connect to the database")
        exit(1)
    return conn