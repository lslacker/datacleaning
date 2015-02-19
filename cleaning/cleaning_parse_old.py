#!/usr/bin/env python

import re
import sys
#reload(sys)
#sys.setdefaultencoding('utf-8')
#print sys.getdefaultencoding()
#sys.path.append(r'Z:\melmailing\_lib')
sys.path.append(r'D:\0_works\pyhon_projects\_lib')
from luan import addressparser
from blink import blinkwrapper
import difflib
import sys
import time
#sys.path.append(r'Z:\melmailing\_lib')
sys.path.append(r'D:\0_works\pyhon_projects\_lib')
import dtconfig

class Parse(object):
    def __init__(self, inStr=['AD1','AD2','AD3','AD4','AD5','AD6','AD7']
                     , outStr=['FUT','FUN','BLT','BLN','BG1','BG2','ALN',
                              'TN1','TS1','TN2','TS2','THN','THT','TTS',
                              'PDT','PDP','PDN','PDS','LOC','STT','PCD',
                              'LC2','CLC','CPC','CTN','CTT','CTS','CAD',
                              'BAR','BSP','PSP','PSC','DPI','PRI','CHG',
                              'ERR','ERP','UNK','AFF']):
        self.inStr = inStr
        self.outStr = outStr
        
    def parse(self, src_table, addresses, suburb, state, postcode, country):
        
        parsed_table = src_table + '_parsed'
        
        blink = blinkwrapper.BlinkWrapper()
        if blink.setInTemplate(self.inStr, '|') > 0: raise Exception("Input Template Invalid")
        if blink.setOutTemplate(self.outStr, '|') > 0: raise Exception("Output Template Invalid")
        
        
        #create parsed table first
        extra_columns = map(lambda x: "''::text as "+x.lower(), self.outStr)
        extra_columns = ",".join(extra_columns)
        create_query = """
            drop table if exists %s;
            
            select *, ''::text as mm_note, %s
            into %s
            from %s;
            
            alter table %s
            add CONSTRAINT fn_%s_pk PRIMARY KEY (mm_key);
            
        """ % (parsed_table, extra_columns, parsed_table, src_table, parsed_table, parsed_table)
        
        dtconfig.DB.query(create_query)
        #address1,address2,address3
        mm_address = addresses.split(',')
        if len(mm_address) > 6:
            raise Exception('Can not be more than 6 address lines')
        elif len(mm_address) > 4:
            #append space to 6 addresses
            #then marge subrb state postcode to address7
            num_rest = 6 - len(mm_address)
            for i in range(num_rest):
                mm_address.append("''")
            
            line7 = "%s||' '||%s||' '||%s" % (suburb, state, postcode)
            
            mm_address.append(line7)
            
        else:
            num_rest = 4 - len(mm_address)
            for i in range(num_rest):
                mm_address.append("''")
                
            mm_address.append(suburb)
            mm_address.append(state)
            mm_address.append(postcode)
            
        #get fields to parse
        #print "||'|'||".join(mm_address)
        get_query = """
            select mm_key, %s as mm_address
            from %s
        """ % ("||'|'||".join(mm_address),parsed_table)
        
        results = dtconfig.DB.query(get_query)
        update_query = """
            update %s
            set %s
            where mm_key = %d
        """
        for result in results:
            mm_key = result.mm_key
            
            mm_address = result.mm_address
            mm_address = mm_address.encode('utf-8')
            
            parsed_address = blink.searchAMAS(mm_address)
            update_fields = ""
            for k, v in parsed_address.items():
                update_fields = update_fields + "%s='%s'," % (k, v.replace("'","''"))
            update_fields = update_fields[:-1]
            
            real_update_query = update_query % (parsed_table, update_fields, mm_key)
            count = dtconfig.DB.query(real_update_query)
            #print '%d = %d updated' % (mm_key, count)
            
        #then, update parsed fields
if __name__ == '__main__':

    #app = CleanDPID('lu_snowgum_preclean_parsed',"address_line_1","address_line_2","address_line_3","postcode","country")
    #app = CleanDPID('lu_saddle_preclean_parsed',"address,address2","city","state","postcode","country")
    t0 = time.time()
    app = Parse()
    app.parse('lu_openuni_preclean',"address1,address2,address3","suburb","state","postcode","country")
    duration = int(time.time()-t0)
    print duration