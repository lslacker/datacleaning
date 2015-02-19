import blinkwrapper
import sys


class AddressParser:
    """

    """
    def __init__(self, inStr=[], outStr=[],delimiter='|'):
        if not inStr:
            self.inStr = ['ADR']
        if not outStr:
            self.outStr = ['FUT', 'FUN', 'BLT', 'BLN', 'BG1', 'BG2', 'ALN',
                      'THN', 'TN1', 'TS1', 'TN2', 'TS2', 'THT', 'TTS',
                      'PDT', 'PDP', 'PDN', 'PDS', 'LOC', 'STT', 'PCD',
                      'LC2', 'CLC', 'CPC', 'CTN', 'CTT', 'CTS', 'CAD',
                      'BAR', 'BSP', 'PSP', 'PSC', 'DPI', 'PRI', 'CHG',
                      'ERR', 'ERP', 'UNK', 'AFF']
        self.blink = blinkwrapper.BlinkWrapper()
        self.delimiter = delimiter

        self.result = ''

    def parse(self, address):
        if self.blink.setInTemplate(self.inStr, self.delimiter) > 0:
            raise RuntimeError("Input Template is not right")

        if self.blink.setOutTemplate(self.outStr, self.delimiter) > 0:
            raise RuntimeError("Output Template is not right")

        self.result = self.blink.searchAMAS(address)

    def parse_template(self, inStr, outStr, address):
        if self.blink.setInTemplate(inStr, self.delimiter) > 0:
            print self.blink.setInTemplate(inStr, self.delimiter)
            raise RuntimeError("Input Template is not right")
        if self.blink.setOutTemplate(outStr, self.delimiter) > 0:
            raise RuntimeError("Output Template is not right")
        self.result = self.blink.searchAMAS(address)

    def getMeThis(self, key):
        return self.result[key]

    def __del__(self):
        self.blink.cleanUp()


class AddressLookup:

    def __init__(self, delimiter='|'):
        self.blink = blinkwrapper.BlinkWrapper()
        self.delimiter = delimiter
        if self.blink.setAnswerFormat() > 0:
            raise RuntimeError("Answer Format Template is wrong")
        self.result = ''

    def parse(self, inStr, outStr, address):
        if self.blink.setInTemplate(inStr, self.delimiter) > 0:
            print self.blink.setInTemplate(inStr, self.delimiter)
            raise RuntimeError("Input Template is not right")
        if self.blink.setOutTemplate(outStr, self.delimiter) > 0:
            raise RuntimeError("Output Template is not right")
        self.result = self.blink.searchNearest(address)

    def getMeThis(self, key):
        finalResult = []
        for aResult in self.result:
            finalResult.append(aResult[key].strip())
        return (len(finalResult), finalResult)

    def __del__(self):
        self.blink.cleanUp()

if __name__ == '__main__':
    #test = AddressParser();
    #test.parse("51 Honour Ave wyndham vale vic")
    #print test.getMeThis('DPI')
    #test.parse("8/146 Rupert Street Footsdray West 3012")
    test = AddressLookup()

    test.parse(inStr=['PCD', 'MTH'],
               outStr=['THN', 'THT', 'LOC', 'PCD'],
               address='3029|JUD')


    #test.parse(inStr  =['THN','MLC'],
    #           outStr =['THN','THT','LOC','PCD'],
    #           address='ALsdfsdfsd|VICTORY'
    #          )
    print test.getMeThis('THN')



