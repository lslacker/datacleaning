#!/usr/bin/env python
from __future__ import division
import sys
sys.path.append(r'D:\0_works\pyhon_projects\_lib')
from blink import addressparser
import difflib
#from googlemaps import GoogleMaps
#from googlemaps import GoogleMapsError
import re
import dtconfig

RAW_WHITE_SPACE='`~!@#$%^&*{}()_<>?,./ \'"'
STREET_TYPE = 'ALLEY|ALY|ALLY|ARCADE|ARC|AVENUE|AVE|BOULEVARD|BLVD|BVD|ROAD|RD|STREET|ST|STR|DRIVE|DR|DRV|CLOSE|CL|LANE|LN|MANOR|MNR|MEWS|PLACE|PL|ROW|TERRACE|TER|TCE|TRACE|TRCE|TRAIL|TRL|COURT|CT|CIRCUS|CIR|CIRCLE|CIRC|CRESCENT|CRES|CRESC|LOOP|OVAL|QUADRANT|SQUARE|SQ|GROVE|GRV|PARKWAY|PKWY|RISE|ESPLANADE|ESP|PARADE|PDE|PROMENADE|PROM|WALK|HIGHWAY|HWY|CRT'
PROPER_STATE = 'V[., ]*I[., ]*C|N[., ]*S[., ]*W[., ]*|Q[., ]*L[., ]*D[., ]*|A[., ]*C[., ]*T[., ]*|T[., ]*A[., ]*S[., ]*|N[., ]*T[., ]*|S[., ]*A[., ]*|W[., ]*A[., ]*'

def look_up_pcdb_1(could_be_suburb):
    
    if re.search(r'\d+',could_be_suburb, re.I):
        return False
    
    results = dtconfig.DB.query("""
        select distinct locality, state, pcode 
        from pcdb
        where upper(locality) ~* '^%s'
    """ % could_be_suburb.replace("'","''").strip())
    
    if results:
        return True
        
    return False

def look_up_pcdb(could_be_suburb):
    
    if re.search(r'\d+',could_be_suburb, re.I):
        return False
    if re.search(r'\[', could_be_suburb, re.I) and re.search(r'\]', could_be_suburb, re.I):
        pass
    else:
        could_be_suburb = could_be_suburb.replace('[','')
        could_be_suburb = could_be_suburb.replace(']','')
        could_be_suburb = could_be_suburb.replace('\\','')
        could_be_suburb = re.sub(r'[.,]',' ',could_be_suburb)
        could_be_suburb = could_be_suburb.strip()
        could_be_suburb = re.sub(r'\b[Mm][Tt]\b','Mount',could_be_suburb)
        #(N|E|W|S|NTH|STH|UPP|LWR|UPPR)
        could_be_suburb = re.sub(r'\b([Nn]|[Nn][Tt][Hh])\b','North',could_be_suburb)
        could_be_suburb = re.sub(r'\b([Ee])\b','East',could_be_suburb)
        could_be_suburb = re.sub(r'\b([Ss]|[Ss][Tt][Hh]|[Ss][Oo][Uu])\b','South',could_be_suburb)
        could_be_suburb = re.sub(r'\b([Ww])\b','West',could_be_suburb)
        could_be_suburb = re.sub(r'\b([Uu][Pp][Pp][Pp]*)\b','Upper',could_be_suburb)
        could_be_suburb = re.sub(r'\b([Ll][Ww][Rr]*)\b','Lower',could_be_suburb)
        
        
    results = dtconfig.DB.query("""
        select distinct locality, state, pcode 
        from pcdb
        where upper(locality) ~* '^%s'
    """ % could_be_suburb.replace("'","''").strip())
    
    if results:
        return True
    else:
        match_obj_1 = re.match(r'^(EAST|SOUTH|NORTH|WEST|UPPER|LOWER)\b(.+)$',could_be_suburb, re.I)
        match_obj_2 = re.match(r'^(.+)\b(EAST|SOUTH|NORTH|WEST|UPPER|LOWER)$',could_be_suburb, re.I)
        if match_obj_1:
            could_be_suburb = match_obj_1.group(2).strip() + ' ' + match_obj_1.group(1).strip()
            
            results = dtconfig.DB.query("""
                select distinct locality, state, pcode 
                from pcdb
                where upper(locality) ~* '^%s'
            """ % could_be_suburb.replace("'","''").strip())
            if results:
                return True
            else:
                could_be_suburb = match_obj_1.group(1).strip()
                results = dtconfig.DB.query("""
                    select distinct locality, state, pcode 
                    from pcdb
                    where upper(locality) ~* '^%s'
                """ % could_be_suburb.replace("'","''").strip())
                if results:
                    return True
        elif match_obj_2:
            
            could_be_suburb = match_obj_2.group(2).strip() + ' ' + match_obj_2.group(1).strip()
            
            results = dtconfig.DB.query("""
                select distinct locality, state, pcode 
                from pcdb
                where upper(locality) ~* '^%s'
            """ % could_be_suburb.replace("'","''").strip())    
            if results:
                return True
            else:
                could_be_suburb = match_obj_2.group(2).strip()
                results = dtconfig.DB.query("""
                    select distinct locality, state, pcode 
                    from pcdb
                    where upper(locality) ~* '^%s'
                """ % could_be_suburb.replace("'","''").strip())
                if results:
                    return True
            
    return False
            
    
def street_in_suburb(full_suburb,full_address='n/a'):
   
    b = re.match('^(.+)\\b(%s)\\b[.,]*(.*)$' % STREET_TYPE, full_suburb, re.I)
    print '*'*30
    print full_address
    if b:
        if re.match(r'^[0-9 ]*$', full_address, re.I):
            return (True,b.group(1)+b.group(2),b.group(3),'0') 
        if not re.match('^(.+)\\b(%s)\\b[.,]*(.*)$' % STREET_TYPE, full_address, re.I):
            return (True,b.group(1)+b.group(2),b.group(3),'0') 
            
        suburb_part1 = b.group(1).strip()
        suburb_part2 = b.group(2).strip()
        suburb_part3 = b.group(3).strip().replace(',','')
        
        #A'Beckett -> ABeckett    
        suburb_part1 = suburb_part1.replace('A\'Bec','ABec')
        
        #just for databaseq query
        spelling_mistake_suburb_part1 = suburb_part1[:2]
        for i in range(3, len(suburb_part1)):
            spelling_mistake_suburb_part1 += '[a-z]*'+suburb_part1[i]
        print spelling_mistake_suburb_part1
        new_full_suburb = suburb_part1+' '+suburb_part2+' '+suburb_part3
        new_full_suburb = new_full_suburb.strip()
       
        if look_up_pcdb(new_full_suburb):
            return (False, '', full_suburb,'1')
        elif ( re.search('^ST$', suburb_part2, re.I)
               #and re.search('KILDA', suburb_part3, re.I) 
               and re.search('^(E|N|W|S|M[T]*)', suburb_part1, re.I)
             ):
             return (False, '', full_suburb,'2')
        elif ( re.search('^RD$', suburb_part2, re.I) and
               re.search('KILDA', suburb_part1, re.I)       
             ):
             return (False, '', suburb_part1+' ROAD '+suburb_part3,'3')
        elif not re.search('^\\s*$', suburb_part3, re.I) and look_up_pcdb(suburb_part3):
            return (True, suburb_part1+' '+suburb_part2, suburb_part3,'4')
        elif re.search('\\d+', suburb_part1, re.I):
            return (True, suburb_part1+' '+suburb_part2, suburb_part3,'5')
        elif not look_up_pcdb(spelling_mistake_suburb_part1+' '+suburb_part2[0]):
            if look_up_pcdb(spelling_mistake_suburb_part1) and re.search('^\\s*$', suburb_part3, re.I):
                return (True, '', suburb_part1,'8')
            else:
                return (True, suburb_part1+' '+suburb_part2, suburb_part3,'6')
        elif look_up_pcdb(spelling_mistake_suburb_part1+' '+suburb_part2[0]) and re.search('^\\s*$', suburb_part3, re.I):
            return (False, '', full_suburb,'7')
        #elif look_up_pcdb(spelling_mistake_suburb_part1) and re.search('^\\s*$', suburb_part3, re.I):
        #    return (True, '', suburb_part1,'8')
        
    return (False,'',full_suburb,'-1')

def box_in_suburb(full_suburb):
    b = re.match('^(P*.*\\s*box\\s*\\d+)[.,]*(.*)$', full_suburb, re.I)
    
    if b:
        suburb_part1 = b.group(1)
        suburb_part2 = b.group(2).strip()
        return (True, suburb_part1, suburb_part2, '1')
        
    b = re.match('^P[., ]*O[., ]*(\\d+)[.,]*(.*)$', full_suburb, re.I)
    
    if b:
        suburb_part1 = 'PO Box '+b.group(1)
        suburb_part2 = b.group(2).strip()
        return (True, suburb_part1, suburb_part2, '1')    
    
    b = re.match('^(X[., ]*\\d+)[.,]*(.*)$', full_suburb, re.I)
    
    if b:
        suburb_part1 = b.group(1)
        suburb_part2 = b.group(2).strip()
        return (True, suburb_part1, suburb_part2, '1')    
        
    return (False,'',full_suburb,'-1')

def is_national_state(full_state):
    if re.match('^(%s)$' % PROPER_STATE, full_state, re.I):
        return (True,'',re.sub('[., ]','',full_state))

def find_oseas(could_be_oseas):
    could_be_oseas = re.sub(r'[.?*+/\\\]\[]','',could_be_oseas)
    could_be_oseas = could_be_oseas.replace("'","\\'")
    
    could_be_oseas_list = could_be_oseas.split(',')
    could_be_oseas_list = map(lambda x: x.strip(), could_be_oseas_list)
    found = False
    country = ''
    while not found and len(could_be_oseas_list) > 0:
        found, country = look_for_oseas(could_be_oseas_list.pop(0))
    return (found, country)    
    
def look_for_oseas(could_be_oseas):
    result = (False,'')
    
    if len(could_be_oseas) > 3:
        select_query = """
            select distinct country
            from world_city
            where country <> 'AU' and (city ~* '^%s$' or '%s' ilike city)
        """ % (could_be_oseas, could_be_oseas)
        
        results = dtconfig.DB.query(select_query)
        
        if results:
            if len(results) == 1:
                result = (True, results[0]['country'])
            else:
                result= (True, 'oseas')
        else:
            select_query = """
                select distinct country_name
                from countrycode
                where country_name <> 'Australia' and (upper(country_name) = upper('%s') )
            """ % (could_be_oseas)
            results = dtconfig.DB.query(select_query)            
            if results:
                if len(results) == 1:
                    result = (True, results[0]['country_name'])
                else:
                    result= (True, 'oseas')        
    elif len(could_be_oseas) == 2:
        select_query = """
            select distinct country
            from world_city
            where country <> 'AU' and upper(region) = upper('%s')
        """ % (could_be_oseas)
        
        results = dtconfig.DB.query(select_query)
        
        if results:
            if len(results) == 1:
                result = (True, results[0]['country'])
            else:
                result= (True, 'oseas')
        else:           
            select_query = """
                select distinct country_name
                from countrycode
                where country_name <> 'Australia' and (upper(country_code_2) = upper('%s') or upper(country_code_3) = upper('%s'))
            """ % (could_be_oseas, could_be_oseas)
            
            results = dtconfig.DB.query(select_query)
            
            if results:
                if len(results) == 1:
                    result = (True, results[0]['country_name'])
                else:
                    result= (True, 'oseas')
            
    return result
    
class CleanNonDPID:
    '''
        Address Cleaning
    '''
    def __init__(self, src_table, addresses, suburb, state, postcode, country):
        self.src_table = src_table
        self.clean_table = self.src_table + '_nondpid'
        self.addresses = addresses
        self.address_list = addresses.split(',')
        self.address_list = map(lambda x: x.strip(), self.address_list)
        self.suburb = suburb
        self.state = state
        self.postcode = postcode
        self.country = country
        self.note= []
        self.lookup = addressparser.AddressLookup()
        self.lookup1 = addressparser.AddressLookupAMAS()
    
    def clean(self):
        
        #create clean_table from src
        self.create_cleaned_table()
        self.step1()
        self.step2()
        self.step3()
        self.step4()
        #self.step5()
        #self.step5_pre()
        #self.step5_pre_2()
        #self.step5()
        #self.step6()
        #how to check suburb in address
        #check 2 addresses
        #if suburb contain street information
    
    def step5(self):
        select_query = """
            select *
            from %s
            where mm_note = '' 
                  and exists (
                                select 1 from pcdb
                                where   upper(pcdb.locality) = upper(%s.%s) 
                            )
        """ % (self.clean_table, self.clean_table, self.suburb)
        results = dtconfig.DB.query(select_query)
        for result in results:
            mm_key = result['mm_key']
            suburb = result[self.suburb]
            state = result[self.state]
            postcode = result[self.postcode]
            country = result[self.country]
            if country == None:
                country = ''
            addresses = []
            address_update_str = ''
            for each_address in self.address_list:
                addresses.append(result[each_address])
                address_update_str += each_address +"= '%s',"
            address_update_str = address_update_str[:-1]
            print mm_key
            print suburb
            print state
            print postcode
            
    def step4(self):
        select_query = """
            select * 
            from %s
            where %s = '' and mm_note = '' and mm_note !~* 'invalid' and mm_preclean !~* 'invalid'
        """ % (self.clean_table, self.country)
        
        results = dtconfig.DB.query(select_query)
        for result in results:
            mm_key = result['mm_key']
            suburb = result[self.suburb]
            state = result[self.state]
            postcode = result[self.postcode]
            addresses = []
            
            for each_address in self.address_list:
                addresses.append(result[each_address])
            
            is_already_updated = False
            if not re.match(r'^\s*$', state, re.I):    
                if not re.search(r'\b(NSW|ACT|QLD|VIC|TAS|NT|WA|SA)\b', state, re.I):
                    
                    print '*'
                    print state
                    print '*'
                    (is_oseas, country_code) = find_oseas(state)
                    
                    if is_oseas:
                        
                        update_query = """
                            update %s
                            set %s = '%s', mm_note = mm_note || 'oseas'
                            where mm_key = %d
                        """ % (self.clean_table, self.country, country_code.replace("'","''"), mm_key)
                        
                        dtconfig.DB.query(update_query)
                        is_already_updated = True
                        
            if not is_already_updated:
                if not re.match(r'^\s*$', postcode, re.I) and not re.match(r'^\d+$', postcode, re.I):  
                    if not re.search(r'\b(NSW|ACT|QLD|VIC|TAS|NT|WA|SA)\b', postcode, re.I):
                        print '*'
                        print postcode
                        print '*'
                        (is_oseas, country_code) = find_oseas(postcode)
                        
                        if is_oseas:
                            
                            update_query = """
                                update %s
                                set %s = '%s', mm_note = mm_note || 'oseas'
                                where mm_key = %d
                            """ % (self.clean_table, self.country, country_code.replace("'","''"), mm_key)
                            
                            dtconfig.DB.query(update_query)
                            is_already_updated = True
            
            if not is_already_updated:
                if not re.match(r'^\s*$', suburb, re.I) and not re.match(r'^\d+$', suburb, re.I):  
                    if not re.search(r'\b(NSW|ACT|QLD|VIC|TAS|NT|WA|SA)\b', suburb, re.I):
                        print '*'
                        print suburb
                        print '*'
                        (is_oseas, country_code) = find_oseas(suburb)
                        
                        if is_oseas:
                            
                            update_query = """
                                update %s
                                set %s = '%s', mm_note = mm_note || 'oseas'
                                where mm_key = %d
                            """ % (self.clean_table, self.country, country_code.replace("'","''"), mm_key)
                            
                            dtconfig.DB.query(update_query)
                            is_already_updated = True
        
    def step3(self):
    
        select_query = """
            select *
            from %s
            where mm_note = '' 
                  and exists (
                                select 1 from pcdb
                                where   upper(pcdb.locality) = upper(%s.%s) 
                                    and upper(pcdb.state) = upper(%s.%s) 
                            )
        """ % (self.clean_table, self.clean_table, self.suburb, self.clean_table, self.state)
        results = dtconfig.DB.query(select_query)
        for result in results:
            mm_key = result['mm_key']
            suburb = result[self.suburb]
            state = result[self.state]
            postcode = result[self.postcode]
            country = result[self.country]
            if country == None:
                country = ''
            addresses = []
            address_update_str = ''
            for each_address in self.address_list:
                addresses.append(result[each_address])
                address_update_str += each_address +"= '%s',"
            address_update_str = address_update_str[:-1]
            new_suburb, new_postcode = self.find_postcode(' '.join(addresses), suburb, state, postcode, country)
            print '$>', new_suburb
            print '$>', new_postcode
            if new_postcode:
                update_query = """
                    update %s
                    set %s = '%s', %s = '%s', mm_note = mm_note || 'UPDATE_PCD'
                    where mm_key = %d
                """ % (self.clean_table, self.suburb, new_suburb.replace("'","''"), self.postcode, new_postcode, mm_key)
                print dtconfig.DB.query(update_query)
            
    def find_postcode(self, address, suburb, state, postcode, country):
        print '*'*10 + 'You are checking' + '*'*10
        print '*'*2 + address + '*'*2
        print '*'*2 + suburb + '*'*2
        print '*'*2 + state + '*'*2
        print '*'*2 + postcode + '*'*2
        print '*'*2 + country + '*'*2
        inStr=['LOC','STT']
        outStr=['PCD']
        
        inStr1=['ADR']
        outStr1=['DPI','CLC','STT', 'CPC','PRI','ERR']
        
        subQuery = '%s|%s' % (suburb.upper(), state.upper())
        
        self.lookup.parse(inStr=inStr,outStr=outStr,address=subQuery)
        retCount, results = self.lookup.getMeThis('PCD')
        
        for each_result in results:
            subQuery1 = '%s %s %s %s' % (address.upper(), suburb.upper(), state.upper(), each_result)
            self.lookup1.parse(inStr=inStr1,outStr=outStr1,address=subQuery1)
            
            count_dpi, result_dpi  = self.lookup1.getMeThis('DPI')
            count_pri, result_pri  = self.lookup1.getMeThis('PRI')
            count_err, result_err  = self.lookup1.getMeThis('ERR')
            print subQuery1
            print result_dpi
            print result_pri
            print result_err
            #and (dont_need_pri or result_pri.strip() == 'R')
            if result_dpi.strip() != '0' :
                count_loc, result_loc  = self.lookup1.getMeThis('CLC')
                count_pcd, result_pcd  = self.lookup1.getMeThis('CPC')
                break
        else:
            return (None, None)
        return (result_loc.strip(),result_pcd.strip())
        
    def step2(self):
    
        select_query = """
            select *
            from %s
            where mm_note = '' 
                  and exists (
                                select 1 from pcdb
                                where   upper(pcdb.state) = upper(%s.%s) 
                                    and upper(pcdb.pcode) = upper(%s.%s) 
                            )
        """ % (self.clean_table, self.clean_table, self.state, self.clean_table, self.postcode)
        results = dtconfig.DB.query(select_query)
        for result in results:
            mm_key = result['mm_key']
            suburb = result[self.suburb]
            state = result[self.state]
            postcode = result[self.postcode]
            country = result[self.country]
            if country == None:
                country = ''
            addresses = []
            
            address_update_str = ''
            for each_address in self.address_list:
                addresses.append(result[each_address])
                address_update_str += each_address +"= '%s',"
            address_update_str = address_update_str[:-1]
            
            (to_update, new_addresses, new_suburb, mm_note, new_state, new_postcode) = self.verify_suburb(addresses, suburb, state, postcode, country)
            if to_update:
                #to update
                if mm_note == 'not yet implement':
                    update_query = """
                        update %s
                        set mm_note = 'not yet'
                        where mm_key = %d
                    """ % (self.clean_table, mm_key)
                    print dtconfig.DB.query(update_query)
                else:
                    new_addresses = map(lambda x: x.replace("'","''"), new_addresses)
                    new_addresses = map(lambda x: x.replace('\\','\\\\'), new_addresses)
                    update_query = """
                        update %s
                        set mm_note = 'UPDATE_LOC_%s',%s = '%s', %s = '%s', %s = '%s',
                    """
                    update_query += address_update_str + """
                        where mm_key = %s
                    """ 
                    
                    tuple_1 = (self.clean_table, mm_note, self.suburb, new_suburb.replace("'","''").replace('\\','\\\\'), self.state, new_state.replace("'","''").replace('\\','\\\\'), self.postcode, new_postcode)
                    
                    tuple_2 = tuple(new_addresses)
                    tuple_3 = (mm_key,)
                    
                    final_tuple = tuple_1 + tuple_2 + tuple_3
                    print update_query
                    print final_tuple
                    print dtconfig.DB.query(update_query % final_tuple)
            else:
                #this record is invalid
                
                update_query = """
                    update %s
                    set mm_note = 'invalid'
                    where mm_key = %d
                """ % (self.clean_table, mm_key)
                print dtconfig.DB.query(update_query)
                
    
        
    def verify_suburb(self, address_lines, suburb, state, postcode, country):
        
        print '*'*10 + 'You are checking' + '*'*10
        print '*'*2 + '->'.join(address_lines) + '*'*2
        print '*'*2 + suburb + '*'*2
        print '*'*2 + state + '*'*2
        print '*'*2 + postcode + '*'*2
        print '*'*2 + country + '*'*2
        
        full_address = ' '.join(address_lines)
        full_address = full_address.strip()
        if re.match(r'^[^a-z0-9]*$', suburb, re.I):
            print 'suburb is blank'
            
            i = len(address_lines)
            nearest_address = address_lines[i-1]
            while re.match(r'^[^a-z0-9]*$', nearest_address, re.I) and i > 0:
                i = i - 1
                nearest_address = address_lines[i-1]
            else:
                #the loop is over
                if i <= 0:
                    print 'invalid record'
                    return (False, address_lines, suburb,'invalid record', state, postcode)
                else:
                    print 'your nearest address is ', nearest_address
                    if look_up_pcdb(nearest_address):
                        print 'yes, your nearest address is a suburb'
                        print 'at index %d' % i
                        address_lines[i-1] = ''
                        suburb = nearest_address
                        print address_lines
                        print suburb
                        return (True, address_lines, suburb,'STR_is_LOC', state, postcode)
                    else:
                        print 'no, could be others'
                        match_obj = re.match(r'^(.+)\b(VIA)\b(.+)$',nearest_address,re.I)
                        if match_obj:
                            _suburb_left = match_obj.group(1).strip()
                            _via = match_obj.group(2).strip()
                            _suburb_right = match_obj.group(3).strip()
                            
                            if re.search(r'\d+',_suburb_left):
                                print 'suburb_left of via is a street'
                                address_lines[i-1] = _suburb_left+ ' ' +_via
                                suburb = _suburb_right
                                print address_lines
                                print suburb
                                return (True, address_lines, suburb,'L_VIA_R_1', state, postcode)
                            elif look_up_pcdb(_suburb_left):
                                print 'suburb_left is a suburb'
                                address_lines[i-1] = _via+' '+_suburb_right
                                suburb = _suburb_left
                                print address_lines
                                print suburb
                                return (True, address_lines, suburb,'L_VIA_R_2', state, postcode)
                            else:
                                print 'suburb_left spelling mistake'
                                address_lines[i-1] = _via+' '+_suburb_right
                                new_suburb, new_postcode = self.find_suburb(nearest_address, state, postcode)
                                if new_suburb != None:
                                    return (True, address_lines, new_suburb.strip(),'Fill_Suburb_6', state, new_postcode.strip())
                                
                        match_obj = re.match(r'^(VIA)\b(.+)$',nearest_address,re.I)
                        if match_obj:
                            _via = match_obj.group(1).strip()
                            _suburb_right = match_obj.group(2).strip()
                            address_lines[i-1] = _via
                            suburb = _suburb_right
                            print address_lines
                            print suburb
                            return (True, address_lines, suburb,'VIA_R', state, postcode)
                        
                        match_obj = re.match(r'^(C/[-0o])*\s*(.+) Post\s*Office',nearest_address,re.I)
                        if match_obj:
                            print 'C/- (suburb) post office'
                            suburb = match_obj.group(2)
                            print address_lines
                            print suburb
                            return (True, address_lines, suburb,'PO_1', state, postcode)
                        
                        match_obj = re.match(r'^(C/[-0o])*\s*P[.,]*O[.,]*\s+(BOX[., ]*)*(\D+)$',nearest_address,re.I)
                        if match_obj:
                            print 'C/- (PO) suburb'
                            suburb = match_obj.group(3)
                            print address_lines
                            print suburb
                            return (True, address_lines, suburb,'PO_2', state, postcode)
                            
                        match_obj = re.match(r'^(.+)\s+(%s)$' % STREET_TYPE, nearest_address,re.I) 
                        if match_obj:
                            print 'there is no suburb'
                            new_suburb, new_postcode = self.find_suburb(nearest_address, state, postcode)
                            if new_suburb != None:
                                return (True, address_lines, new_suburb.strip(),'Fill_Suburb_1', state, new_postcode.strip())
                        
                        match_obj = re.match(r'^[G]*[., ]*P(.+)Box\s*\d+$', nearest_address,re.I) 
                        if match_obj:
                            print 'there is no suburb'
                            new_suburb, new_postcode = self.find_suburb(nearest_address, state, postcode)
                            if new_suburb != None:
                                return (True, address_lines, new_suburb.strip(),'Fill_Suburb_2', state, new_postcode.strip())
                        
                        (is_street_in_suburb, street_part, new_suburb, method) = street_in_suburb(nearest_address, full_address)
                        if is_street_in_suburb:
                            address_lines[i-1] = street_part
                            to_be_suburb, to_be_postcode = self.find_suburb((' '.join(address_lines)).strip(), state, postcode)
                            if to_be_suburb != None:
                                return (True, address_lines, to_be_suburb.strip(),'Fill_Suburb_9', state, to_be_postcode.strip())
                            else:
                                return (True, address_lines, new_suburb.strip(),'STR_is_LOC_1', state, postcode)
                        
                        (is_box_in_suburb, street_part, new_suburb, method) = box_in_suburb(nearest_address)
                        if is_box_in_suburb:
                            address_lines[i-1] = street_part
                            to_be_suburb, to_be_postcode = self.find_suburb((' '.join(address_lines)).strip(), state, postcode)
                            if to_be_suburb != None:
                                return (True, address_lines, to_be_suburb.strip(),'Fill_Suburb_10', state, to_be_postcode.strip())
                            else:
                                return (True, address_lines, new_suburb.strip(),'STR_is_LOC_2', state, postcode)
                            
                        
                #what to do next
                #search address
                print 'searching address'
                
                to_search_address = address_lines[:(-1)*(i-1)]
                print to_search_address
                if to_search_address:
                    new_suburb, new_postcode = self.find_suburb(' '.join(to_search_address), state, postcode)
                    if new_suburb != None:
                        return (True, address_lines, new_suburb.strip(),'Fill_Suburb_7', state, new_postcode.strip())
                    
                    #address_lines[i-1] = ''
                    #suburb = nearest_address
                    #print address_lines
                    #print suburb
                    #return (True, address_lines, suburb,'check_suburb', state, postcode)
                
                return (True, address_lines, suburb,'check_suburb', state, postcode)
        else:
            print 'suburb is not blank'
            
            (is_street_in_suburb, street_part, new_suburb, method) = street_in_suburb(suburb, full_address)
            print (is_street_in_suburb, street_part, new_suburb, method)
            if is_street_in_suburb:
                print 'street in suburb'
                new_suburb = new_suburb.strip()
                if re.match(r'^\s*$', new_suburb, re.I):
                    if re.search(r'\d+', street_part,re.I):
                        #find new suburb
                        new_suburb, new_postcode = self.find_suburb(street_part, state, postcode)
                        if new_suburb != None:
                            address_lines[-1] = (address_lines[-1]+ ' ' + street_part).strip()
                            return (True, address_lines, new_suburb.strip(),'STR_in_LOC_Fill_Suburb_3', state, new_postcode.strip())
                    else:
                        if (re.match(r'^[0-9 ]*$', full_address, re.I) or
                           not re.match('^(.+)\\b(%s)\\b[.,]*(.*)$' % STREET_TYPE, full_address, re.I)):
                            address_lines[-1] = (address_lines[-1]+ ' ' + street_part).strip()
                            to_be_suburb, new_postcode = self.find_suburb(' '.join(address_lines).upper(), state, postcode)
                            if to_be_suburb != None:
                                return (True, address_lines, to_be_suburb.strip(),'STR_in_LOC_Fill_Suburb_4', state, new_postcode.strip())
                            else:
                                #could be wrong postcode                                
                                return (True, address_lines, new_suburb,'check_suburb_postcode', state, postcode)
                        else:
                            #street_part is suburb
                            #could be spelling mistake
                            new_suburb, new_postcode = self.find_suburb(' '.join(address_lines).upper(), state, postcode)
                            if new_suburb != None:
                                return (True, address_lines, new_suburb.strip(),'STR_in_LOC_Fill_Suburb_4_[%s]' % suburb, state, new_postcode.strip())
                            else:
                                #could be wrong postcode                                
                                return (True, address_lines, suburb,'check_suburb_postcode', state, postcode)
                else:        
                    address_lines[-1] = (address_lines[-1]+ ' ' + street_part).strip()  
                    to_be_suburb, new_postcode = self.find_suburb(' '.join(address_lines).upper(), state, postcode)
                    
                    if to_be_suburb != None:
                        return (True, address_lines, to_be_suburb.strip(),'STR_in_LOC_Fill_Suburb_8', state, new_postcode.strip())
                    else:
                        #could be wrong postcode                                
                        return (True, address_lines, new_suburb,'check_suburb_postcode', state, postcode)
                    
                return (True, address_lines, suburb,'not yet implement', state, postcode)        
            
            (is_box_in_suburb, street_part, new_suburb, method) = box_in_suburb(suburb)
            if is_box_in_suburb:
                print 'box in suburb'
                address_lines[-1] = (address_lines[-1]+ ' ' + street_part).strip()
                suburb = new_suburb.strip()
                to_be_suburb, new_postcode = self.find_suburb(' '.join(address_lines), state, postcode)
                if to_be_suburb:
                    return (True, address_lines, to_be_suburb,'BOX_in_LOC_Fill_Suburb_9', state, new_postcode)
                    
                return (True, address_lines, suburb,'BOX_in_LOC', state, postcode)
            
            match_obj = re.match(r'^(VIA)[ .,]*(.+)$', suburb, re.I)
            if match_obj:
                print 'via suburb'
                address_lines[-1] = (address_lines[-1]+ ' ' + match_obj.group(1)).strip()
                suburb = match_obj.group(2)
                return (True, address_lines, suburb,'VIA_R_in_LOC', state, postcode)
            
            match_obj = re.match(r'^(.+)[.,]*\s+[.,]*(VIA)[.,]*\s+[.,]*(.+)$', suburb, re.I)
            if match_obj:
                print 'via suburb'
                address_lines[-1] = (address_lines[-1]+ ' ' + match_obj.group(1)+ ' '+match_obj.group(2)).strip()
                suburb = match_obj.group(3)
                return (True, address_lines, suburb,'L_VIA_R_in_LOC', state, postcode)
                
           
            match_obj = re.match(r'^(.+)[., ]*\b(?<!Of\s)(%s)$' % state, suburb, re.I)
            if match_obj:
                print 'suburb contains state'
                #address_lines[-1] = (address_lines[-1]+ ' ' + match_obj.group(1)+ ' '+match_obj.group(2)).strip()
                suburb = match_obj.group(1)
                return (True, address_lines, suburb,'STT_in_LOC', state, postcode)
                
                
            print 'could be spelling mistake'    
            print 'or wrong postcode '
            print 'or wrong suburb '    
            if look_up_pcdb(suburb):
                print 'check_suburb_state'
                new_suburb, new_postcode = self.find_suburb(' '.join(address_lines), state, postcode)
                print 'luan'
                print new_suburb
                print new_postcode
                print 'ulan'
                if new_suburb != None:
                    return (True, address_lines, new_suburb.strip(),'Fill_Suburb_11', state, new_postcode.strip())
                return (True, address_lines, suburb,'check_suburb_postcode', state, postcode)
            else:
                print 'could be spelling mistake'
                new_suburb, new_postcode = self.find_suburb(' '.join(address_lines), state, postcode)
                
                if new_suburb != None:
                    return (True, address_lines, new_suburb.strip(),'Fill_Suburb_5', state, new_postcode.strip())
                else:
                    print 'check_suburb_state'
                    return (True, address_lines, suburb,'check_suburb_postcode', state, postcode)
            
            new_suburb, new_postcode = self.find_suburb(' '.join(address_lines), state, postcode)
            if new_suburb:
                return (True, address_lines, new_suburb,'Fill_Suburb_10', state, new_postcode)
                
            #return (True, address_lines, suburb, 'not yet implement', state, postcode)
        print '-'*10 + 'END You are checking' + '-'*10
        return (True, address_lines, suburb, 'not yet implement', state, postcode)
        
    def find_suburb(self, address, state, postcode):
        inStr=['STT','PCD']
        outStr=['LOC']
        
        inStr1=['ADR']
        outStr1=['DPI','CLC','STT', 'CPC','PRI','ERR']
        
        subQuery = '%s|%s' % (state.upper(), postcode.upper())
        
        self.lookup.parse(inStr=inStr,outStr=outStr,address=subQuery)
        retCount, results = self.lookup.getMeThis('LOC')
        dont_need_pri = False
        #"RSD"
        #"LOCKED BAG"
        #"RMB"
        #"PO BOX"
        #"MS"
        #"PRIVATE BAG"
        #"GPO BOX"
        #"CMB"
        #"RMS"
        if re.search(r'\b(Rsd|Box|Bag|rmb|ms|cmb|rms)\b\s*\d+', address, re.I):
            dont_need_pri = True
        
        for each_result in results:
            subQuery1 = '%s %s %s %s' % (address.upper(), each_result, state.upper(), postcode.upper())
            print subQuery1
            print self.lookup1.parse(inStr=inStr1,outStr=outStr1,address=subQuery1)
            
            count_dpi, result_dpi  = self.lookup1.getMeThis('DPI')
            count_pri, result_pri  = self.lookup1.getMeThis('PRI')
            count_err, result_err  = self.lookup1.getMeThis('ERR')
            
            print result_dpi
            print result_pri
            print result_err
            if result_dpi.strip() != '0' and (dont_need_pri or result_pri.strip() == 'R'):
                count_loc, result_loc  = self.lookup1.getMeThis('CLC')
                count_pcd, result_pcd  = self.lookup1.getMeThis('CPC')
                delta = abs(int(result_pcd) - int(postcode))
                print 'delta=%d' % delta
                if delta <= 3:
                    break
                else:
                    pass
        else:
            return (None, None)
        return (result_loc.strip(),result_pcd.strip())
            
        
    def step1(self):
        update_query = """
            
            update %s
            set mm_note = 'GOODSSP'
            where exists (
                            select 1 from pcdb
                            where   upper(pcdb.locality) = upper(%s.%s) 
                                and upper(pcdb.state)    = upper(%s.%s) 
                                and upper(pcdb.pcode)    = upper(%s.%s) 
                         )
        """ % (self.clean_table, self.clean_table,self.suburb, self.clean_table,self.state, self.clean_table,self.postcode)
        print dtconfig.DB.query(update_query)
        
        update_query = """
            update %s
            set %s = pcdb.state, mm_note = 'UPDATE_STT'
            from pcdb
            where   upper(pcdb.locality) = upper(%s.%s) 
            and upper(pcdb.pcode)    = upper(%s.%s)                          
            and mm_note = ''
        """ % (self.clean_table, self.state, self.clean_table, self.suburb, self.clean_table, self.postcode)
        print dtconfig.DB.query(update_query)
        
        update_query = """
            update %s
            set mm_note = mm_note || '|%s'
            where mm_note <> '' and 
        """
        for each_address in self.address_list:
            update_query += """%s ~* '^[ ~\\!@#$^&*()_/.,"'']*$' and """ % each_address
            
        update_query = update_query[:-4]
        print update_query
        print dtconfig.DB.query(update_query % (self.clean_table, 'invalid'))
        
    def create_cleaned_table(self):
        create_query = """
            DROP TABLE IF EXISTS %s;
            
            select *
            into %s
            from %s 
            where dpi = '0';
            
            CREATE INDEX %s_idx1 on %s(mm_key);
            
        """ % (self.clean_table, self.clean_table, self.src_table, self.clean_table, self.clean_table)
        
        dtconfig.DB.query(create_query)    
if __name__ == '__main__':

    #app = CleanNonDPID('lu_snowgum_preclean_parsed',"address_line_1","address_line_2","address_line_3","postcode","country")
    #app = CleanNonDPID('lu_saddle_preclean_parsed',"address,address2","city","state","postcode","country")
    app = CleanNonDPID('lu_blue_preclean_parsed',"address_1,address_2","address_3","address_4","postcode","country")
    #app = CleanNonDPID('lu_openuni_preclean_parsed',"address1","suburb_","state_","postcode_","country")
    app.clean()
    #app.verify_suburb(['2576',''], 'GOLD COAST HIGHWAY', 'QLD', '4218', '')
    
    