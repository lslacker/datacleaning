# -*- coding: utf-8 -*-
import csv
import cStringIO
import codecs

import psycopg2

import utils


try:
    import logger
    log = logger.getlogger()
except:
    import logging
    log = logging.getlogger()


class TextReader():
    """
    Read delimited text file
    """
    def __init__(self, textfile, delimiter='\t', has_header=True, lines_skipped=0):
        """Create file pointer and parse header.

        Keyword arguments:
        textfile -- string -- text file name
        delimiter -- string -- file delimiter
        has_header -- boolean -- if text file has header
        lines_skipped --int -- number of lines skipped from the top

        """

        #self.f = open(textfile, 'r')

        #--- open file with utf8 as default
        self.f = codecs.open(textfile, encoding='utf-8', mode='r', errors='replace')

        self.has_header = has_header
        self.lines_skipped = lines_skipped
        self.delimiter = delimiter
        self.textfile = textfile
        self.mm_sheet_index = 'no index'

        for i in range(lines_skipped):
            self.f.readline()
        """
            get file header
            if no header
                remember file pointer
                get first line data to know max fields
                then, replace with default name
                wind back file pointer
        """
        if self.has_header:
            tmp = csv.reader([self.f.readline()], delimiter=self.delimiter)
            self.header = tmp.next()
        else:
            x = self.f.tell()
            tmp = self.f.readline()
            tmp_array = csv.reader([tmp], delimiter=self.delimiter)
            tmp_array = tmp_array.next()
            tmp_array = ['field%d' % i for i in range(len(tmp_array))]
            self.header = tmp_array
            self.f.seek(x)

        #--- Remeber the pointer to first data, useful for later use
        self.first = self.f.tell()

        self.header = [utils.lm_simplify(i, txt) for i, txt in enumerate(self.header)]

        #--- We should check for double header
        utils.remove_duplicate_fields(self.header)

        log.info(self.header)

    def get_header(self):
        """return list of header field names"""
        return self.header

    def get_file_pointer(self):
        """return file pointer for bulk postgresql database import"""
        return self.f

    def __del__(self):
        """close file pointer, and return void"""
        self.f.close()
        del self.f

    def bulk2db(self, conn, tablename, appendseq=True, append=False):
        """Create table & bulk insert data into database, return boolean

        import 438,221 records in 0:00:10.512680

        """
        isOk = True
        output = cStringIO.StringIO()
        idx = 1
        line = self.f.readline()

        #--- Overule appendSeq, if mm_origseq, mm_fn, or mm_sheet_index already exists
        overrule = 'mm_origseq' in self.header \
            or 'mm_fn' in self.header \
            or 'mm_sheet_index' in self.header

        #--- Overule appendSeq, if mm_origseq, mm_fn, or mm_sheet_index already exists
        mm_key_exists = 'mm_key' in self.header

        while len(line) > 0:
            #--- FORMAT DATA
            #log.info(line)
            line = line.encode('utf-8')    #encode to convert unicode char to byte string character
            tmp_array = csv.reader([line], delimiter=self.delimiter).next()
            log.info(tmp_array)
            tmp_array = [field_data for field_data in tmp_array]

            tmp_array = [utils.remove_escape_char(field_data) for field_data in tmp_array]

            #Append some blank field at the end
            #Excel save as text

            while len(tmp_array) < len(self.header):
                log.info('adding 1 field at the end')
                tmp_array.append('')

            # Sometime, there is extra tab at the end, need to remove
            # to match header
            while len(tmp_array) > len(self.header):
                log.info('remove 1 field at the end')
                tmp_array.pop()

            if appendseq and not overrule:
                tmp_array.insert(0, self.mm_sheet_index)
                tmp_array.insert(0, self.textfile.replace('\\', '\\\\'))
                tmp_array.insert(0, str(idx))

            output.write('\t'.join(tmp_array) + '\n')
            idx += 1
            line = self.f.readline()

        #----------------------------------------------------------
        # Save string to file-like
        # --> bulk import will be faster than insert into statement
        #----------------------------------------------------------
        output.seek(0)
        cur = conn.cursor()
        #----------------------
        # Drop table if exists
        # Re-create new table
        #----------------------
        if appendseq and not overrule:
            #--- Add origseq and filename
            self.header.insert(0, 'mm_sheet_index')
            self.header.insert(0, 'mm_fn')
            self.header.insert(0, 'mm_origseq')
        try:
            if not append:
                cur.execute("drop table if exists {0}".format(tablename))

                create_query = 'CREATE TABLE %s (\n%s text)' \
                                % (tablename, ' text\n,'.join(self.header))
                log.info(create_query)
                cur.execute(create_query)
            # Do bulk insert
            #----------------------------------------------------
            # copy_from only works with POSTGRESQL
            # copy file-like to POSTGRESQL -> I think it's faster
            #----------------------------------------------------
            cur.copy_from(output, tablename, sep='\t', columns=tuple(self.header))

            # if mm_origseq is blank
            cur.execute("""UPDATE {0}
            SET mm_origseq = '0'
            WHERE mm_origseq = '' or mm_origseq = ' '
            """.format(tablename))

            # Change mm_origseq to int
            cur.execute("""ALTER TABLE %s ALTER mm_origseq TYPE int using mm_origseq::int""" % tablename)

            if mm_key_exists:
                cur.execute("""ALTER TABLE %s DROP COLUMN mm_key""" % tablename)

        except psycopg2.DataError as e:
            log.error(e.pgerror)
            isOk = False

        return isOk
