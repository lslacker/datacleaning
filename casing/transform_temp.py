#!/usr/bin/env python
# -*- coding: latin-1 -*-
import re
import sys
#sys.path.append(r'Z:\melmailing\_lib')
sys.path.append(r'D:\0_works\pyhon_projects\_lib')
import dtconfig
SMALL = 'a|an|and|as|at|but|by|en|for|if|in|of|on|or|the|to|v\.?|via|vs\.?'
PUNCT = "[!\"#$%&'‘()*+,-./:;?@[\\\\\\]_`{|}~]"
def is_a_meaningful_word(a_word, count = 0):
    print '*'*80
    print 'count=%d' % count
    print 'a_word=%s' % a_word
    result = False
    
    if re.search(r'[0-9]+',a_word,re.I):
        return False
    
    myvars = dict(word = a_word)
    results = dtconfig.DB.select('usr_dict', vars = myvars, where="upper(words)=upper($word)")
    print results
    if results:
        result = True
    
    if not result and count == 0:
        if re.search(r'^[od]',a_word,re.I):
            new_word = a_word[0] + "'" + a_word[1:]
            result = is_a_meaningful_word(new_word, 1)
    print result
    print '*'*80
    
    return result
    
def preclean(aStr):
    #check ' or ` S
    #cases = re.findall("('\\s+\\bs|S)",aStr)
    cases = re.sub("\\s{2,}"," ", aStr)
    cases = re.sub("('\\s+(s|S)\\b)(?=\Z| )",'\'S', cases)
    return cases
       
    
def convert(aWord, transformType=None):
    #title case everything
    tempWord = aWord.title()
    
    #check 'S
    tempWord = re.sub("'S$","'s", tempWord)
    
    #check for Mc
    tempWord = re.sub("(Mc)([a-z])(.{2,})",lambda pat: pat.group(1)+pat.group(2).upper()+pat.group(3), tempWord)
    
    #check for Mac
    tempWord = re.sub("(Mac)([^ocrqekihzsbgua])(.{3,})",lambda pat: pat.group(1)+pat.group(2).upper()+pat.group(3), tempWord)
    
    return tempWord

def checkAddress(aStr):
    tempWord = aStr
    
    #check Gpo, Lpo
    tempWord = re.sub("(L|G)(po)(?=\\s+|\\Z|Box|[0-9])",lambda pat: pat.group(1)+pat.group(2).upper(), tempWord)
    
    #check Po
    tempWord = re.sub("(Po)(?=\\Z|\\s+|Box|[0-9])",lambda pat: pat.group(1).upper(), tempWord)
    
    #check RMB, CMS, RSD, CMA
    tempWord = re.sub("(Pmb|Cmb|Rsd|Rms|Cma|Cpa|Rmb)(?=\\s+|[0-9])",lambda pat: pat.group(1).upper(), tempWord)
    
    #check MS
    tempWord = re.sub("(Ms)\\s*(?=[0-9])",lambda pat: pat.group(1).upper(), tempWord)
    
    return tempWord
    
def checkCompany(transformed_words):
    new_words = []
    NORMAL_CASE = 'Pty|Ltd|Inc|Mac|Of|La|Di|Mc|Or|De|Du|Le|Ma|Co'
    
    for each_word in transformed_words:
        new_word = each_word
        if (     not re.search(r'[.]', each_word, re.I)
             and not re.search(r'^\b(%s)\b$' % NORMAL_CASE, each_word, re.I) 
           ):
            if len(each_word) <= 2:
                new_word = each_word.upper()
            elif len(each_word) <= 6:
                if not re.search(r'[aeiou]', each_word, re.I):
                    new_word = each_word.upper()
                else:
                    if len(each_word) == 3 or len(each_word) == 4:
                        if not is_a_meaningful_word(each_word):
                            new_word = each_word.upper()
                    
            
        new_words.append(new_word)
    print new_words
    return new_words


def titlecase(aStr, transformType=None):
    aStr = preclean(aStr)
    newStr = ''
    #print aStr
    words =  re.split(r'(\s+|[./,\"])', aStr)
    #print words
    #print re.split(r'\b(\W+)\b', aStr)
    transformed_words = []
    for eachword in words:
        transformed_words.append(convert(eachword,transformType))
        #print convert(eachword,transformType)
        
    newStr =  ''.join(transformed_words)    
        
    
    if transformType == 'NAME':
        pass
    elif transformType == 'POSITION':
        pass
    elif transformType == 'COMPANY':
        newStr = ''.join(checkCompany(transformed_words))
    elif transformType == 'ADDRESS':
        newStr = checkAddress(newStr)
        
    return newStr

if __name__ == '__main__':
    #test1 = 'O\'Connor   O`Connor this is my houses''s Mckly McDonald machine co-or Barney\'s Barney\' s0 P.O.Box G P O Box pO box LMB Barney\'s o Dortothy D\'reilly invoke-me-hello 35AB test Barney\' s'
    #test1 = "macabre      , machell .macadamia macan macadamize macadamized macadamizes macadamizing macafee macaffer macaque macaques macaulay macaroni macaronic  macaronically macaronics macaronies macaronis macaroon macaroons macaws maccheroni macclesfield macduff macedon macedonia macedonian macedonians macerate macerated macerates macerating maceration macerator macerators macers machair machan machans machell machen machete machetes macher machiavelli machiavellian machiavellianism machiavellism machicolate machicolated machicolates machicolating machicolation machicolations machismo mackerel macho machmeter machmeters machos machree machtpolitik machzor machzorim macintosh macintoshes macinzewski mackenzie mackie mackinaw mackinaws mackintosh mackintoshes mackle mackled mackles mackling macmillan macmillanite macquarie macramé macramés macrura macrural macrurous mactation mactations macula maculae macular maculate maculated maculates maculating maculation maculations macule macules maculose macaco macacos macadamisation macadamise macadamised macadamises macadamising macadamization macanese macarise macarised macarises macarising macarism macarisms macarize macarized macarizes macarizing macassar macbeth macbeth maccabaean maccabean maccabees macchie machairodont machairodonts machairodus machairs macleaya macled macles mackey mack maciel macumber macquardt macuenzie macklin macauley mackay macarthur macabees macsfield  macedan macquaire macki macri maceon machin macharell mace machisa macartney macer machon macaskill macey maczkowiack macrae macciavelli macchia macallister machado maccc macor macesic mackins macciocca macha macolino machalek maco maculley macarry macao macqurie maculata maceri macumba macorna macrina macomb macrey macaranga macumba machine machinery mach Machalany Machala Machin- Macri- Mackness Macciocco Mackow Mackovska Mackaway Machenko Mackieson Maccar Maccaio Mackin Machuca Macarow Macris Macaluso Macky Mackieson Macknamara Mackender Maconachy Mackley Mackic Macklan Maconachie Macklan Machnyk Macura Maccora Macarol Macheftsi Machevski Macca Mackwell Mackiewicz Macauda Macaro Macheras Macko Macuz Machi Macks Maccioni Mackney macadam macualey macquarie macchion maccarthy macoma maccauley macguarie macott"
    
    test1 = "Ct Electrics (Vic) Pty Ltd"
    #preclean(test1)
    #print type(test1)
    print titlecase(test1.upper(),'COMPANY')
    #u = u'abcdé'
    #print ord(u[-1])