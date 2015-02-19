# -*- coding: utf-8 -*-
import xlsxwriter

try:
    import logger
    log = logger.getlogger()
except:
    import logging
    log = logging.getlogger()

def remove_quote(field):
    while field.startswith('"') and field.endswith('"'):
        field = field[1:-1]
    return field

class ExcelWriter(object):
    """
    Accept file-like object, then write to excel 2007 and above file format
    """
    def __init__(self, dest_file):
        self.wb = xlsxwriter.Workbook(dest_file)

    def write(self, filelike):
        filelike.seek(0)
        ws = self.wb.add_worksheet()
        content = filelike.getvalue()

        rowidx = 0  # first row
        colidx = 0  # first column
        ncol = 0
        ok_to_write = True
        token_list = []
        first_time = True
        for line in content.split('\n'):
            # text from postgresql is unicode, but displayed as string
            # it has to be decoded to unicode to display text properly
            line = line.decode('utf-8')
            rows = line.split('\t')

            # remove surrounding quote within field

            rows = [x for x in rows]

            if token_list:
                token_list[-1] = token_list[-1] + "\n" + rows.pop(0)
                rows = token_list + rows
                token_list = []

            if rowidx > 0:
                if len(rows) == ncol:
                    ok_to_write = True
                else:
                    token_list = rows
                    print rowidx

            if ok_to_write:
                rows = map(remove_quote, rows)
                ws.write_row(rowidx, colidx, rows)
                rowidx += 1
                ok_to_write = False

            if first_time: # after writing header row
                ncol = len(rows)
                ok_to_write = False
                first_time = False

    def save(self):
        self.wb.close()

    def __del__(self):
        del self.wb
