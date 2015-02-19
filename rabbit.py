__author__ = 'luan'
import pika
import json
import sys
import traceback
import db
import logger
from celery.task.control import revoke

log = logger.getlogger()


def get_header(module, argument):
    response = {'ok': 'False'}
    try:
        filename, delimiter = argument

        m = __import__(module)

        if filename.lower().endswith('.xls') or filename.lower().endswith('.xlsx'):
            func = getattr(m, 'excelreader')
            ReaderClass = getattr(func, 'ExcelReader')
            texter = ReaderClass(filename, sheet_index=int(delimiter), has_header=True)
        else:
            if '\\t' in delimiter:
                delimiter = delimiter.decode('string_escape')
            func = getattr(m, 'textreader')
            ReaderClass = getattr(func, 'TextReader')

            texter = ReaderClass(filename, delimiter=delimiter.encode('utf-8'), has_header=True)

        message = ','.join(texter.get_header())
        response['ok'] = True

    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        message = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))

    response['message'] = message

    return json.dumps(response)


def show_tables(schema_name='public'):
    response = {'ok': 'False'}
    try:
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema=%s", (schema_name,))
        rows = cur.fetchall()
        x = [row[0] for row in rows]

        message = ','.join(x)
        response['ok'] = True
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        message = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))

    response['message'] = message

    return json.dumps(response)


def show_table(table_name):
    response = {'ok': 'False'}
    try:
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name=%s", (table_name,))
        rows = cur.fetchall()
        x = [row[0] for row in rows]

        message = ','.join(x)

        response['ok'] = True

    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        message = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))

    response['message'] = message
    log.info(json.dumps(response))
    return json.dumps(response)


def cancel_job(celery_id):
    response = {'ok': 'False'}

    message = 'good'

    try:
        revoke(celery_id, terminate=True)
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        message = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))

    try:
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("update jobs_lock set status='error' where celery_id=%s", (celery_id,))
        response['ok'] = True
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        message = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    finally:
        conn.commit()

    response['message'] = message
    log.info(json.dumps(response))

    return json.dumps(response)

def on_request(ch, method, props, body):

    n = json.loads(body)
    module = n['module']
    arguments = n['args']
    log.info(module)
    log.info(arguments)
    response = {}
    try:
        if module == 'import2db':
            log.info(" [.] get_header({0})".format(','.join(arguments)))
            response = get_header(module, arguments)
        else:
            log.info(" [.] {1}({0})".format(','.join(arguments), module))
            func = globals()[module]
            response = func(*arguments)
    except:
        response['ok'] = False
        exc_type, exc_value, exc_traceback = sys.exc_info()
        message = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))

    ch.basic_publish(exchange='',
                     routing_key=props.reply_to,
                     properties=pika.BasicProperties(correlation_id=props.correlation_id),
                     body=str(response))
    ch.basic_ack(delivery_tag=method.delivery_tag)


def server():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='rpc_queue')
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(on_request, queue='rpc_queue')
    log.info("[x] Awaiting RPC requests")
    channel.start_consuming()

if __name__ == '__main__':
    server()
    #show_table('lu_liberal_bad_clean')
