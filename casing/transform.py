#!/usr/bin/env python
# -*- coding: latin-1 -*-
import re

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
    
    #check RMB, CMS, RSD, CMA, MS
    tempWord = re.sub("(Pmb|Cmb|Ms|Rsd|Rms|Cma|Cpa|Rmb)(?=\\s+|[0-9])",lambda pat: pat.group(1).upper(), tempWord)
    
    return tempWord
    
def checkCompany(aStr):
    pass



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
        pass
    elif transformType == 'ADDRESS':
        newStr = checkAddress(newStr)
        
    return newStr

if __name__ == '__main__':
    #test1 = 'O\'Connor   O`Connor this is my houses''s Mckly McDonald machine co-or Barney\'s Barney\' s0 P.O.Box G P O Box pO box LMB Barney\'s o Dortothy D\'reilly invoke-me-hello 35AB test Barney\' s'
    #test1 = "macabre      , machell .macadamia macan macadamize macadamized macadamizes macadamizing macafee macaffer macaque macaques macaulay macaroni macaronic  macaronically macaronics macaronies macaronis macaroon macaroons macaws maccheroni macclesfield macduff macedon macedonia macedonian macedonians macerate macerated macerates macerating maceration macerator macerators macers machair machan machans machell machen machete machetes macher machiavelli machiavellian machiavellianism machiavellism machicolate machicolated machicolates machicolating machicolation machicolations machismo mackerel macho machmeter machmeters machos machree machtpolitik machzor machzorim macintosh macintoshes macinzewski mackenzie mackie mackinaw mackinaws mackintosh mackintoshes mackle mackled mackles mackling macmillan macmillanite macquarie macramé macramés macrura macrural macrurous mactation mactations macula maculae macular maculate maculated maculates maculating maculation maculations macule macules maculose macaco macacos macadamisation macadamise macadamised macadamises macadamising macadamization macanese macarise macarised macarises macarising macarism macarisms macarize macarized macarizes macarizing macassar macbeth macbeth maccabaean maccabean maccabees macchie machairodont machairodonts machairodus machairs macleaya macled macles mackey mack maciel macumber macquardt macuenzie macklin macauley mackay macarthur macabees macsfield  macedan macquaire macki macri maceon machin macharell mace machisa macartney macer machon macaskill macey maczkowiack macrae macciavelli macchia macallister machado maccc macor macesic mackins macciocca macha macolino machalek maco maculley macarry macao macqurie maculata maceri macumba macorna macrina macomb macrey macaranga macumba machine machinery mach Machalany Machala Machin- Macri- Mackness Macciocco Mackow Mackovska Mackaway Machenko Mackieson Maccar Maccaio Mackin Machuca Macarow Macris Macaluso Macky Mackieson Macknamara Mackender Maconachy Mackley Mackic Macklan Maconachie Macklan Machnyk Macura Maccora Macarol Macheftsi Machevski Macca Mackwell Mackiewicz Macauda Macaro Macheras Macko Macuz Machi Macks Maccioni Mackney macadam macualey macquarie macchion maccarthy macoma maccauley macguarie macott"
    
    test1 = "Care Po"
    #preclean(test1)
    #print type(test1)
    print titlecase(test1.upper(),'ADDRESS')
    #u = u'abcdé'
    #print ord(u[-1])