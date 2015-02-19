#!/usr/bin/env python
from __future__ import division
import re
import difflib
import sys
#sys.path.append(r'Z:\melmailing\_lib')
sys.path.append(r'D:\0_works\pyhon_projects\_lib')
from blink import addressparser
import dtconfig

RAW_WHITE_SPACE='`~!@#$%^&*{}()_<>?,./ \'"'

def is_not_suburb(suburb):
    result = False
    if suburb.upper().startswith('OPPOSITE') or suburb.upper().startswith('OPP') or suburb.upper().startswith('CNR') or suburb.upper().startswith('CORNER'):
       result = True
    return result

def is_a_meaningful_word(a_word, count = 0):
    print '*'*80
    print 'count=%d' % count
    print 'a_word=%s' % a_word
    result = False
    
    if re.search(r'[0-9]+',a_word,re.I):
        return False
    
    myvars = dict(word = a_word)
    results = dtconfig.DB.select('worddict', vars = myvars, where="aword=upper($word)")
    if results:
        result = True
    
    if not result and count == 0:
        if re.search(r'^[od]',a_word,re.I):
            new_word = a_word[0] + "'" + a_word[1:]
            result = is_a_meaningful_word(new_word, 1)
    print '*'*80
    return result
    
def is_a_suburb(a_word):
    result = False
    myvars = dict(word = a_word)
    results = dtconfig.DB.select('pcdb', vars = myvars, where="upper(locality)=upper($word)")
    if results:
        result = True
    return result    
    
def is_a_state(a_word):
    result = False
    myvars = dict(word = a_word)
    results = dtconfig.DB.select('pcdb', vars = myvars, where="upper(state)=upper($word)")
    if results:
        result = True
    return result  
    
def is_in_mydict(a_word):
    result = False
    myvars = dict(word = a_word)
    results = dtconfig.DB.select('my_dict', vars = myvars, where="upper(words)=upper($word)")
    if results:
        result = True
    return result  

def is_world_city(a_word):
    result = False
    myvars = dict(word = a_word)
    results = dtconfig.DB.select('world_city', vars = myvars, where="upper(city)=upper($word)")
    if results:
        result = True
    return result  

def compare_2_addresses(address1, address2):
    s = difflib.SequenceMatcher(None, address1.upper(), address2.upper())
    matching_blocks =  s.get_matching_blocks()
    matching_blocks.pop()
    #print '<<<<',matching_blocks
    
    if not matching_blocks:
        return (0, '')
        
    address1_list = list(address1)
    address2_list = list(address2)    
    
    for each_matching_block in matching_blocks:
        #print each_matching_block
        a,b,size =  each_matching_block
        #print range(a,a+size)
        for i in range(a,a+size):
            address1_list[i] = '*'
        for i in range(b,b+size):
            address2_list[i] = '*'        
        address1_str=''.join(address1_list)
        address2_str = ''.join(address2_list)                    
    
    #print 'address1_str=',address1_str
    #print 'address2_str=',address2_str
    
    if re.match(r'^[*]+$',address2_str,re.I):
        #print '2.M1'
        return (2,'2.M1')
    elif re.match(r'^[*]+[a-z/ ]?[*]*$',address2_str,re.I):
        #print '2.M2'
        return (2,'2.M2')
    elif re.match(r'^[*]+[a-z]{,2}[*]$',address2_str,re.I):
        #print '2.M3'
        return (2,'2.M3')
    elif re.match(r'^[0-9]?[*]{,%d}[a-z* ]{,6}$' % len(address1_str),address2_str,re.I):
        #print '2.M4'
        return (2,'2.M4')
    elif re.match(r'^[*]+[a-z/ ]?[*]+[a-z]{,4}$',address2_str,re.I):
        #print '2.M5'
        return (2,'2.M5')
    if re.match(r'^[*]+$',address1_str,re.I):
        #print '1.M1'
        return (1,'1.M1')
    elif re.match(r'^[*]+[a-z/ ]?[*]*$',address1_str,re.I):
        #print '1.M2'
        return (1,'1.M2')
    elif re.match(r'^[*]+[a-z]{,2}[*]$',address1_str,re.I):
        #print '1.M3'
        return (1,'1.M3')
    elif re.match(r'^[0-9]?[*]{,%d}[a-z* ]{,6}$' % len(address2_str),address1_str,re.I):
        #print '1.M4'
        return (1,'1.M4')
    elif re.match(r'^[*]+[a-z/ ]?[*]+[a-z]{,4}$',address1_str,re.I):
        #print '1.M5'
        return (1,'1.M5')   
    else:
        return (0,'')
    
    #print '-'*40, 'NEXT RECORD', '-'*40   
        
            
class Clean:
    '''
        Address Cleaning
    '''
    def __init__(self, src_table, addresses, suburb, state, postcode, country):        
        self.src_table = src_table
        self.clean_table = self.src_table + '_preclean'
        self.addresses = addresses
        self.address_list = addresses.split(',')
        self.address_list = map(lambda x: x.strip(), self.address_list)
        self.suburb = suburb
        self.state = state
        self.postcode = postcode
        self.country = country
        self.note= []
        
    def clean(self):
        
        #create clean_table from src
        self.create_cleaned_table()
        self.step0()
        self.step1()
        self.step2()
        self.step3()
        self.step4()
        self.step8()
        self.step5()
        self.step6()
        self.step7()
        self.step9()
        self.step10()
        self.step11()
        self.step12()
        self.mark_invalid()
    
    def step12(self):
        select_query = """
            select * 
            from %s
            where %s ~* '^[A-z]$'
        """ % (self.clean_table, self.state)
        results = dtconfig.DB.query(select_query)
        for result in results:
            mm_key = result['mm_key']
            state = result[self.state]
            suburb = result[self.suburb]
            if suburb != '':
                could_be_new_state = suburb[-1]+state
                could_be_new_suburb = suburb[:-1]
                if state == 'V' and suburb.endswith('IC'):
                    could_be_new_state = 'VIC'
                    could_be_new_suburb = suburb[:-2]
                if is_a_state(could_be_new_state):
                    #update
                    dtconfig.DB.query("""
                        update %s
                        set %s = '%s', %s = '%s', mm_preclean=mm_preclean||'|half_stt_in_loc'
                        where mm_key = %d
                    """ % (self.clean_table, self.suburb, could_be_new_suburb.replace("'","''"), self.state, could_be_new_state.replace("'","''"), mm_key))
                    
                    
            
    def mark_invalid(self):
        address_update_str = ''
        for each_address in self.address_list:
            address_update_str += each_address + "~* '^\\\\W*$' and "
        address_update_str = address_update_str[:-5]
        
        update_query = """
            update %s
            set mm_preclean = mm_preclean || '|invalid'
            where %s and %s ~* '^\\\\W*$' and %s ~* '^\\\\W*$' and %s ~* '^\\\\W*$'
        """ % (self.clean_table, address_update_str, self.suburb, self.state, self.postcode)
        dtconfig.DB.query(update_query)
        
        address_update_str = ''
        for each_address in self.address_list:
            address_update_str += each_address + "~* '^[x ]*$' and "
        address_update_str = address_update_str[:-5]
        
        update_query = """
            update %s
            set mm_preclean = mm_preclean || '|invalid'
            where %s and %s ~* '^[x ]*$' and %s ~* '^[x ]*$' and %s ~* '^[x ]*$'
        """ % (self.clean_table, address_update_str, self.suburb, self.state, self.postcode)
        dtconfig.DB.query(update_query)
        
    def step11(self):
        myvars = dict(rtype='state')
        results = dtconfig.DB.select("find_and_replace", vars=myvars, where='rtype=$rtype', order="id")
        results = list(results)
        update_query = """
            update %s
            set %s = trim(regexp_replace(regexp_replace(%s, '%s', '%s', 'gi'),'\\\\s{2,}',' ','gi')), mm_preclean=mm_preclean||'|%s'
            where %s ~* '%s' and %s not in (select distinct state from pcdb)
        """
        
        for result in results:
            find_what = result.find_str
            replace_by = result.replace_str
            method = '%s_M%02d' % (result.rtype, result.id)
            print dtconfig.DB.query(update_query % (self.clean_table, self.state, self.state, find_what, replace_by, method, self.state, find_what, self.state))
            
    def step10(self):
        myvars = dict(rtype='suburb')
        results = dtconfig.DB.select("find_and_replace", vars=myvars, where='rtype=$rtype', order="id")
        results = list(results)
        update_query = """
            update %s
            set %s = trim(regexp_replace(regexp_replace(%s, '%s', '%s', 'gi'),'\\\\s{2,}',' ','gi')), mm_preclean=mm_preclean||'|%s'
            where %s ~* '%s'
        """
        
        for result in results:
            find_what = result.find_str
            replace_by = result.replace_str
            method = '%s_M%02d' % (result.rtype, result.id)
            print dtconfig.DB.query(update_query % (self.clean_table, self.suburb, self.suburb, find_what, replace_by, method, self.suburb, find_what))
                
    def step9(self):
        update_query = """
            update %s
            set %s = regexp_replace(%s,'^(.+)\\\\m(\\\\D+)([\\\\\\\\]+)$','\\\\1\\\\2','gi')
            where %s ~* '^(.+)\\\\m(\\\\D+)([\\\\\\\\])$'
        """
        
        for each_address in self.address_list:
            dtconfig.DB.query(update_query % (self.clean_table, each_address, each_address, each_address))
            
        dtconfig.DB.query(update_query % (self.clean_table, self.suburb, self.suburb, self.suburb))
        dtconfig.DB.query(update_query % (self.clean_table, self.state, self.state, self.state))
        
    def step8(self):
        query = """
            select *
            from %s
            where %s ~* '\\\\m(ALLEY|ALY|ALLY|ARCADE|ARC|AVENUE|AVE|BOULEVARD|BLVD|BVD|ROAD|RD|STREET|ST|STR|DRIVE|DR|DRV|CLOSE|CL|LANE|LN|MANOR|MNR|MEWS|PLACE|PL|ROW|TERRACE|TER|TCE|TRACE|TRCE|TRAIL|TRL|COURT|CRT|CR|CT|CIRCUS|CIR|CIRCUIT|CIRCLE|CIRC|CRESCENT|CRES|CRESC|LOOP|OVAL|QUADRANT|SQUARE|SQ|GROVE|GRV|PARKWAY|PKWY|RISE|ESPLANADE|ESP|PARADE|PDE|PROMENADE|PROM|WALK|HIGHWAY|HWY|WAY)$'
            and %s ~* '\\\\m(ALLEY|ALY|ALLY|ARCADE|ARC|AVENUE|AVE|BOULEVARD|BLVD|BVD|ROAD|RD|STREET|ST|STR|DRIVE|DR|DRV|CLOSE|CL|LANE|LN|MANOR|MNR|MEWS|PLACE|PL|ROW|TERRACE|TER|TCE|TRACE|TRCE|TRAIL|TRL|COURT|CRT|CR|CT|CIRCUS|CIR|CIRCUIT|CIRCLE|CIRC|CRESCENT|CRES|CRESC|LOOP|OVAL|QUADRANT|SQUARE|SQ|GROVE|GRV|PARKWAY|PKWY|RISE|ESPLANADE|ESP|PARADE|PDE|PROMENADE|PROM|WALK|HIGHWAY|HWY|WAY)$'
        """ 
        reversed_address_list = list(reversed(self.address_list))
        #first_address_line = reversed_address_list.pop()
        
        for i in range(len(reversed_address_list)):
            try:
                address1_field = reversed_address_list[i+1]
                address2_field = reversed_address_list[i]
            except IndexError:
                #last
                pass
            else:
                results = dtconfig.DB.query(query % (self.clean_table, address1_field, address2_field))
                for result in results:
                    address1 = result[address1_field]
                    address2 = result[address2_field]
                    mm_key = result['mm_key']
                    
                    (what_size, what_method) = compare_2_addresses(address1,address2)
                    if what_size == 1:
                        address1 = ''
                    elif what_size == 2:
                        address2 = ''
                    
                    if what_method != '':
                        update_query = r"""
                            update %s
                            set %s = '%s', %s = '%s', mm_preclean = mm_preclean||'|addresses=same=%s'
                            where mm_key = %s
                        """ % (self.clean_table, address1_field, address1.replace("'","''"), address2_field, address2.replace("'","''"), what_method, mm_key)
                        dtconfig.DB.query(update_query)
    def step7(self):
        query = r"""
            update %s
            set %s = '', mm_preclean = mm_preclean||'|addresses=same'
            where %s ilike '%s'||%s||'%s' and %s <>''
            and %s ~* '\\m(ALLEY|ALY|ALLY|ARCADE|ARC|AVENUE|AVE|BOULEVARD|BLVD|BVD|ROAD|RD|STREET|ST|STR|DRIVE|DR|DRV|CLOSE|CL|LANE|LN|MANOR|MNR|MEWS|PLACE|PL|ROW|TERRACE|TER|TCE|TRACE|TRCE|TRAIL|TRL|COURT|CRT|CR|CT|CIRCUS|CIR|CIRCUIT|CIRCLE|CIRC|CRESCENT|CRES|CRESC|LOOP|OVAL|QUADRANT|SQUARE|SQ|GROVE|GRV|PARKWAY|PKWY|RISE|ESPLANADE|ESP|PARADE|PDE|PROMENADE|PROM|WALK|HIGHWAY|HWY|WAY)$'
        """
        
        reversed_address_list = list(reversed(self.address_list))
        #first_address_line = reversed_address_list.pop()
        
        for i in range(len(reversed_address_list)-1):
            try:
                sibling_address_line = reversed_address_list[i+1]
            except IndexError:
                #last
                pass
            else:
                temp_query = query % (  self.clean_table
                                      , reversed_address_list[i]
                                      , sibling_address_line
                                      , chr(37)
                                      , reversed_address_list[i]
                                      , chr(37)
                                      , reversed_address_list[i]
                                      , reversed_address_list[i])
                #print temp_query
                dtconfig.DB.query(temp_query)
                
    def step6(self):
        query = r"""
            update %s
            set %s = %s || ' '||%s, %s = '', mm_preclean = mm_preclean || '|%s'
            where %s ~* '^(ALLEY|ALY|ALLY|ARCADE|ARC|AVENUE|AVE|BOULEVARD|BLVD|BVD|ROAD|RD|STREET|ST|STR|DRIVE|DR|DRV|CLOSE|CL|LANE|LN|MANOR|MNR|MEWS|PLACE|PL|ROW|TERRACE|TER|TCE|TRACE|TRCE|TRAIL|TRL|COURT|CT|CIRCUS|CIR|CIRCLE|CIRC|CRESCENT|CRES|CRESC|LOOP|OVAL|QUADRANT|SQUARE|SQ|GROVE|GRV|PARKWAY|PKWY|RISE|ESPLANADE|ESP|PARADE|PDE|PROMENADE|PROM|WALK|HIGHWAY|HWY|WAY|RETREAT)[.,]*$'
        """
        reversed_address_list = list(reversed(self.address_list))
        #first_address_line = reversed_address_list.pop()
        
        for i in range(len(reversed_address_list)):
            try:
                address1_field = reversed_address_list[i+1]
                address2_field = reversed_address_list[i]
            except IndexError:
                #last
                pass
            else:
                results = dtconfig.DB.query("""
                    select * 
                    from %s
                    where %s <> '' and %s <> ''
                """ % (self.clean_table, address2_field, address1_field))
                
                for result in results:
                    address1 = result[address1_field]                    
                    address2 = result[address2_field]
                    mm_key = result['mm_key']
                    if (re.search(r'[)]', address2, re.I) and not re.search(r'[(]', address2, re.I)
                        and re.search(r'[(]', address1, re.I) and not re.search(r'[)]', address1, re.I)):
                        #print address2, ' in ', address1
                        temp_bracket_index = address2.index(')')
                        new_address1 = address1 + ' ' + address2[:temp_bracket_index+1]
                        new_address2 = address2[temp_bracket_index+1:]
                        dtconfig.DB.query("""
                            update %s
                            set %s = '%s', %s = '%s', mm_preclean = mm_preclean||'|%s'
                            where mm_key = %d
                        """ % (self.clean_table, address1_field, new_address1.replace("'","''"), address2_field, new_address2.replace("'","''"), 'bracket', mm_key))
                
    def step5(self):
        query = r"""
            update %s
            set %s = %s || ' '||%s, %s = '', mm_preclean = mm_preclean || '|%s'
            where %s ~* '^(ALLEY|ALY|ALLY|ARCADE|ARC|AVENUE|AVE|BOULEVARD|BLVD|BVD|ROAD|RD|STREET|ST|STR|DRIVE|DR|DRV|CLOSE|CL|LANE|LN|MANOR|MNR|MEWS|PLACE|PL|ROW|TERRACE|TER|TCE|TRACE|TRCE|TRAIL|TRL|COURT|CRT|CR|CT|CIRCUS|CIR|CIRCUIT|CIRCLE|CIRC|CRESCENT|CRES|CRESC|LOOP|OVAL|QUADRANT|SQUARE|SQ|GROVE|GRV|PARKWAY|PKWY|RISE|ESPLANADE|ESP|PARADE|PDE|PROMENADE|PROM|WALK|HIGHWAY|HWY|WAY)[.,]*$'
        """
        reversed_address_list = list(reversed(self.address_list))
        #first_address_line = reversed_address_list.pop()
        
        for i in range(len(reversed_address_list)-1):
            try:
                sibling_address_line = reversed_address_list[i+1]
            except AttributeError:
                #last
                pass
            else:
                temp_query = query % (  self.clean_table
                                      , sibling_address_line
                                      , sibling_address_line
                                      , reversed_address_list[i]
                                      , reversed_address_list[i]
                                      , 'move_street_type'
                                      , reversed_address_list[i])
                dtconfig.DB.query(temp_query)
    
    def step4(self):
       
        reversed_address_list = list(reversed(self.address_list))
        #first_address_line = reversed_address_list.pop()
        
        for i in range(len(reversed_address_list)):
            try:
                address1_field = reversed_address_list[i+1]
                address2_field = reversed_address_list[i]
                #print address1_field
                #print address2_field
            except IndexError:
                #that where we need to check first address is a number
                #address2_field is first address line
                #if it is a number only
                address1_field = reversed_address_list[i]
                address2_field = reversed_address_list[i-1]
                
                if address1_field != address2_field:
                    results = dtconfig.DB.query("""
                        select * 
                        from %s
                        where %s <> '' and %s <> ''
                    """ % (self.clean_table, address2_field, address1_field))
                    
                    for result in results:
                        address1 = result[address1_field]                    
                        address2 = result[address2_field]
                        mm_key = result['mm_key']
                        if re.match(r'^(U[nit ]*|S[uite ]*|F[lat]*)*[0-9 /-]+[a-z]?$', address1, re.I):
                            new_address1 = address1+' '+address2
                            new_address2 = ''
                            dtconfig.DB.query("""
                                update %s
                                set %s = '%s', %s = '%s', mm_preclean = mm_preclean||'|%s'
                                where mm_key = %d
                            """ % (self.clean_table, address1_field, new_address1.replace("'","''"), address2_field.replace("'","''"), new_address2, 'merge_address', mm_key))
            else:
                do_again = True
                while do_again:
                    do_again = False
                    results = dtconfig.DB.query("""
                        select * 
                        from %s
                        where %s <> '' and %s <> ''
                    """ % (self.clean_table, address2_field, address1_field))
                    
                    for result in results:
                        address1 = result[address1_field].strip()                  
                        address2 = result[address2_field].strip()
                        mm_key = result['mm_key']
                        
                        #if address2 is a number
                        if re.match(r'^\d+$', address2, re.I):
                            if re.match(r'^(.+?)box[ ,.]*$', address1, re.I): 
                                #print address1+' '+address2
                                dtconfig.DB.query("""
                                    update %s
                                    set %s = '%s', %s = '%s', mm_preclean = mm_preclean||'|%s'
                                    where mm_key = %d
                                """ % (self.clean_table, address1_field, (address1+' '+address2).replace("'","''"), address2_field, '', 'is_pdn', mm_key))
                                
                            elif re.search(r'box\s*%s' % address2, address1, re.I):
                                #print address2, ' in ', address1
                                dtconfig.DB.query("""
                                    update %s
                                    set %s = '%s', mm_preclean = mm_preclean||'|%s'
                                    where mm_key = %d
                                """ % (self.clean_table, address2_field, '', 'is_pdn', mm_key))
                        else:
                            pass
                            #word2_list = re.split('\\s+',address2)
                            #word2_list = map(lambda x: str(x), word2_list)
                            #word1_list = re.split('\\s+',address1)
                            #word1_list = map(lambda x: str(x), word1_list)
                            #word2 = word2_list.pop(0)
                            #
                            #word1 = word1_list.pop()
                            #if not is_a_meaningful_word(re.sub(r'[%s]+' % RAW_WHITE_SPACE,'',word1)) and not is_a_meaningful_word(re.sub(r'[%s]+' % RAW_WHITE_SPACE,'',word2)):
                            ##if not re.search('[0-9]+', word1, re.I) and not re.search('[0-9]+', word2, re.I):
                            #    a_word = word1+word2
                            #    a_word = re.sub(r'[%s]+' % RAW_WHITE_SPACE,'',a_word)
                            #    if is_a_meaningful_word(a_word):
                            #    #if (is_a_meaningful_word(a_word) or is_in_mydict(a_word) 
                            #    #   or is_a_suburb(a_word) or is_world_city(a_word)):
                            #        do_again = True
                            #        word1_list.append(word1+word2)
                            #        new_address1= ' '.join(word1_list)
                            #        new_address2= ' '.join(word2_list)
                            #        dtconfig.DB.query("""
                            #            update %s
                            #            set %s = '%s', %s = '%s', mm_preclean = mm_preclean||'|%s'
                            #            where mm_key = %d
                            #        """ % (self.clean_table, address1_field, new_address1.replace("'","''"), address2_field.replace("'","''"), new_address2, 'is_a_word', mm_key))
    def step3(self):
        myvars = dict(rtype='spelling')
        results = dtconfig.DB.select("find_and_replace", vars=myvars, where='rtype=$rtype', order="id")
        results = list(results)
        update_query = """
            update %s
            set %s = regexp_replace(%s, '%s', '%s', 'gi'), mm_preclean='%s'
            where %s ~* '%s'
        """
        for each_address in self.address_list:
            for result in results:
                find_what = result.find_str
                replace_by = result.replace_str
                method = '%s_M%02d' % (result.rtype, result.id)
                print update_query % (self.clean_table, each_address, each_address, find_what, replace_by, method, each_address, find_what)
                print dtconfig.DB.query(update_query % (self.clean_table, each_address, each_address, find_what, replace_by, method, each_address, find_what))
                
    def step2(self):
        myvars = dict(rtype='Address')
        results = dtconfig.DB.select("find_and_replace", vars=myvars, where='rtype=$rtype and id = 10', order="id")
        results = list(results)
        update_query = """
            update %s
            set %s = '%s', mm_preclean=mm_preclean||'|%s'
            where mm_key = %d
        """
        
        select_query = """
            select mm_key, %s
            , regexp_replace(%s,'%s','\\\\1','gi') as arg1
            , regexp_replace(%s,'%s','\\\\2','gi') as arg2
            , regexp_replace(%s,'%s','\\\\3','gi') as arg3
            , regexp_replace(%s,'%s','\\\\4','gi') as arg4
            , regexp_replace(%s,'%s','\\\\5','gi') as arg5
            , regexp_replace(%s,'%s','\\\\6','gi') as arg6
            from %s
            where %s ~* '%s' and (%s = '' or %s ~* '^Aust')
        """
        for each_address in self.address_list:
            for result in results:
                find_what = result.find_str
                replace_by = result.replace_str
                method = '%s_M%02d' % (result.rtype, result.id)
                results_1 = dtconfig.DB.query(select_query % ( each_address
                                                              ,each_address
                                                              ,find_what
                                                              ,each_address
                                                              ,find_what
                                                              ,each_address
                                                              ,find_what
                                                              ,each_address
                                                              ,find_what
                                                              ,each_address
                                                              ,find_what
                                                              ,each_address
                                                              ,find_what
                                                              ,self.clean_table
                                                              ,each_address
                                                              ,find_what
                                                              ,self.country
                                                              ,self.country))
                for result_1 in results_1:
                    mm_key = result_1.mm_key
                    could_be_street_name = result_1.arg3+result_1.arg4
                    
                    if is_a_meaningful_word(could_be_street_name):
                        #update different
                        new_address = result_1.arg1+result_1.arg2+' '+result_1.arg3+result_1.arg4+' '+result_1.arg5+result_1.arg6
                        mm_preclean = 'Street_Num_Prefix_1'
                    else:
                        new_address = result_1.arg1+result_1.arg2+result_1.arg3+' '+result_1.arg4+' '+result_1.arg5+result_1.arg6
                        mm_preclean = 'Street_Num_Prefix_2'
                        
                    dtconfig.DB.query(update_query % (self.clean_table, each_address, new_address.replace("'","''"), mm_preclean, mm_key))
                    
    def step1(self):
        myvars = dict(rtype='PO Box')
        results = dtconfig.DB.select("find_and_replace", vars=myvars, where='rtype=$rtype', order="id")
        results = list(results)
        update_query = """
            update %s
            set %s = regexp_replace(%s, '%s', '%s', 'gi'), mm_preclean='%s'
            where %s ~* '%s'
        """
        for each_address in self.address_list:
            for result in results:
                find_what = result.find_str
                replace_by = result.replace_str
                method = '%s_M%02d' % (result.rtype, result.id)
                print dtconfig.DB.query(update_query % (self.clean_table, each_address, each_address, find_what, replace_by, method, each_address, find_what))
                
    def step0(self):
        update_query = """
            update %s
            set %s = '', mm_preclean='%s'
            where %s ~* '^\\\\W+$'
        """
        
        update_query_1 = """
            update %s
            set %s = '', mm_preclean = mm_preclean || '|%s'
            where upper(%s) = 'NONE' or upper(%s) = 'N/A' or upper(%s) = 'TBA'
        """
        
        for each_address in self.address_list:
            dtconfig.DB.query(update_query % (self.clean_table, each_address, 'whitespace', each_address))
            dtconfig.DB.query(update_query_1 % (self.clean_table, each_address, 'whitespace', each_address, each_address, each_address))
                                
    def create_cleaned_table(self):
        create_query = """
            drop table if exists %s;
            
            select *, ''::text as mm_preclean
            into %s
            from %s;
            
        """ % (self.clean_table, self.clean_table, self.src_table)
        
        dtconfig.DB.query(create_query)
        
if __name__ == '__main__':

    #app = Clean('lu_saddle',"address,address2","city","state","postcode","country")
    #app = Clean('lu_blue',"address_1,address_2","address_3","address_4","postcode","country")
    app = Clean('lu_openuni',"address1","suburb_","state_","postcode_","country")
    app.clean()
    
    
    