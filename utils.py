# -*- coding: utf-8 -*-
import string
from string import maketrans
import config
import db
import re
import datetime

try:
    import logger
    log = logger.getlogger()
except:
    import logging
    log = logging.getlogger()


def lm_simplify(idx, txt):
    """Replace special characters, or postgresql keyworks
        and return new string"""

    #--------------------------------
    # DEFAULT: lowercase
    #--------------------------------
    txt = txt.lower()

    #--------------------------------
    # REMOVE LEFT SPACE & WHITE SPACE
    #--------------------------------
    #txt = txt.lstrip() #skip this step because matching with old system
    #txt = txt.rstrip()

    #---------------------------------
    # REMOVE WHITE SPACE & PUNCTUATION
    #---------------------------------
    intab  = "- \n+"
    outtab = "____"
    trantab = maketrans(intab, outtab)
    result = txt.translate(trantab, "!#$%&'*,./:;<=>?@[]^`(){|}~'")

    #trantab = maketrans(" ", "_")
    #result = result.translate(trantab)
    if not result:
        result = 'unknown_%d' % idx
    else:
        #---------------------------------------------------------
        # APPEND _ AT THE BEGINNING IF FIRST CHARACTER IS A NUMBER
        #---------------------------------------------------------
        try:
            int(result[0])
            result = '_' + result
        except ValueError:
            pass
    #----------------------------
    # REPLACE POSTGRESQL KEYWORKS
    #----------------------------
    if result.upper()+'\n' in config.keyworks:
        result = 'kw_' + result

    return result


def remove_duplicate_fields(fields):
    """Check duplicate field in header and
    replace with new field name if dup is found

    Arguments:
    fields -- array of string -- header fields

    """
    _fields = set(fields)

    if len(_fields) == len(fields):
        return fields

    for field in _fields:
        if fields.count(field) == 1:
            continue
        indices = [i for i, x in enumerate(fields) if x == field]
        indices.pop(0)

        for indx in indices:
            fields[indx] = fields[indx] + '_' + str(indx)

def remove_escape_char(field_data):
    """Remove Escape Character \ and return new string

    Arguments:
    line -- string -- field data

    """
    # remove hard return for excel
    field_data = field_data.replace("\r", "|")
    field_data = field_data.replace("\n", "|")
    field_data = field_data.replace("\t", "|")
    field_data = field_data.replace("||", "|")
    while field_data.endswith('\\'):
        field_data = field_data[:-1]
    else:
        field_data = field_data.replace("\\", "\\\\")
    return field_data


def mm_translate(encoded_string, environment_vars=None):
    """Decode encoded_string using key-value defined
    in environment_vars dictionary

    Arguments:
    encoded_string -- string
    environment_vars -- list or integer

    """
    if encoded_string is None:
        return ''

    if environment_vars is None:
        return encoded_string

    #if environment_vars is not None and \
    #        isinstance(environment_vars, int):
    #    environment_vars = dtconfig.DB.query("""
    #                        select a.key_value from vars_tasks a
    #                        inner join tasks b on a.jobid = b.jobid
    #                        where b.id=%d
    #                     """ % environment_vars)

    dt_obj = datetime.datetime.now()
    all_vars = re.findall(r'([%][dmyY]|[%][{][d][+-]\d+[}])', encoded_string)
    new_all_vars = []
    for each_var in all_vars:
        temp_obj = re.match(r'([%])[{]([d])([+-]\d+)[}]', each_var)
        if temp_obj:
            each_var = temp_obj.group(1)+temp_obj.group(2)

            if temp_obj.group(2) == 'd':
                offset_delta = datetime.timedelta(days=int(temp_obj.group(3)))
                dt_obj = dt_obj + offset_delta
        new_all_vars.append(each_var)

    for idx, each_var in enumerate(all_vars):
        encoded_string = encoded_string.replace(each_var, dt_obj.strftime(new_all_vars[idx]))

    if environment_vars:
        try:
            temp_str = environment_vars[0].key_value
        except AttributeError, e:
            temp_str = environment_vars[0]['key_value']
        if temp_str.find('\r\n') > -1:
            key_value_raw = (temp_str).split('\r\n')
        else:
            key_value_raw = (temp_str).split('\n')

        for each_key_value in key_value_raw:
            var_key, var_value = re.split('=', each_key_value, 1)
            if each_key_value.startswith('#'):
                continue
            encoded_string = encoded_string.replace('${%s}' % var_key.strip(), var_value)

    return encoded_string