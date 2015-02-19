#!/usr/bin/env python
import re
from fuzzywuzzy import process
from fuzzywuzzy import fuzz
import helper
import decor
import difflib

try:
    import logger
    log = logger.getlogger()
except:
    import logging
    log = logging.getlogger()


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


def update_suburb(f):
    """
    Validate suburb, state, and postcode against auspost, big chance it is a good record
    """
    def wrapped_f(*args):

        addresses, suburb, state, postcode, country, mm_preclean, mm_note, mm_clean_type = f(*args)

        if '<SuStP>' not in mm_preclean:
            _suburb = helper.m_parser.getMeThis('CLC')
            # find suburb in address
            #for address in reversed(addresses):
            # for i in xrange(len(addresses) - 1, -1, -1):
            #     address = addresses[i]
            #     if helper.is_ssp_in_pcdb(address, state, postcode):
            #         if not suburb:
            #             suburb = address
            #             addresses[i] = ''

            # compare the correct suburb with existing suburb


        return addresses, suburb, state, postcode, country, mm_preclean, mm_note, mm_clean_type

    return wrapped_f

def update_state_postcode(f):
    """
    Validate suburb, state, and postcode against auspost, big chance it is a good record
    """
    def wrapped_f(*args):

        addresses, suburb, state, postcode, country, mm_preclean, mm_note, mm_clean_type = f(*args)

        if '<SuStP>' not in mm_preclean:
            _state = helper.m_parser.getMeThis('STT')
            if not helper.is_state_in_pcdb(state) or _state != state:
                mm_note += '<update st from [{0}]>'.format(state)
                state = _state

            _postcode = helper.m_parser.getMeThis('CPC')
            if not helper.is_postcode_in_pcdb(postcode) or _postcode != postcode:
                mm_note += '<update pc from [{0}]>'.format(postcode)
                postcode = _postcode

        return addresses, suburb, state, postcode, country, mm_preclean, mm_note, mm_clean_type

    return wrapped_f

# @decor.validate_suburb_state_postcode
# @update_suburb
# @decor.validate_suburb_state_postcode
# @update_state_postcode
def validate_record(addresses, suburb, state, postcode, country, mm_preclean, mm_note, mm_clean_type):
    mm_preclean += '<@DPID>'
    return addresses, suburb, state, postcode, country, mm_preclean, mm_note, mm_clean_type
