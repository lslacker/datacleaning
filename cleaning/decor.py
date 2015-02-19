__author__ = 'luan'
import helper
import re
import datetime
from fuzzywuzzy import process
from fuzzywuzzy import fuzz
import sys


try:
    import logger
    log = logger.getlogger()
except:
    import logging
    log = logging.getlogger()

r_lookup = None

def validate_suburb_state_postcode(f):
    """
    Validate suburb, state, and postcode against auspost, big chance it is a good record
    """
    def wrapped_f(*args):

        addresses, suburb, state, postcode, country, mm_preclean, mm_note, mm_clean_type, parsed_result = f(*args)
        suburb = suburb.strip(',')
        state = state.strip(',')

        if '<SuStP>' not in mm_preclean and not country:
            # check suburb, state, and postcode against australia post database
            # remove comma, . in suburb, check via
            suburbs = helper.give_me_suburbs(suburb)

            for _suburb in suburbs:
                if helper.is_ssp_in_pcdb(_suburb, state, postcode):
                    mm_preclean += '<SuStP>'
                    break

        return addresses, suburb, state, postcode, country, mm_preclean, mm_note, mm_clean_type, parsed_result
    return wrapped_f


NON_WORD_EXP = re.compile(r'^\W*$')
SSP_EXP = re.compile(r'^(.+)\s*\b(VIC|NSW|QLD|TAS|NSW|ACT|SA|WA|NT)\b\s*(\d{3,4})')



def dpid_address(f):
    """
    If address is valid
    """

    @validate_suburb_state_postcode
    def wrapped_f(*args):


        addresses, suburb, state, postcode, country, mm_preclean, mm_note, mm_clean_type = f(*args)

        address = '{0} {1} {2} {3} {4}'.format(' '.join(addresses), suburb, state, postcode, country)
        #cleaning.lock.acquire()
        if helper.is_address_good(address):
            mm_clean_type += '<DPID>'
        else:
            mm_clean_type += '<nonDPID>'

        parsed_result = helper.m_parser.result.copy()

        #cleaning.lock.release()
        return addresses, suburb, state, postcode, country, mm_preclean, mm_note, mm_clean_type, parsed_result

    return wrapped_f

def split_ssp(f):
    """
    if suburb, state, and postcode are blank,
    assume address hold suburb, state, and postcode
    """
    @validate_suburb_state_postcode
    def wrapped_f(*args):

        addresses, suburb, state, postcode, country, mm_preclean, mm_note, mm_clean_type, parsed_result = f(*args)
        # have to remove '<SuStP>' not in mm_preclean as it could contain VIC even if it contains SuStP
        if not country:
            # suburb, state, postcode are all blank
            if NON_WORD_EXP.match(suburb)\
                and NON_WORD_EXP.match(state)\
                and NON_WORD_EXP.match(postcode):

                for i in range(-1, -len(addresses), -1):
                    if not NON_WORD_EXP.match(addresses[i]):
                        suburb, state, postcode = helper.split_suburb_state_postcode(addresses[i])
                        if suburb == addresses[i]:
                            pass
                        else:
                            addresses[i] = ''
                        break
            else:

                # suburb may contains either state or postcode info
                # eventhough state and postcode are not empty
                if not NON_WORD_EXP.match(suburb):
                    _suburb, _state, _postcode = helper.split_suburb_state_postcode(suburb)
                    log.info(_suburb)
                    if _suburb != suburb:
                        suburb = _suburb

                        if _state:
                            # I believe state from suburb if any is more accurate
                            state = _state

                        if _postcode:
                            # I believe postcode from suburb if any is more accurate
                            postcode = _postcode

        # check ssp in address here

        return addresses, suburb, state, postcode, country, mm_preclean, mm_note, mm_clean_type, parsed_result
    return wrapped_f


def pre_check_ssp(f):
    @validate_suburb_state_postcode
    def wrapped_f(*args):

        addresses, suburb, state, postcode, country, mm_preclean, mm_note, mm_clean_type, parsed_result = f(*args)

        if '<SuStP>' not in mm_preclean and not country:
            # if state is not state
            if not helper.is_state_in_pcdb(state):
                _state = helper.rename_split_state(state)
                if helper.is_state_in_pcdb(_state):
                    state = _state
                    mm_note += '<format state>'

            if not helper.is_suburb_in_pcdb(suburb):
                suburb = helper.rename_split_suburb(suburb)
                #mm_note += '<format suburb>'

            if not helper.is_postcode_in_pcdb(postcode):
                if state == 'NT' and postcode.startswith('8') and len(postcode) == 3:
                    postcode = '0{0}'.format(postcode)
                    mm_note += '<add 0 to postcode>'



        return addresses, suburb, state, postcode, country, mm_preclean, mm_note, mm_clean_type, parsed_result
    return wrapped_f

def check_street_in_ssp(f):

    @validate_suburb_state_postcode
    def wrapped_f(*args):

        addresses, suburb, state, postcode, country, mm_preclean, mm_note, mm_clean_type, parsed_result = f(*args)

        if '<SuStP>' not in mm_preclean and not country:
            # if address in suburb
            _addresses, _suburb = helper.check_street_in_text(suburb)

            if (_addresses
                    and not helper.is_suburb_in_pcdb(_addresses)
                    and 'KILDA' not in _suburb
                    and 'MARYS' not in _suburb
                    and len(_suburb) <= 2
               ):

                log.info(_addresses)
                if addresses[-1]:
                    addresses[-1] += ', {0}'.format(_addresses)
                else:
                    addresses[-1] = _addresses
                suburb = _suburb
                mm_note += '<street in suburb>'
            else:
                _addresses, _suburb = helper.check_pobox_in_text(suburb)
                if _addresses:
                    if addresses[-1]:
                        addresses[-1] += ', {0}'.format(_addresses)
                    else:
                        addresses[-1] = _addresses
                    suburb = _suburb
                    mm_note += '<pobox in suburb>'

            # # if address in state
            # _addresses, _state = helper.check_street_in_text(state)
            # if _addresses:
            #     if addresses[-1]:
            #         addresses[-1] += ', {0}'.format(_addresses)
            #     else:
            #         addresses[-1] = _addresses
            #     state = _state
            #     mm_note += '<address in state>'
            # else:
            #     _addresses, _state = helper.check_pobox_in_text(state)
            #     if addresses[-1]:
            #         addresses[-1] += ', {0}'.format(_addresses)
            #     else:
            #         addresses[-1] = _addresses
            #     state = _state
            #     mm_note += '<address in state>'
            # # if address in postcode
            # _addresses, _postcode = helper.check_street_in_text(postcode)
            # if _addresses:
            #     if addresses[-1]:
            #         addresses[-1] += ', {0}'.format(_addresses)
            #     else:
            #         addresses[-1] = _addresses
            #     postcode = _postcode
            #     mm_note += '<address in postcode>'
            # else:
            #     _addresses, _postcode = helper.check_pobox_in_text(postcode)
            #     if addresses[-1]:
            #         addresses[-1] += ', {0}'.format(_addresses)
            #     else:
            #         addresses[-1] = _addresses
            #     postcode = _postcode
            #     mm_note += '<address in postcode>'
        return addresses, suburb, state, postcode, country, mm_preclean, mm_note, mm_clean_type, parsed_result
    return wrapped_f

def pre_check_ssp_in_address(f):
    @validate_suburb_state_postcode
    def wrapped_f(*args):
        addresses, suburb, state, postcode, country, mm_preclean, mm_note, mm_clean_type, parsed_result = f(*args)
        if '<SuStP>' not in mm_preclean and not country:
            i = len(addresses) - 1
            while i >= 0:
                address = addresses[i].upper()

                if address:
                    # address contains suburb
                    if helper.is_ssp_in_pcdb_fuzzy(address, state, postcode):
                        break

                    # if is_good:
                    #     # make sure left over is not address or po box
                    #     log.info(helper.check_street_in_text(left_over))
                    #
                    #     break
                # address is suburb + postcode
                i -= 1

            # found a suburb in address, now just check info
            #   after address
            if i > -1:
                a = [x for x in addresses[i+1:] if not NON_WORD_EXP.match(x)]

                should_update = True
                if a:
                    #number --> possibly postcode
                    #or suburb state postcode
                    #or state, full state
                    #or ...
                    if len(a) == 1:
                        either_ssp = a[0]
                        # suburb, state, postcode ---> suburb is university (normally???) e.g monash uni clayton vic 3800...
                        _suburb, _state, _postcode = helper.split_suburb_state_postcode(either_ssp)
                        # postcode
                        if helper.is_postcode_in_pcdb(either_ssp):
                            postcode = either_ssp
                            idx = addresses.index(either_ssp)
                            addresses[idx] = ''
                            mm_note += "<{0} is a postcode in address line {1}>".format(either_ssp, idx)
                        # state
                        elif either_ssp.upper() in helper.states:
                            state = helper.states[either_ssp.upper()]
                            idx = addresses.index(either_ssp)
                            addresses[idx] = ''
                            mm_note += "<{0} is a state in address line {1}>".format(either_ssp, idx)
                        # state
                        elif helper.is_state_in_pcdb(either_ssp):
                            state = either_ssp
                            idx = addresses.index(either_ssp)
                            addresses[idx] = ''
                            mm_note += "<{0} is a state in address line {1}>".format(either_ssp, idx)
                        #suburb
                        elif helper.is_suburb_in_pcdb_fuzzy(either_ssp):
                            idx = addresses.index(either_ssp)
                            addresses[idx] = ''
                            mm_note += "<{0} is a suburb in address line {1}, but dont use>".format(either_ssp, idx)
                        # ssp
                        elif _suburb != either_ssp:
                                if _state:
                                    state = _state
                                if _postcode:
                                    postcode = _postcode
                                suburb = _suburb
                                idx = addresses.index(either_ssp)
                                addresses[idx] = ''
                                mm_note += "<{0} is a ssp in address line {1}>".format(either_ssp, idx)
                                should_update = False
                        else:
                            # if contain road street, ...
                            # -> that means 2 addresses, right????
                            should_update = False
                            log.info(a)

                if helper.is_ssp_in_pcdb_fuzzy(suburb, state, postcode):
                    _suburb = addresses[i]
                    #compare ---> if same, update, if not dont update
                    # domain road and south yarra have same postcode
                    if fuzz.token_set_ratio(suburb, _suburb) <= 60:
                        should_update = False

                # it's weird to move university suburb into suburb as address will look weird
                if 'UNIVERSITY' in addresses[i]:
                    mm_preclean += '<Uni>'
                    should_update = False

                if should_update:
                    mm_note += "<{0} was in address line {1}>".format(addresses[i], i)
                    suburb = addresses[i]
                    addresses[i] = ''

        return addresses, suburb, state, postcode, country, mm_preclean, mm_note, mm_clean_type, parsed_result
    return wrapped_f


def pre_check_ssp_within_address(f):
    @validate_suburb_state_postcode
    def wrapped_f(*args):
        addresses, suburb, state, postcode, country, mm_preclean, mm_note, mm_clean_type, parsed_result = f(*args)
        if not country:
            i = len(addresses) - 1
            while i >= 0:
                address = addresses[i].upper()

                if address:
                    # address contains suburb
                    #123 Sample Street Wyndham Vale
                    _addresses, _ssp = helper.check_street_in_text(address.upper())

                    if _ssp:
                        _suburb, _state, _postcode = helper.split_suburb_state_postcode(_ssp)
                        _suburb = _suburb.strip(',. ')
                        _state = _state.strip(',. ')
                        _postcode = _postcode.strip(',. ')
                        tobeupdate = False
                        if helper.is_suburb_in_pcdb_fuzzy(_suburb):
                            if ('<SuStP>' in mm_preclean and
                                fuzz.token_set_ratio(suburb, _suburb) <= 70):
                                pass
                            else:
                                mm_note += '<suburb within address: {0}>'.format(suburb)
                                tobeupdate = True
                                suburb = _suburb
                        if helper.is_state_in_pcdb(_state):
                            if '<SuStP>' in mm_preclean:
                                pass
                            else:
                                mm_note += '<state within address: {0}>'.format(state)
                                tobeupdate = True
                                state = _state
                        if helper.is_postcode_in_pcdb(_postcode):
                            if '<SuStP>' in mm_preclean:
                                pass
                            else:
                                mm_note += '<postcode within address: {0}>'.format(postcode)
                                tobeupdate = True
                                postcode = _postcode
                        if tobeupdate:
                            mm_note += '<address line {0} was {1}>'.format(i, address)
                            addresses[i] = addresses[i][:len(_addresses)]
                            break
                    # now po box 20 ballarat
                    else:
                        _addresses, _ssp = helper.check_pobox_in_text(address.upper())
                        if _ssp:
                            _suburb, _state, _postcode = helper.split_suburb_state_postcode(_ssp)
                            _suburb = _suburb.strip(',. ')
                            _state = _state.strip(',. ')
                            _postcode = _postcode.strip(',. ')
                            tobeupdate = False
                            if helper.is_suburb_in_pcdb_fuzzy(_suburb):
                                if ('<SuStP>' in mm_preclean and
                                    fuzz.token_set_ratio(suburb, _suburb) <= 70):
                                    pass
                                else:
                                    mm_note += '<suburb within paddress: {0}>'.format(suburb)
                                    tobeupdate = True
                                    suburb = _suburb
                            if helper.is_state_in_pcdb(_state):
                                if '<SuStP>' in mm_preclean:
                                    pass
                                else:
                                    mm_note += '<state within paddress: {0}>'.format(state)
                                    tobeupdate = True
                                    state = _state
                            if helper.is_postcode_in_pcdb(_postcode):
                                if '<SuStP>' in mm_preclean:
                                    pass
                                else:
                                    mm_note += '<postcode within paddress: {0}>'.format(postcode)
                                    tobeupdate = True
                                    postcode = _postcode
                            if tobeupdate:
                                mm_note += '<paddress line {0} was {1}>'.format(i, address)
                                addresses[i] = addresses[i][:len(_addresses)]
                                break

                    # if addressline2 does not contain ssp, why addressline1?? --> skip it
                    # it will prevent 2 addresslines mixed up
                    break
                i -= 1
        return addresses, suburb, state, postcode, country, mm_preclean, mm_note, mm_clean_type, parsed_result
    return wrapped_f



def fill_state(f):
    """
    If address is valid
    """
    @validate_suburb_state_postcode
    def wrapped_f(*args):

        addresses, suburb, state, postcode, country, mm_preclean, mm_note, mm_clean_type, parsed_result = f(*args)
        if '<SuStP>' not in mm_preclean and not country:
            if not helper.is_state_in_pcdb(state):
                _state = helper.give_me_state(suburb, {"$regex": postcode[:3]})
                if _state:
                    mm_note += "<state: {0} was filled with {1}>".format(state, _state)
                    state = _state

        return addresses, suburb, state, postcode, country, mm_preclean, mm_note, mm_clean_type, parsed_result

    return wrapped_f

def fill_postcode(f):
    """
    If address is valid
    """
    @validate_suburb_state_postcode
    def wrapped_f(*args):

        addresses, suburb, state, postcode, country, mm_preclean, mm_note, mm_clean_type, parsed_result = f(*args)
        if '<SuStP>' not in mm_preclean and not country:
            if not helper.is_postcode_in_pcdb(postcode):
                _postcode = helper.give_me_postcode(suburb, state)
                if _postcode:
                    mm_note += "<postcode: {0} was filled with {1}>".format(postcode, _postcode)
                    postcode = _postcode

        return addresses, suburb, state, postcode, country, mm_preclean, mm_note, mm_clean_type, parsed_result

    return wrapped_f

def fill_suburb(f):
    """
    If address is valid
    """
    @validate_suburb_state_postcode
    def wrapped_f(*args):

        addresses, suburb, state, postcode, country, mm_preclean, mm_note, mm_clean_type, parsed_result = f(*args)
        if '<SuStP>' not in mm_preclean and not country:
            if not suburb:
                _suburb = helper.give_me_suburb(state, postcode)
                if _suburb:
                    mm_note += "<suburb: {0} was filled with {1}>".format(suburb, _suburb)
                    suburb = _suburb

        return addresses, suburb, state, postcode, country, mm_preclean, mm_note, mm_clean_type, parsed_result

    return wrapped_f

def validate_suburb_state_postcode_fuzzy(f):
    """
    Validate suburb, state, and postcode against auspost, big chance it is a good record
    """
    def wrapped_f(*args):

        addresses, suburb, state, postcode, country, mm_preclean, mm_note, mm_clean_type, parsed_result = f(*args)

        if '<SuStP>' not in mm_preclean and not country:
            # check suburb, state, and postcode against australia post database
            # remove comma, . in suburb, check via
            #if postcode return same as state ==> ok
            _states = helper.give_me_state(None, postcode)

            #postcode is valid
            if _states and state.upper().strip() in _states:
                if not NON_WORD_EXP.match(suburb):
                    mm_preclean += '<SuStP>(fuzzy)'
            else:
                _states = helper.give_me_state(suburb, None)
                #suburb is valid
                if _states and state.upper().strip() in _states:
                    if not NON_WORD_EXP.match(postcode):
                        mm_preclean += '<SuStP>(fuzzy)'

        return addresses, suburb, state, postcode, country, mm_preclean, mm_note, mm_clean_type, parsed_result
    return wrapped_f


def fill_state_fuzzy(f):
    """
    If address is valid
    """
    @validate_suburb_state_postcode_fuzzy
    def wrapped_f(*args):

        addresses, suburb, state, postcode, country, mm_preclean, mm_note, mm_clean_type, parsed_result = f(*args)
        if '<SuStP>' not in mm_preclean and not country:
            if helper.is_postcode_in_pcdb(postcode) and not NON_WORD_EXP.match(suburb):
                # get a list of suburbs from postcode
                # get extract match
                # assign state
                # mark it as <SuStP>(fuzzy)
                #{"$regex": postcode[:3]}
                _resultset = helper.from_postcode({"$regex": '^'+postcode[:3]})
                list_of_suburbs, list_of_states, list_of_postcodes = helper.mongo_to_3list(_resultset)
                if list_of_suburbs:
                    try:
                        _suburb, _rate = process.extractOne(suburb, list_of_suburbs)
                    except TypeError:
                        _rate = 0
                        _suburb = ''

                    if _rate >= 75:
                        mm_note += '<{0} is updated to {1} using postcode'.format(state, list_of_states[0])
                        state = list_of_states[0]
                    else:
                        #suburb is more correct
                        _resultset = helper.from_suburb(suburb)
                        list_of_suburbs, list_of_states, list_of_postcodes = helper.mongo_to_3list(_resultset)
                        if list_of_postcodes:
                            try:
                                _postcode, _rate = process.extractOne(postcode, list_of_postcodes)
                            except TypeError:
                                _rate = 0
                                _suburb = ''

                            if _rate >= 75:
                                _state = helper.give_me_state(suburb, _postcode)
                                if _state:
                                    mm_note += '<{0} is updated to {1} using suburb'.format(state, _state)
                                    state = _state

                else:
                    log.info('<'+postcode+'>')
        return addresses, suburb, state, postcode, country, mm_preclean, mm_note, mm_clean_type, parsed_result
    return wrapped_f


def fill_ssp_fuzzy(f):
    """
    If address is valid
    """
    @validate_suburb_state_postcode_fuzzy
    @validate_suburb_state_postcode
    def wrapped_f(*args):
        addresses, suburb, state, postcode, country, mm_preclean, mm_note, mm_clean_type, parsed_result = f(*args)
        if '<SuStP>' not in mm_preclean and not country:
            found = False
            if not NON_WORD_EXP.match(postcode):
                _resultset = r_lookup.run(postcode, parsed_result['THN']+parsed_result['THT'], parsed_result['TN1'])
                resultset = helper.parlinkr_resultset(_resultset)

                #check street
                if resultset:
                    result = resultset[0]
                    # ['', '', '', '', '183', '', '', '', '', '', '', '', '', '', '', 'Freestone', 'Rd', '', '', 'SLADEVALE', 'QLD', '4370']
                    mm_note += '<paflinkr: pc {0} is updated to {1}>'.format(state, result[-2])
                    mm_note += '<paflinkr: pc {0} is updated to {1}>'.format(suburb, result[-3])
                    state = result[-2]  #state
                    suburb = result[-3]  #suburb
                    found = True
                    # is it safe to update
                    if len(resultset) > 1:
                        log.info("paflinkr more than 1 results")
                else:
                    #check po box
                    _resultset = r_lookup.run(postcode, parsed_result['PDT'], parsed_result['PDN'])
                    resultset = helper.parlinkr_resultset(_resultset)
                    if resultset:
                        result = resultset[0]
                        # ['', '', '', '', '183', '', '', '', '', '', '', '', '', '', '', 'Freestone', 'Rd', '', '', 'SLADEVALE', 'QLD', '4370']
                        mm_note += '<paflinkr: pc {0} is updated to {1}>'.format(state, result[-2])
                        mm_note += '<paflinkr: pc {0} is updated to {1}>'.format(suburb, result[-3])
                        state = result[-2]  #state
                        suburb = result[-3]  #suburb
                        found = True
                        # is it safe to update
                        if len(resultset) > 1:
                            log.info("paflinkr more than 1 results")

            if not NON_WORD_EXP.match(suburb) and not found:
                _resultset = r_lookup.run(suburb, parsed_result['THN']+parsed_result['THT'], parsed_result['TN1'])
                resultset = helper.parlinkr_resultset(_resultset)
                if resultset:
                    result = resultset[0]
                    # ['', '', '', '', '183', '', '', '', '', '', '', '', '', '', '', 'Freestone', 'Rd', '', '', 'SLADEVALE', 'QLD', '4370']
                    mm_note += '<paflinkr: su {0} is updated to {1}>'.format(state, result[-2])
                    mm_note += '<paflinkr: su {0} is updated to {1}>'.format(suburb, result[-3])
                    mm_note += '<paflinkr: su {0} is updated to {1}>'.format(postcode, result[-1])
                    postcode = result[-1]  #postcode
                    state = result[-2]  #state
                    suburb = result[-3]  #suburb
                    # is it safe to update
                    if len(resultset) > 1:
                        log.info("paflinkr more than 1 results")
                else:
                    _resultset = r_lookup.run_fuzzy(suburb, parsed_result['THN'][:2])
                    resultset = helper.parlinkr_resultset(_resultset)
                    log.info(parsed_result)
                    resultset = [x for x in resultset
                             if (fuzz.partial_ratio(parsed_result['THN'].upper(), x[0].upper()) >= 75 and
                                parsed_result['THT'].upper() == x[1].upper())]
                    if resultset:
                        for each_result in resultset:
                            _resultset = r_lookup.run(each_result[-1], each_result[0]+each_result[1], parsed_result['TN1'])
                            resultset1 = helper.parlinkr_resultset(_resultset)
                            if resultset1:
                                result = resultset1[0]
                                # ['', '', '', '', '183', '', '', '', '', '', '', '', '', '', '', 'Freestone', 'Rd', '', '', 'SLADEVALE', 'QLD', '4370']
                                mm_note += '<paflinkr: {0} is updated to {1}>'.format(state, result[-2])
                                mm_note += '<paflinkr: {0} is updated to {1}>'.format(suburb, result[-3])
                                mm_note += '<paflinkr: {0} is updated to {1}>'.format(postcode, result[-1])
                                postcode = result[-1]  #postcode
                                state = result[-2]  #state
                                suburb = result[-3]  #suburb
                                # is it safe to update
                                if len(resultset) > 1:
                                    log.info("paflinkr more than 1 results")
                                break
                    else:
                        #now try few word of suburb, then compare 1 more suburb, make sure it is the same
                        #log.info(parsed_result['THN'][:2])
                        _resultset = r_lookup.run_fuzzy(suburb[:4], parsed_result['THN'][:2])
                        log.info(_resultset)
                        resultset = helper.parlinkr_resultset(_resultset)
                        # log.info(parsed_result)
                        resultset = [x for x in resultset
                                 if (fuzz.partial_ratio(parsed_result['THN'].upper(), x[0].upper()) >= 75 and
                                    fuzz.partial_ratio(suburb.upper(), x[-3].upper()) >= 75 and
                                    parsed_result['THT'].upper() == x[1].upper())]

                        if resultset:
                            for each_result in resultset:
                                _resultset = r_lookup.run(each_result[-1], each_result[0]+each_result[1], parsed_result['TN1'])
                                resultset1 = helper.parlinkr_resultset(_resultset)
                                if resultset1:
                                    result = resultset1[0]
                                    # ['', '', '', '', '183', '', '', '', '', '', '', '', '', '', '', 'Freestone', 'Rd', '', '', 'SLADEVALE', 'QLD', '4370']
                                    mm_note += '<paflinkr: {0} is updated to {1}>'.format(state, result[-2])
                                    mm_note += '<paflinkr: {0} is updated to {1}>'.format(suburb, result[-3])
                                    mm_note += '<paflinkr: {0} is updated to {1}>'.format(postcode, result[-1])
                                    postcode = result[-1]  #postcode
                                    state = result[-2]  #state
                                    suburb = result[-3]  #suburb
                                    # is it safe to update
                                    if len(resultset) > 1:
                                        log.info("paflinkr more than 1 results")
                                    break
                        else:
                            #check po box
                            _resultset = r_lookup.run(suburb, parsed_result['PDT'], parsed_result['PDN'])
                            resultset = helper.parlinkr_resultset(_resultset)
                            if resultset:
                                result = resultset[0]
                                # ['', '', '', '', '183', '', '', '', '', '', '', '', '', '', '', 'Freestone', 'Rd', '', '', 'SLADEVALE', 'QLD', '4370']
                                mm_note += '<paflinkr: su {0} is updated to {1}>'.format(state, result[-2])
                                mm_note += '<paflinkr: su {0} is updated to {1}>'.format(suburb, result[-3])
                                mm_note += '<paflinkr: su {0} is updated to {1}>'.format(postcode, result[-1])
                                postcode = result[-1]  #postcode
                                state = result[-2]  #state
                                suburb = result[-3]  #suburb
                                # is it safe to update
                                if len(resultset) > 1:
                                    log.info("paflinkr more than 1 results")

        return addresses, suburb, state, postcode, country, mm_preclean, mm_note, mm_clean_type, parsed_result
    return wrapped_f


def fill_ssp_fuzzy1(f):
    """
    If address is valid
    """
    @validate_suburb_state_postcode_fuzzy
    @validate_suburb_state_postcode
    def wrapped_f(*args):
        addresses, suburb, state, postcode, country, mm_preclean, mm_note, mm_clean_type, parsed_result = f(*args)
        if '<SuStP>' not in mm_preclean and not country:
            _resultset = r_lookup.similar_run(parsed_result['THN'])
            resultset = helper.parlinkr_resultset(_resultset)
            resultset = [x for x in resultset if x[1].upper() == parsed_result['THT'].upper()] # road type same

            # if psotcode not blank
            if not NON_WORD_EXP.match(postcode):
                resultset = [x for x in resultset if x[-1][0] == postcode[0]]  # postcode similar

            # if state not blank
            if not NON_WORD_EXP.match(suburb):
                resultset = [x for x in resultset if fuzz.partial_ratio(suburb.upper(), x[-3].upper()) >= 75]  # postcode similar

            # suburb is not blank, need to compare to make sure than have to have someting in common ==> little rather than wrong
            for each_result in resultset:
                _resultset = r_lookup.run(each_result[-1], each_result[0]+each_result[1], parsed_result['TN1'])
                resultset1 = helper.parlinkr_resultset(_resultset)
                if resultset1:
                    result = resultset1[0]
                    # ['', '', '', '', '183', '', '', '', '', '', '', '', '', '', '', 'Freestone', 'Rd', '', '', 'SLADEVALE', 'QLD', '4370']
                    mm_note += '<paflinkr1: thn {0} is updated to {1}>'.format(state, result[-2])
                    mm_note += '<paflinkr1: thn {0} is updated to {1}>'.format(suburb, result[-3])
                    mm_note += '<paflinkr1: thn {0} is updated to {1}>'.format(postcode, result[-1])
                    postcode = result[-1]  #postcode
                    state = result[-2]  #state
                    suburb = result[-3]  #suburb
                    # is it safe to update
                    if len(resultset) > 1:
                        log.info("paflinkr more than 1 results")
                    break
        return addresses, suburb, state, postcode, country, mm_preclean, mm_note, mm_clean_type, parsed_result
    return wrapped_f

def fill_ssp_maps(f):
    """
    If address is valid
    """
    @validate_suburb_state_postcode_fuzzy
    @validate_suburb_state_postcode
    def wrapped_f(*args):
        addresses, suburb, state, postcode, country, mm_preclean, mm_note, mm_clean_type, parsed_result = f(*args)
        if '<SuStP>' not in mm_preclean and not country:
            _full_address = '{0} {1} {2} {3} {4}'.format(' '.join(addresses), suburb, state, postcode, country)
            # search _full_address in mongo db
            # if sucess found, check for result, save result
            current_date_str = datetime.datetime.now().strftime('%Y-%m-%d')
            if not NON_WORD_EXP.match(_full_address):
                a = {
                    'query': _full_address
                }
                result = helper.geotb.find(a)
                if result.count() > 0:
                    log.info("FOUND")
                    a = result.next()
                else:
                    ## check number of queries for today
                    ## if > max, dont do anything
                    b = {
                        'date': current_date_str
                    }
                    result = helper.geotb.find(b)
                    if result.count() > 1000:
                        log.info("OVER LIMIT")
                    else:
                        result = helper.geocoder.geocode(_full_address)
                        a['date'] = current_date_str
                        if result.is_success():
                            a['location_type'] = result.get_location_type()
                            if 'ROOFTOP' in result.get_location_type():
                                log.info(result.get_location())
                                log.info(len(result))
                                log.info(result.get_formatted_address())
                                a['result'] = result.get_formatted_address()
                            else:
                                for r in result:
                                    log.info(r["formatted_address"])
                        helper.geotb.insert(a)

                if 'result' in a:
                    if ', Australia' in a['result']:
                        temp = [x.strip() for x in a['result'].split(',')]
                        _country = temp.pop()
                        _ssp = temp.pop()
                        _address = ', '.join(temp)
                        log.info(_address)
                        log.info(_ssp)
                        log.info(_country)

                        ### update ssp
                        temp = _ssp.split(' ')
                        _postcode = temp.pop()
                        _state = temp.pop()
                        _suburb = ' '.join(temp)
                        mm_note += '<map: {0} is updated to {1}>'.format(state, _state)
                        mm_note += '<map: {0} is updated to {1}>'.format(suburb, _suburb)
                        mm_note += '<map: {0} is updated to {1}>'.format(postcode, _postcode)
                        postcode = _postcode.encode('utf-8')
                        state = _state.encode('utf-8')
                        suburb = _suburb.encode('utf-8')
                    else:
                        tmp = a['result'].split(',')
                        mm_note += '<map: country is updated>'
                        country = tmp[-1]
            else:
                mm_preclean += '<invalid>'
        return addresses, suburb, state, postcode, country, mm_preclean, mm_note, mm_clean_type, parsed_result
    return wrapped_f

def check_oseas(f):
    """
    If address is valid
    """

    def wrapped_f(*args):
        addresses, suburb, state, postcode, country, mm_preclean, mm_note, mm_clean_type, parsed_result = f(*args)
        if '<SuStP>' not in mm_preclean and not country:
            # check for oseas here in suburb
            _country, _suburb = helper.check_country_in_ssp(suburb)
            if _country:
                country = _country
                suburb = _suburb
                mm_note += 'country: (suburb) {0} was updated to {1}'.format(country, _country)
            else:
                # check for oseas here in state
                _country, _state = helper.check_country_in_ssp(state)
                if _country:
                    country = _country
                    state = _state
                    mm_note += 'country: (state) {0} was updated to {1}'.format(country, _country)
                else:
                    # check for oseas here in postcode
                    _country, _postcode = helper.check_country_in_ssp(postcode)
                    if _country:
                        country = _country
                        postcode = _postcode
                        mm_note += 'country: (postcode) {0} was updated to {1}'.format(country, _country)
        return addresses, suburb, state, postcode, country, mm_preclean, mm_note, mm_clean_type, parsed_result
    return wrapped_f


def dedupe_ssp_in_address(f):
    """
    If address is valid
    """

    def wrapped_f(*args):
        addresses, suburb, state, postcode, country, mm_preclean, mm_note, mm_clean_type, parsed_result = f(*args)
        # compare suburb and address
        #fuzz.token_sort_ratio("fuzzy wuzzy was a bear", "wuzzy fuzzy was a bear")
        for i in range(-1, -len(addresses), -1):
            if not NON_WORD_EXP.match(addresses[i]):
                _rate = fuzz.token_sort_ratio(addresses[i], suburb)
                if _rate >= 80:
                    mm_note += '<address line {0} was {1}>'.format(i, addresses[i])
                    addresses[i] = ''
                    break
                #_rate = fuzz.token_sort_ratio(addresses[i], state)
                # if _rate >= 75:
                #     mm_note += '<address line {0} was {1}>'.format(i, addresses[i])
                #     addresses[i] = ''
                # _rate = fuzz.token_sort_ratio(addresses[i], suburb)
                # if _rate >= 75:
                #     mm_note += '<address line {0} was {1}>'.format(i, addresses[i])
                #     addresses[i] = ''

        return addresses, suburb, state, postcode, country, mm_preclean, mm_note, mm_clean_type, parsed_result
    return wrapped_f


def dpid_address_last(f):
    """
    If address is valid
    """
    def wrapped_f(*args):
        addresses, suburb, state, postcode, country, mm_preclean, mm_note, mm_clean_type, parsed_result = f(*args)

        address = '{0} {1} {2} {3} {4}'.format(' '.join(addresses), suburb, state, postcode, country)
        #cleaning.lock.acquire()
        if helper.is_address_good(address):
            mm_clean_type += '<DPID>'
        else:
            mm_clean_type += '<nonDPID>'

        parsed_result = ''
        #cleaning.lock.release()
        return addresses, suburb, state, postcode, country, mm_preclean, mm_note, mm_clean_type, parsed_result

    return wrapped_f

