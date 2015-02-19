#!/usr/bin/env python
# -*- coding: utf-8 -*-

__version__ = 1.0

import web
import sys
#sys.path.append(r'Z:\melmailing\_lib')
sys.path.append(r'D:\0_works\pyhon_projects\_lib')
from myutils import mmutils
from database import database
import dtconfig
import os
import time
import transform_temp 
import re


SMALL = 'a|an|and|as|at|but|by|en|for|if|in|of|on|or|the|to|v\.?|via|vs\.?'
PUNCT = "[!\"#$%&'‘()*+,-./:;?@[\\\\\\]_`{|}~]"

class Casing(object):
    def __init__(self, taskid):
        self.taskid = taskid
    
    def run(self):
        myvars = dict(taskid = self.taskid)
        try:
            t0 = time.time()
            count = dtconfig.DB.update('tasks', where='id = $taskid', vars = myvars, when_start = dtconfig.GET_NOW_CLASS("NOW()"), error=None, status='processing')
            time.sleep(10)
            results = dtconfig.DB.select('titlecase_tasks', where="taskid = $taskid", vars = myvars)
            result = results[0]
            
            src_table = result.src_table
            address = result.address
            name = result.name
            company = result.company
            position = result.position
            
            address_list = []
            name_list = []
            company_list = []
            position_list = []
            
            if address != None and address != '':
                address_list = address.split(',')
            if name != None and name != '':
                name_list = name.split(',')
            if company != None and company != '':
                company_list = company.split(',')
            if position != None and position != '':
                position_list = position.split(',')
            
            results = dtconfig.DB.select(src_table)
            
            update_query = """
                update %s
                set """ % src_table
            
            for each_field in address_list:
                update_query += each_field +"= '%s',"
            for each_field in name_list:
                update_query += each_field +"= '%s',"
            
            for each_field in company_list:
                update_query += each_field +"= '%s',"
            
            for each_field in position_list:
                update_query += each_field +"= '%s',"
                
            update_query = update_query[:-1] + " where mm_key = %d"
            
            print update_query
            for result in results:
                mm_key = result['mm_key']
                address_data = []
                name_data = []
                company_data = []
                position_data = []
                for each_field in address_list:
                    temp_data =  transform_temp.titlecase(result[each_field],'ADDRESS')
                    temp_data = temp_data.replace("'","''")
                    address_data.append(temp_data)
                for each_field in name_list:
                    temp_data =  transform_temp.titlecase(result[each_field],'ADDRESS')
                    temp_data = temp_data.replace("'","''")
                    name_data.append(temp_data)
                for each_field in company_list:
                    temp_data =  transform_temp.titlecase(result[each_field],'COMPANY')
                    temp_data = temp_data.replace("'","''")
                    company_data.append(temp_data)
                for each_field in position_list:
                    temp_data =  transform_temp.titlecase(result[each_field],'ADDRESS')
                    temp_data = temp_data.replace("'","''")
                    position_data.append(temp_data)
                    
                final_tuple = tuple(address_data) + tuple(name_data) + tuple(company_data) + tuple(position_data) + (mm_key,)
                
                dtconfig.DB.query(update_query % final_tuple)
                
                #run update_query
            
            duration = int(time.time()-t0)
            
            #update duration into tables
            count = dtconfig.DB.update('tasks', where='id = $taskid', vars = myvars, duration = duration, status='done')
            job_status = 0
        except:
            print  sys.exc_info()[0]
            print  str(sys.exc_info()[1])
            count = dtconfig.DB.update('tasks', where='id = $taskid', vars = myvars, error = str(sys.exc_info()[1]), status='error')
            job_status = 1
        
        return job_status

if __name__ == '__main__':
    app = Casing(106)
    app.run()
    
    