#!/usr/bin/python
import pywinauto
from pywinauto.findbestmatch import MatchError
import time

try:
    import logger
    log = logger.getlogger()
except:
    import logging
    log = logging.getlogger()

SECOND = 1
MINUTE = 30*SECOND
DATAWIZARD=r'C:\Program Files\PrintSoft\Blink\DataWizard.exe'


class DataWizard(object):

    def __init__(self):
        self.app = pywinauto.application.Application()

    def run(self, _datafile, _template):
        # Check DataWizard Dialog is open
        # if there is 1 open, wait
        # else, kill all, then start
        handleids = []


        howlong = 0

        while True:
            try:
                self.app.connect_(path=DATAWIZARD)
                howlong += 10*SECOND
                log.info("Waiting for another process to finish... idle for 10 seconds")
                if howlong > 30*SECOND:
                    log.error("Been waiting for 30 minutes, something wrong with DPID")
                    raise RuntimeError("Been waiting for 30 minutes, something wrong with DPID")
                time.sleep(10*SECOND)
            except pywinauto.application.ProcessNotFoundError:
                break

        self.app.start_(DATAWIZARD)
        
        #load template
        self.app.datawizard.TypeKeys('%L')

        #enter filename
        self.app.open.TypeKeys(_template, with_spaces=True)
        self.app.open.TypeKeys('%O')


        #run dpid
        self.app.addressmappingscreen.TypeKeys('%N')

        while True:
            try:
                #Keep pressing ^-X
                self.app.recordconversionscreen.TypeKeys('%x')
                if self.app.recordconversionscreen.Exists():
                    log.info("still running DPID, please be patient")
                    time.sleep(10*SECOND)  #sleep 10 seconds
            except pywinauto.findwindows.WindowNotFoundError:
                break

    def __del__(self):
        self.app = None
        del self.app
        
if __name__ == '__main__':
    a_wizard = DataWizard()
    a_wizard.run(r'N:\jno38622\workingData\240214\38622_matched.mdb.txt', r'N:\jno38622\workingData\240214\38622_matched.mdb.tpl')
