#!/usr/bin/python
from pywinauto import application
from pywinauto import WindowNotFoundError
import time
import re
import os

try:
    import logger
    log = logger.getlogger()
except:
    import logging
    log = logging.getlogger()


class PaflinkR(object):
    def __init__(self):
        self.app = application.Application()
        os.chdir(r'D:\apps\Blink')
        self.app.start_(r'D:\apps\Blink\paflinkr.exe')
        #self.app.connect_(title_re = "PAFlink Rapid 8.0", class_name = "#32770", visible_only = False)
        
    def run(self, suburb_or_postcode, street_name, street_number):

        results = None
        if re.match(r'^\d+$', suburb_or_postcode):
            #postcode
            if len(suburb_or_postcode) == 4:
                self.app['Dialog'].TypeKeys('%L')
                self.app['Dialog'].TypeKeys(suburb_or_postcode)
                self.app['Dialog'].TypeKeys(street_name)
                self.app['Dialog'].TypeKeys('{SPACE}')
                self.app['Dialog'].TypeKeys(street_number)
                try:
                    results = self.app.Dialog.ListBox.ItemTexts()
                except:
                    print 'im here'
                    self.app['Dialog'].TypeKeys('{ENTER}')
        else:
            #suburb
            self.app['Dialog'].TypeKeys('%L')
            array_of_words = re.split(r'\s+',suburb_or_postcode)
            
            for each_word in array_of_words:
                self.app['Dialog'].TypeKeys(each_word)
                self.app['Dialog'].TypeKeys('{SPACE}')
                
            self.app['Dialog'].TypeKeys('{TAB}')
            self.app['Dialog'].TypeKeys(street_name)
            self.app['Dialog'].TypeKeys('{SPACE}')
            self.app['Dialog'].TypeKeys(street_number)
            results = self.app.Dialog.ListBox.ItemTexts()
            
        return results
        
    def select(self, suburb_or_postcode, box_type, number, idx=0):
        results = None
        
        if re.match(r'^\d{4}$',suburb_or_postcode):
            #postcode
            print 'POSTCODE'
            
            self.app['Dialog'].TypeKeys('%L')
            self.app['Dialog'].TypeKeys(suburb_or_postcode)
            self.app['Dialog'].TypeKeys(box_type)
            
            self.app.Dialog.ListBox.Select(idx)
            self.app['Dialog'].TypeKeys(number)
            
            results = self.app.Dialog.ListBox.ItemTexts()
        else:
            #suburb
            print 'SUBURB'
            self.app['Dialog'].TypeKeys('%L')
            array_of_words = re.split(r'\s+', suburb_or_postcode)
            
            for each_word in array_of_words:
                self.app['Dialog'].TypeKeys(each_word)
                self.app['Dialog'].TypeKeys('{SPACE}')
                
            self.app['Dialog'].TypeKeys('{TAB}')
            self.app['Dialog'].TypeKeys(box_type)
            
            self.app.Dialog.ListBox.Select(idx)
            self.app['Dialog'].TypeKeys(number)
            
            results = self.app['Dialog'].ListBox.ItemTexts()
            
        return results

    def run_fuzzy(self, suburb_or_postcode, street_name):

        results = None
        if re.match(r'^\d+$', suburb_or_postcode):
            #postcode
            log.info("NOT YET IMPLEMENTED")
        else:
            #suburb
            self.app['Dialog'].TypeKeys('%L')
            array_of_words = re.split(r'\s+', suburb_or_postcode)

            for each_word in array_of_words:
                self.app['Dialog'].TypeKeys(each_word)
                self.app['Dialog'].TypeKeys('{SPACE}')

            self.app['Dialog'].TypeKeys('{TAB}')
            self.app['Dialog'].TypeKeys(street_name)
            try:
                results = self.app.Dialog.ListBox.ItemTexts()
            except:
                self.app['Dialog'].TypeKeys('{ENTER}')

        return results

    def similar_run(self, street_name):
        results = None
        try:
            self.app['Dialog'].TypeKeys('%L')
            self.app['Dialog'].TypeKeys('{TAB}')
            self.app['Dialog'].TypeKeys('#'+street_name.replace(' ', '').upper())
            self.app['Dialog'].TypeKeys('{SPACE}')
            results = self.app.Dialog.ListBox.ItemTexts()
        except:
            pass
        return results
    
    def select_similar_run(self, street_name, street_number, idx=0):
        results = None
        self.app['Dialog'].TypeKeys('%L')
        self.app['Dialog'].TypeKeys('{TAB}')
        self.app['Dialog'].TypeKeys('#'+street_name.replace(' ','').upper())
        self.app['Dialog'].TypeKeys('{SPACE}')
        
        self.app.Dialog.ListBox.Select(idx)
        self.app['Dialog'].TypeKeys(street_number)
        
        results = self.app.Dialog.ListBox.ItemTexts()
            
        return results
        
    def close(self):
        try:
            self.app['Dialog'].TypeKeys('%E')
        except WindowNotFoundError:
            pass
        
    def __del__(self):
        print '*im cleaning up*'
        self.app = None
        del self.app
        
if __name__ == '__main__':
    import time
    time.sleep(5)
    
    app = PaflinkR()
    
    #print app.select_similar_run('Honour','51',4)
    #print app.run('3012','ru')


    #print app.run('3012','as')
    #address= PO BOX 380
    #suburb= Sebastopol
    #new_state= 
    #new_postcode= 3350
    #mm_key= 499
    #log.info(app.select('3356','po box','380',0))
    log.info(app.run('4370', 'freestone', '183'))
    app.close()
    