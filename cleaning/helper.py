__author__ = 'luan'
import pyparsing as pp
import re
import mongotute
import addressparser
import string
from geocode.google import GoogleGeocoderClient
import difflib


try:
    import logger
    log = logger.getlogger()
except:
    import logging
    log = logging.getlogger()

unicodePrintables = u''.join(unichr(c) for c in xrange(65536)
                                        if not unichr(c).isspace())
STREET_TYPE = 'STREET ST STR \
BOULEVARD BLVD BVD \
LANE LN \
ROAD RD \
AVENUE AVE \
CIRCLE CIR \
COVE CV \
DRIVE DR DV \
PARKWAY PKWY \
COURT CT \
SQUARE SQ \
ALLEY ALY ALLY \
ARCADE ARC \
MANOR MNR \
TRAIL TRL \
ROW \
MEWS \
TERRACE TER TCE TRACE TRCE \
CRESCENT CRES CRESC CRS \
RISE \
CIRCUS CIR CIRCLE CIRC CIRCUIT \
ESPLANADE ESP \
PARADE PDE \
PROMENADE PROM \
PLACE PL \
OVAL QUADRANT \
HIGHWAY HWAY HWY H/WAY \
LOOP LP'
acronym = lambda s: pp.Regex(r"\b"+r"\.?,?".join(s)+r"\.?\b,?", flags=re.IGNORECASE)
state_acronym = lambda s: pp.Regex(s, flags=re.IGNORECASE)




states = {
    'NEW SOUTH WALES': 'NSW',
    'QUEENSLAND': 'QLD',
    'WESTERN AUSTRALIA': 'WA',
    'SOUTH AUSTRALIA': 'SA',
    'NORTHERN TERRITORY': 'NT',
    'AUSTRALIAN CAPITAL TERRITORY': 'ACT',
    'TASMANIA': 'TAS',
    'VICTORIA': 'VIC'
}

# GET CONNECTON FROM MONGODB
conn = mongotute.get_connection()
db = conn.mydb
tb = db.pcdb
geotb = db.geo
countriestb = db.countries
geocoder = GoogleGeocoderClient(False)  # must specify sensor parameter explicitely

m_parser = addressparser.addressparser.AddressParser()
m_lookup = addressparser.addressparser.AddressLookup()


def get_me_countries():
    _resultset = countriestb.find()
    country_codes = []
    country_names = []
    for each_result in _resultset:
        country_codes.append(each_result['country_code'].encode('utf-8'))
        country_names.append(each_result['country_name'].encode('utf-8'))
    return zip(country_codes, country_names)

countriesset = get_me_countries()


def is_address_good(address):

    m_parser.parse(address)

    dpi = m_parser.getMeThis('DPI')

    if dpi != '0':
        return True

    return False

def is_state_in_pcdb(state):
    a = {
        'state': state.upper()
    }
    results = tb.find(a)
    if results.count() > 0:
        return True
    return False

def is_postcode_in_pcdb(postcode):
    a = {
        'postcode': postcode
    }
    results = tb.find(a)
    if results.count() > 0:
        return True
    return False


def is_suburb_in_pcdb(suburb):
    a = {
        'suburb': suburb.upper()
    }
    results = tb.find(a)
    if results.count() > 0:
        return True
    return False

def is_suburb_in_pcdb_fuzzy(suburb):
    suburbs = give_me_suburbs(suburb.upper())

    for suburb in suburbs:
        a = {
            'suburb': suburb.upper()
        }
        results = tb.find(a)
        if results.count() > 0:
            return True
        return False

def is_ssp_in_pcdb(suburb, state, postcode):
    a = {
        'suburb': suburb.upper(),
        'state': state.upper(),
        'postcode': postcode
    }
    results = tb.find(a)
    if results.count() > 0:
        return True
    return False

def is_ssp_in_pcdb_fuzzy(suburb, state, postcode):
    _addresses, _suburb = check_street_in_text(suburb)

    if _addresses and not is_suburb_in_pcdb(_addresses):
        return False

    _addresses, _suburb = check_pobox_in_text(suburb)
    if _addresses:
        return False

    suburbs = give_me_suburbs(suburb.upper())

    for suburb in suburbs:
        a = {
            'suburb': suburb.upper(),
            'state': state.upper(),
            'postcode': postcode
        }
        results = tb.find(a)
        if results.count() > 0:
            return True
        return False

def is_sup_in_pcdb_fuzzy(suburb, state, postcode, cond='SuStP'):
    suburbs = give_me_suburbs(suburb.upper())
    log.info(suburbs)
    a = {}
    # if 'St' in cond:
    #     a['state'] = state
    # if 'P' in cond:
    #     a['postcode'] = postcode
    #
    is_good = False
    _state = ''
    _postcode = ''

    while suburbs:
        a['suburb'] = suburbs.pop()
        results = tb.find(a)
        if results.count() > 0:
            is_good = True
            break
            # list_of_state = mongo_to_list(results, 'state')
            # list_of_postcode = mongo_to_list(results, 'postcode')
            #
            # # Update state
            # if 'P' in cond and len(list_of_state) == 1 and state.upper() != list_of_state[0].upper():
            #     _state = list_of_state[0]
            # # Update postcode
            # if 'St' in cond and len(list_of_postcode) == 1 and postcode.upper() != list_of_postcode[0].upper():
            #     _postcode = list_of_postcode[0]

    return is_good, suburbs

def rename_split_state(text):
    _state_keys = states.keys()
    _state = state_acronym(_state_keys.pop())
    for x in _state_keys:
        _state = _state | state_acronym(x)

    for t, start, end in _state.scanString(text):
        return text.replace(t[0], states[t[0]])

    return text

def mongo_to_list(resultset, key):
    a = []
    for result in resultset:
        try:
            a.index(result[key])
        except ValueError:
            a.append(result[key])
    return a

def mongo_to_3list(resultset):
    a = []
    b = []
    c = []
    for result in resultset:
        try:
            a.index(result['suburb'])
        except ValueError:
            a.append(result['suburb'])
        try:
            b.index(result['state'])
        except ValueError:
            b.append(result['state'])
        try:
            c.index(result['postcode'])
        except ValueError:
            c.append(result['postcode'])
    return a, b, c

def parlinkr_resultset(resultset):

    results = []
    if resultset:
        for each_result in resultset:
            fields = each_result.split('\t')
            fields.pop()
            fields = [x.encode('utf-8') for x in fields]
            results.append(fields)
    return results


def check_mt_word(f):
    def wrapped_f(*args):
        text = f(*args)
        mt = pp.Combine(pp.Keyword("MT") + pp.Optional(".").suppress())
        for t, start, end in mt.scanString(text):
            text = text.replace(t[0], 'MOUNT ').strip()
        #return text.replace(match_t, states[match_t])

        return text.replace('  ', ' ')
    return wrapped_f

def check_lwr_word(f):
    def wrapped_f(*args):
        text = f(*args)
        mt = pp.Combine("LWR" + pp.Optional("."))
        for t, start, end in mt.scanString(text):
            #log.info(t[0])
            text = text.replace(t[0], 'LOWER ').strip()
        #return text.replace(match_t, states[match_t])
        return text.replace('  ', ' ')
    return wrapped_f

def check_nsew_word(f):
    def wrapped_f(*args):
        text = f(*args)
        nsew = pp.WordStart() + pp.Combine(pp.oneOf("N S E W") + pp.Optional(".")) + pp.WordEnd()
        #mount walker
        for t, start, end in nsew.scanString(text):
            _t = ''
            if t[0][0].startswith('N'):
                _t = 'NORTH'
            elif t[0][0].startswith('S'):
                _t = 'SOUTH'
            elif t[0][0].startswith('E'):
                _t = 'EAST'
            elif t[0][0].startswith('W'):
                _t = 'WEST'
            else:
                pass
            text = text.replace(t[0], _t)

        return text.replace('  ', ' ')
    return wrapped_f


@check_lwr_word
@check_nsew_word
@check_mt_word
def rename_split_suburb(text):
    return text.upper()


def split_suburb_state_postcode(text):
    """
    Split suburb, state, postcode
    """
    #x = [ord(x) for x in text.decode('utf-8')]
    #log.info(x)
    # "\xe2\x80\x99" -- right single quotation
    # "\xe2\x80\x98" -- left single quotation
    word = pp.Word(pp.alphanums+"'.,\"/-`" + "\xe2\x80\x99" + "\xe2\x80\x98")
    #word = pp.Word(unicodePrintables)
    _state = (acronym('NSW') | acronym('QLD') | acronym('VIC') | acronym('ACT') | acronym('TAS') | acronym('NT')
             | acronym('SA') | acronym('WA') | acronym('Q')).setResultsName('state')
    #log.info(_state)
    #_postcode = pp.Regex(r"\d{3,4}$", flags=re.IGNORECASE).setResultsName("postcode")
    _postcode = pp.Word(pp.nums+".,", min=3).setResultsName("postcode")
    #_suburb = pp.Group(word + pp.ZeroOrMore(~_state+word)).setResultsName("suburb")
    _suburb = pp.Group(pp.OneOrMore(~_state+~_postcode+word)).setResultsName("suburb")
    ssp = pp.Optional(_suburb) + pp.Optional(_state) + pp.Optional(_postcode + pp.lineEnd())
    try:
        result = ssp.parseString(text.replace(",", ", "))
    except pp.ParseException:
        log.info(text)
        raise
    try:
        suburb = ' '.join(result['suburb'])
    except KeyError:
        suburb = ''

    try:
        state = result['state']
        if state == 'Q':
            state = 'QLD'
    except KeyError:
        state = ''

    try:
        postcode = result['postcode']
        # make sure it is australia postcode
    except KeyError:
        postcode = ''

    # do final check
    if suburb.endswith('PRIVATE BOXES'):
        suburb = text
        state = ''
        postcode = ''
    log.info(suburb)
    return suburb, state, postcode

def check_street_in_text(text):
    """
    Split suburb, state, postcode
    """
    suburb = ''
    address = ''
    #ALLEY|ALY|ALLY|ARCADE|ARC|AVENUE|AVE|BOULEVARD|BLVD|BVD|ROAD|RD|STREET|ST|STR|DRIVE|DR|DRV
    # |CLOSE|CL|LANE|LN|MANOR|MNR|MEWS|PLACE|PL|ROW|TERRACE|TER|TCE|TRACE|TRCE|TRAIL|TRL|COURT|
    # CT|CIRCUS|CIR|CIRCLE|CIRC|CIRCUIT|CRESCENT|CRES|CRESC|LOOP|OVAL|QUADRANT|
    # SQUARE|SQ|GROVE|GRV|PARKWAY|PKWY|RISE|ESPLANADE|ESP|PARADE|PDE|PROMENADE|PROM|WALK|HIGHWAY|HWY

    street_type = pp.Combine(pp.MatchFirst(map(pp.Keyword, STREET_TYPE.split())) + pp.Optional(".").suppress())

    for t, start, end in street_type.scanString(text):
        if start > 0:
            address = text[:end]
            suburb = text[end:]
    return address, suburb

def check_pobox_in_text(text):
    """
    Split suburb, state, postcode
    """
    suburb = ''
    address = ''
    #ALLEY|ALY|ALLY|ARCADE|ARC|AVENUE|AVE|BOULEVARD|BLVD|BVD|ROAD|RD|STREET|ST|STR|DRIVE|DR|DRV
    # |CLOSE|CL|LANE|LN|MANOR|MNR|MEWS|PLACE|PL|ROW|TERRACE|TER|TCE|TRACE|TRCE|TRAIL|TRL|COURT|
    # CT|CIRCUS|CIR|CIRCLE|CIRC|CIRCUIT|CRESCENT|CRES|CRESC|LOOP|OVAL|QUADRANT|
    # SQUARE|SQ|GROVE|GRV|PARKWAY|PKWY|RISE|ESPLANADE|ESP|PARADE|PDE|PROMENADE|PROM|WALK|HIGHWAY|HWY
    poboxnumber = pp.Combine(pp.Optional(pp.Word(pp.alphas, max=1) + pp.CaselessLiteral(" ")) + pp.Word(pp.nums) + pp.Optional(pp.CaselessLiteral(" ") + pp.Word(pp.alphas, max=2)))
    poboxref = ((acronym("PO") | acronym("LPO") | acronym("GPO") | acronym("CMA") | acronym("CMB") | acronym("CPA")
                | acronym("MS") | acronym("RMB") | acronym("RMS") | acronym("RSD") | acronym("POSTAL")) +
                pp.Optional(pp.CaselessLiteral("BOX"))) + poboxnumber

    for t, start, end in poboxref.scanString(text):
        #log.info(t)
        address += text[:end] + ' '
        suburb += text[end:] + ' '
    return address.strip(), suburb.strip()

def nsew_suburb(text):
    nsew = pp.WordStart() + pp.Combine(pp.oneOf("NORTH SOUTH EAST WEST N E W S NTH STH") + pp.Optional(".").suppress()) + pp.WordEnd()
    nsew_pt_mt = pp.OneOrMore(nsew).setResultsName("direction")

    is_first = False
    is_last = False

    # west footscray
    suburb_with_nsew_pt_mt_first = nsew_pt_mt + pp.OneOrMore(pp.Word(pp.alphanums+"'.,\"/-`")).setResultsName("suburb")

    # footscray west
    suburb_with_nsew_pt_mt_last = pp.OneOrMore(~nsew_pt_mt + pp.Word(pp.alphanums+"'.,\"/-`")).setResultsName("suburb") + nsew_pt_mt
    try:
        result = suburb_with_nsew_pt_mt_last.parseString(text)
        is_last = True
    except pp.ParseException:
        try:
            result = suburb_with_nsew_pt_mt_first.parseString(text)
            is_first = True
        except pp.ParseException:
            pass

    if is_first or is_last:
        directions = result["direction"]
        suburbs = result["suburb"]
        for idx, direction in enumerate(directions):
            if direction.startswith('N'):
                directions[idx] = 'NORTH'
            elif direction.startswith('S'):
                directions[idx] = 'SOUTH'
            elif direction.startswith('E'):
                directions[idx] = 'EAST'
            elif direction.startswith('W'):
                directions[idx] = 'WEST'
        if is_first:
            return "{1} {0}".format(' '.join(suburbs), ' '.join(directions)), "{0} {1}".format(' '.join(suburbs), ' '.join(directions))
        else:
            return "{1} {0}".format(' '.join(directions), ' '.join(suburbs)), "{0} {1}".format(' '.join(directions), ' '.join(suburbs))
    return None


def give_me_suburbs(text):
    punc="`'-/"
    suburbs = pp.Word(pp.alphanums + punc)
    _suburbs = []
    for t, start, end in suburbs.scanString(text):
        _suburbs.append(t[0])

    intab = ""
    outtab = ""
    trantab = string.maketrans(intab, outtab)

    _suburbs = map(lambda x: x.translate(trantab, punc), _suburbs)
    _suburb1 = []

    while True:
        try:
            i = _suburbs.index('VIA')
            if i > 0:
                _suburb1 = _suburbs[i+1:]
                _suburbs = _suburbs[:i]  # possibly street
            else:
                _suburbs.pop(i)
        except ValueError:
            break
    result = []
    extras = []

    #make sure _suburbs is not street

    for a in [' '.join(_suburbs), ' '.join(_suburb1)]:
        if a.startswith("OBIL") or \
                a.startswith("OBRIEN") or \
                a.startswith("OCONNOR") or \
                a.startswith("OCONNELL") or \
                a.startswith("OHALLORAN") or \
                a.startswith("OSULLIVAN") or \
                a.startswith("DAGUILAR") or \
                a.startswith("DESTREES"):
            a = a[0] + "'" + a[1:]
        if a.endswith(' ST'):
            a += 'REET'
        if ' ST ' in a:
            a = a.replace(' ST ', ' STREET ')

        # footscray west --> we have to check west footscray
        extra_suburbs = nsew_suburb(a)
        if extra_suburbs:
            for extra_suburb in extra_suburbs:
                extras.append(extra_suburb)

        result.append(a)

    result = [x for x in result if x]

    if 'WATTLETREE RD POST OFFICE' in result:
        extras.append('WATTLETREE ROAD PO')
    if 'GCMC' in result:
        extras.append('GOLD COAST MC')
    if extras:
        result.extend(extras)

    return result

def give_me_state(suburb, postcode):
    if suburb is not None:
        if postcode is not None:
            for _suburb in give_me_suburbs(suburb):
                a = {
                    'suburb': _suburb.upper(),
                    'postcode': postcode
                }
                results = tb.find(a)
                results = mongo_to_list(results, 'state')
                if len(results) == 1:
                    return results[0].encode('utf-8')
        else:
            a = {
                'postcode': postcode
            }
            results = tb.find(a)
            results = mongo_to_list(results, 'state')
            if len(results) > 1:
                return results

    else:
        a = {
            'postcode': postcode
        }
        results = tb.find(a)
        results = mongo_to_list(results, 'state')
        if len(results) > 0:
            return results

    return None

def give_me_postcode(suburb, state):
    for _suburb in give_me_suburbs(suburb):

        a = {
            'suburb': _suburb.upper(),
            'state': state.upper()
        }

        results = tb.find(a)
        results = mongo_to_list(results, 'postcode')

        if len(results) == 1:
            return results[0].encode('utf-8')
    return None

def give_me_suburb(state, postcode):
    a = {
        'postcode': postcode,
        'state': state.upper()
    }
    results = tb.find(a)
    results = mongo_to_list(results, 'suburb')
    if len(results) == 1:
        return results[0].encode('utf-8')

    return None


def from_postcode(postcode):
    a = {
        'postcode': postcode
    }
    return tb.find(a)

def from_suburb(suburb):
    a = {
        'suburb': suburb.upper()
    }
    return tb.find(a)

@check_mt_word
def test_function(addresses, suburb, state, postcode, country, mm_preclean, mm_note, mm_clean_type):
    return addresses, suburb, state, postcode, country, mm_preclean, mm_note, mm_clean_type


def parse_address(text):
    # define number as a set of words

    streetnumber = pp.originalTextFor(pp.Word(pp.nums))

    # just a basic word of alpha characters, Maple, Main, etc.


    # types of streets - extend as desired
    street_type = pp.Combine(pp.MatchFirst(map(pp.Keyword, STREET_TYPE.split())) + pp.Optional(".").suppress())
    street_name = pp.OneOrMore(~street_type + pp.Combine(pp.Word(pp.alphas) + pp.Optional(".")))
    streetAddress = streetnumber+ street_name + street_type

    log.info(streetAddress.parseString(text))

def check_dupes_info(address, suburb):
    s = difflib.SequenceMatcher(None, address.upper(), suburb.upper())
    matching_blocks = s.get_matching_blocks()
    matching_blocks.pop()
    log.info(matching_blocks)
    if len(matching_blocks) == 1:
        i, j, n = matching_blocks[0]
        if (i == 0 and j == 0
            and (n == len(address) or n == len(suburb))):
            return True
        else:
            log.info(address)
            log.info(suburb)

def check_country_in_ssp(text):

    _country = None
    found = False
    _new_country = ''
    _new_text = ''

    for country_code, country_name in countriesset:

        if not country_name:
            continue
        log.info(country_name)
        _country = acronym(country_name)
        for t, start, end in _country.scanString(text):
            _new_text = text[:start] + text[end:]
            found = True
            break
        if found:
            _new_country = country_name
            break

    return _new_country, _new_text


def check_ssp_within_address(text):
    #123 Sample Street Wyndham Vale
    _addresses, _ssp = check_street_in_text(text.upper())
    # how to check ssp
    _suburb, _state, _postcode = split_suburb_state_postcode(_ssp)




if __name__ == '__main__':
    #log.info(split_suburb_state_postcode("North Motton, Ulverstone TAS 7315"))
    #log.info(check_pobox_in_text('PO BOX 350 CP  Ballarat'))
    # addresses = [' ']
    # suburb = 'Lower Mt Walker'
    # state = ''
    # postcode = ''
    # country = ''
    # mm_preclean = ''
    # mm_note = ''
    # mm_clean_type = ''
    # log.info(rename_split_suburb("Cape Clear C/- Post Office".upper()))
    #log.info(split_suburb_state_postcode("Cape Clear C/- Post Office".upper()))
    #log.info(give_me_suburbs('"OBRIEN '))
    # m_lookup.parse(inStr=['TN1','THN', 'PCD'],
    #        outStr=['TN1', 'THN', 'THT', 'LOC', 'PCD'],
    #        address='1|SHAWS|7277')
    # log.info(m_lookup.result)
    #loc_result = m_lookup.getMeThis('LOC')[1]
    #check_country_in_ssp("HILLSBOROUGH, AUCKLAND NZ")

    #s1 = 'BALLARAT'

    #s2 = 'BALLARAT, MELBOURNE'
    #log.info(fuzz.ratio(s2, s1))
    #log.info(fuzz.token_set_ratio(s1, s2))

    #log.info(loc_result)
    #s = difflib.SequenceMatcher(None, s2.upper(), s1.upper())
    #matching_blocks = s.get_matching_blocks().pop()
    #matching_blocks.pop()
    #log.info(matching_blocks.pop())
    #parse_address("11 MCCLEVERTY'S COURT".upper())
    #log.info(STREET_TYPE.split())
    #log.info(nsew_suburb("MOOROOPNA"))
    #log.info(nsew_suburb("NORTH kippa ring"))
    #log.info(nsew_suburb("WEST FOOTSCRAY"))
    #log.info(give_me_state('WEST FOOTSCRAY', {"$regex": '301'}))
    log.info(split_suburb_state_postcode("EAST VICTORIA PARK 6101"))
    #log.info(check_street_in_text('59 MANOR LAKES BVD'))