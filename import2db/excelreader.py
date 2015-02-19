# -*- coding: utf-8 -*-
import cStringIO
import psycopg2
import xlrd
import utils
import datetime


try:
    import logger
    log = logger.getlogger()
except:
    import logging
    log = logging.getlogger()

def to_string(cell):
    field_data

class ExcelReader():
    """
    Read excel file, import to database
    """
    def __init__(self, excelfile, sheet_index=0,
                    has_header=True, lines_skipped=0):
        """Create file pointer and parse header.

        Keyword arguments:
        textfile -- string -- text file name
        delimiter -- string -- file delimiter
        has_header -- boolean -- if text file has header
        lines_skipped --int -- number of lines skipped from the top

        """
        self.has_header = has_header
        self.excelfile = excelfile
        self.book = xlrd.open_workbook(excelfile)
        self.sheet = self.book.sheet_by_index(sheet_index)
        self.mm_sheet_index = sheet_index
        self.rpointer = 0
        self.no_rows = self.sheet.nrows
        for i in range(lines_skipped):
            self.rpointer += 1

        if self.has_header:
            first_column = self.sheet.row_values(self.rpointer)
            self.header = first_column
            self.rpointer += 1
        else:
            self.header = ['field%d' % i for i in range(self.sheet.ncols)]

        self.header = [utils.lm_simplify(i, txt.encode('utf-8', errors='replace'))
                            for i, txt in enumerate(self.header)]

        # We should check for duplicate field name :-)
        utils.remove_duplicate_fields(self.header)


        #remove hard return in header
        self.header = [x.replace("\n", "_") for x in self.header]

    def get_header(self):
        """return list of header field names"""

        return self.header

    def bulk2db(self, conn, tablename='', appendseq=True, append=False):
        """Create table & bulk insert data into database, return boolean

        import 438,221 records in 0:00:10.512680

        """
        #temp = ''
        isOk = True

        #--- Overule appendSeq, if mm_origseq, mm_fn, or mm_sheet_index already exists
        overrule = 'mm_origseq' in self.header \
            or 'mm_fn' in self.header \
            or 'mm_sheet_index' in self.header

        #--- Overule appendSeq, if mm_origseq, mm_fn, or mm_sheet_index already exists
        mm_key_exists = 'mm_key' in self.header

        output = cStringIO.StringIO()
        while self.rpointer < self.no_rows:
            #FORMAT DATA
            # try:
            #     tmp_array = self.sheet.row_values(self.rpointer)
            #
            #     tmp_array = [utils.remove_escape_char(field_data)
            #                 for field_data in tmp_array]
            #     if appendseq and not overrule:
            #         tmp_array.insert(0, str(self.mm_sheet_index))
            #         tmp_array.insert(0, self.excelfile.replace('\\', '\\\\'))
            #         tmp_array.insert(0, str(self.rpointer))
            #     #temp += '\t'.join(tmp_array)
            #     #temp += '\n'
            #     output.write('\t'.join(tmp_array)+'\n')
            #     self.rpointer += 1
            # except IndexError:
            #     break
            try:
                tmp_array = []

                for cpointer in range(len(self.header)):
                    try:
                        cell_type = self.sheet.cell_type(self.rpointer, cpointer)
                        cell_value = self.sheet.cell_value(self.rpointer, cpointer)

                        if cell_type == xlrd.XL_CELL_DATE:
                            # Returns a tuple.
                            dt_tuple = xlrd.xldate_as_tuple(cell_value, self.book.datemode)
                            # Create datetime object from this tuple.
                            d = datetime.datetime(
                                dt_tuple[0], dt_tuple[1], dt_tuple[2],
                                dt_tuple[3], dt_tuple[4], dt_tuple[5]
                            )
                            get_col = d.strftime('%Y-%m-%d %H:%M:%S')
                        elif cell_type == xlrd.XL_CELL_NUMBER:
                            get_col = repr(cell_value)
                            if get_col.endswith('.0'):
                                get_col = get_col[:-2]

                        else:
                            get_col = cell_value.encode('utf-8')
                    except:
                        #if cell is error, which is #N/A, just replace with blank
                        get_col = ''
                        #get_col = cell_value.encode('utf-8')
                    tmp_array.append(get_col)

                #tmp_array = self.sheet.row_values(self.rpointer)

                tmp_array = [utils.remove_escape_char(field_data)
                            for field_data in tmp_array]
                if appendseq and not overrule:
                    tmp_array.insert(0, str(self.mm_sheet_index))
                    tmp_array.insert(0, self.excelfile.replace('\\', '\\\\'))
                    tmp_array.insert(0, str(self.rpointer))
                #temp += '\t'.join(tmp_array)
                #temp += '\n'
                output.write('\t'.join(tmp_array)+'\n')
                self.rpointer += 1

            except IndexError:
                break
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
                cur.execute('drop table if exists %s' % tablename)
                create_query = 'CREATE TABLE %s (\n%s text)'\
                                % (tablename, ' text\n,'.join(self.header))
                log.info(create_query)
                cur.execute(create_query)
            #--------------------------------------------------
            # Do bulk insert
            # copy_from only works with POSTGRESQL
            # copy file-like to POSTGRESQL -> I think it's faster
            #--------------------------------------------------
            cur.copy_from(output, tablename, sep='\t',
                                columns=tuple(self.header))
            # check if mm_origseq is empty, then add extra, especially for n-up data
            # generate a random number from 1 to 50
            # cur.execute("""
            # update {0}
            # set mm_origseq = ((select max(mm_origseq::int) from {0} where mm_origseq<>'') + floor(random()*(50-1)+1))::text
            # where mm_origseq=''
            # """.format(tablename))

            # if mm_origseq is blank
            cur.execute("""UPDATE {0}
            SET mm_origseq = '0'
            WHERE mm_origseq = '' or mm_origseq = ' '
            """.format(tablename))

            cur.execute("""ALTER TABLE %s ALTER mm_origseq TYPE int using mm_origseq::int""" % tablename)

            if mm_key_exists:
                cur.execute("""ALTER TABLE %s DROP COLUMN mm_key""" % tablename)

        except psycopg2.DataError as e:
            log.error(e.pgerror)
            isOk = False
        output.close()
        return isOk
