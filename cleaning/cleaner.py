__author__ = 'luan'


import re
from fuzzywuzzy import process
from fuzzywuzzy import fuzz
from dpid import paflinkr

import time
import decor
import helper
import cStringIO


try:
    import logger
    log = logger.getlogger()
except:
    import logging
    log = logging.getlogger()


# SPECIAL REGEX MODULE

lock = None

r_lookup = None


def check_dpid(f):
    """
    Validate  state, and postcode against auspost, big chance it is a good record
    """
    def wrapped_f(*args):

        addresses, suburb, state, postcode, country, mm_preclean, mm_note, mm_clean_type = f(*args)

        # if mm_preclean != 'SuStP':
        #     # check state, and postcode against australia post database
        #     a = {
        #         'state': state,
        #         'postcode': postcode
        #     }
        #     results = helper.tb.find(a)
        #     if results.count() > 0:
        #         # why suburb was not matched before --> via, mt, typo, east, north, south, west, empty, street
        #         '''
        #         "COTSWELL HILL, TOOWOOMBA"
        #         "YAKANDANDAH,"
        #         "WOORAGEE VIC"
        #         '''
        #         mm_preclean = 'StP'
        #         # now, trying to fill correct state
        #         _suburb = ''
        #         if mm_clean_type == '<DPID>':
        #             _suburb = helper.m_parser.getMeThis('CLC')
        #             mm_note += '<Used parsed info>'
        #         #else:
        #             #street_name = helper.m_parser.getMeThis('THN').replace(' ', '')[:6]
        #             #log.info(helper.m_parser.getMeThis('PDT'))
        #             #street_type = helper.m_parser.getMeThis('THT')
        #             #street_number = helper.m_parser.getMeThis('TN1')
        #             #lookup_results = r_lookup.run(postcode, street_name)
        #
        #         # Once you have correct suburb, match against street, to remove suburb in street
        #         if _suburb:
        #             suburb = _suburb
        if mm_clean_type == '<DPID>':
            addresses, suburb, state, postcode, country, mm_preclean, mm_note, mm_clean_type = \
                cleaning_dpid.validate_record(addresses, suburb, state, postcode, country,
                                              mm_preclean, mm_note, mm_clean_type)

        return addresses, suburb, state, postcode, country, mm_preclean, mm_note, mm_clean_type
    return wrapped_f




def check_street_in_ssp(f):
    def wrapped_f(*args):

        addresses, suburb, state, postcode, country, mm_preclean, mm_note, mm_clean_type = f(*args)
        _address, _suburb = helper.check_street_in_text(suburb)
        if _address:
            if not helper.is_suburb_in_pcdb(_address):
                addresses[-1] = "{0} {1}".format(addresses[-1], _address).replace('  ', ' ').strip()
                suburb = _suburb
                mm_note += '<str_in_ssp_1>'
        return addresses, suburb, state, postcode, country, mm_preclean, mm_note, mm_clean_type
    return wrapped_f

def check_pobox_in_ssp(f):
    def wrapped_f(*args):

        addresses, suburb, state, postcode, country, mm_preclean, mm_note, mm_clean_type = f(*args)
        _address, _suburb = helper.check_pobox_in_text(suburb)
        if _address:
            if not helper.is_suburb_in_pcdb(_address):
                addresses[-1] = "{0} {1}".format(addresses[-1], _address).replace('  ', ' ').strip()
                suburb = _suburb
                mm_note += '<str_in_ssp_2>'
        return addresses, suburb, state, postcode, country, mm_preclean, mm_note, mm_clean_type
    return wrapped_f



@decor.dpid_address_last
@decor.fill_ssp_fuzzy
@decor.validate_suburb_state_postcode_fuzzy
@decor.fill_suburb
@decor.fill_postcode
@decor.fill_state
@decor.pre_check_ssp_in_address
@decor.split_ssp
@decor.check_street_in_ssp
@decor.pre_check_ssp
@decor.dpid_address
def validate_record(addresses, suburb, state, postcode, country, mm_preclean, mm_note, mm_clean_type):
    return addresses, suburb, state, postcode, country, mm_preclean, mm_note, mm_clean_type


def clean(line):

    fields = line[:-1].split('\t')
    mm_table_type = fields.pop()
    mm_clean_type = fields.pop()
    mm_note = fields.pop()
    mm_preclean = fields.pop()
    country = fields.pop()
    postcode = fields.pop()
    state = fields.pop()
    suburb = fields.pop()
    mm_key = fields.pop(0)
    addresses = fields
    mm_table_type = 'NEW'
    log.info("Cleaning == mm_key={0}".format(mm_key))

    addresses, suburb, state, postcode, country, mm_preclean, mm_note, mm_clean_type, parsed_result = \
                                                        validate_record(addresses, suburb, state, postcode, country,
                                                                        mm_preclean, mm_note, mm_clean_type)

    return '{0}\t{1}\t{2}\t{3}\t{4}\t{5}\t{6}\t{7}\t{8}\t{9}\n'.format(mm_key, '\t'.join(addresses), suburb,\
                                                                        state, postcode, country, mm_preclean,\
                                                                        mm_note, mm_clean_type, mm_table_type)


# def clean_thread(self, i):
    #
    #     while True:
    #         #log.info('%s: Looking for the next enclosure' % i)
    #         line = self.inqueue.get()
    #         log.info("{0}.Cleaning == mm_key={1}".format(i, line))
    #
    #         fields = line[:-1].split('\t')
    #         mm_table_type = fields.pop()
    #         mm_clean_type = fields.pop()
    #         mm_note = fields.pop()
    #         mm_preclean = fields.pop()
    #         country = fields.pop()
    #         postcode = fields.pop()
    #         state = fields.pop()
    #         suburb = fields.pop()
    #         mm_key = fields.pop(0)
    #         addresses = fields
    #         mm_table_type = 'NEW'
    #
    #
    #         addresses, suburb, state, postcode, country, mm_preclean, mm_note, mm_clean_type, parsed_result = \
    #                                                             cleaner.validate_record(addresses, suburb, state, postcode, country,
    #                                                                             mm_preclean, mm_note, mm_clean_type)
    #
    #         self.in_buffer.write('{0}\t{1}\t{2}\t{3}\t{4}\t{5}\t{6}\t{7}\t{8}\t{9}\n'.format(mm_key, '\t'.join(addresses), suburb,\
    #                                                                             state, postcode, country, mm_preclean,\
    #                                                                             mm_note, mm_clean_type, mm_table_type))
    #         self.inqueue.task_done()