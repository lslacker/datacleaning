__author__ = 'luan'
import pyparsing as pp
import re

word = pp.Word(pp.alphas)
num = pp.Word(pp.nums)

suburbs = pp.OneOrMore(word)
state = pp.Combine(pp.oneOf("NSW VIC"))
postcode = pp.OneOrMore(pp.Word(pp.nums))
ssp = state
testList = ['Mcdonal VIC 3024']
# - - - - - m a i n
def main():
    for text in testList:
        test(text)

# - - - t e s t
def test(s):
    print "---Test for '{0}'".format(s)
    try:
        result = ssp.parseString(s)

        print " Matches: {0}".format(result)
    except pp.ParseException as x:
        print " No match: {0}".format(str(x))

if __name__ == "__main__":
    #main()

    word = pp.Word(pp.alphanums+"'.,\"")

    acronym = lambda s: pp.Regex(r"\.?\s*".join(s)+r"\.?", flags=re.IGNORECASE)

    state = (acronym('NSW') | acronym('QLD') | acronym('VIC') | acronym('ACT') | acronym('TAS') | acronym('NT')
             | acronym('SA') | acronym('WA')).setResultsName('state')

    postcode = pp.Word(pp.nums, exact=4).setResultsName("postcode")

    suburb = pp.Group(pp.OneOrMore(~state+~postcode+word)).setResultsName("suburb")

    ssp = pp.Optional(suburb) + pp.Optional(state) + pp.Optional(postcode)

    result = ssp.parseString('wyndham vale 32257')

    print result
    print result['suburb']
    #print result['state']
    print result['postcode']

