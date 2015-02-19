# -*- coding: utf-8 -*-

import codecs

try:
    import logger
    log = logger.getlogger()
except:
    import logging
    log = logging.getlogger()

class TextWriter(object):
    """
    Accept file-like object, then write to tab delimited text file
    """

    def __init__(self, dest_file):
        self.writer = codecs.open(dest_file, 'w', 'utf-8')

    def write(self, filelike):
        filelike.seek(0)
        self.writer.write(filelike.getvalue().decode('utf-8'))    # back to unicode from byte string
    
    def save(self):
        self.writer.close()
        
    def __del__(self):
        del self.writer