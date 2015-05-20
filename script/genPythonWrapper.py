#!/usr/bin/env python

# Some basic idea of the generated source files and how to use it.
##
##
##            +-----------+  parse +-------------+ wrapped+-------------------+ wrapped  +-----------+ compile  +----------+
##            |EClient.h  |------->|IBClient.hpp |------->|IBClientWrapper.hop|--------->|IBroker.cpp|--------->|IBroker.so|
##            |EWrapper.h |        +-------------+        +-------------------+        / +-----------+          +----------+
##            +-----------+                                                           /
##                                                                                   /
##                                                                                  /
##                                                                                 / parse
##                                                        +---------------------+ /
##                                                        |Other Data Structures|/
##                                                        +---------------------+
##
##
##






import re

from ConstDefs import *

def addBackVariableName(p):
    '''

    In case that the declare looks like "void getOrder(const Order&)",
    we need to add a variable name so that getListParamName won't be
    confused.

    Input:  A string. It is assumed to contain exact one declare.

    Output: A modified string
    '''

    label = 0; # to handle the case such that multiple arguments have same type
    tmp = p.replace('const', '').strip().split(' ')
    if len(tmp) == 1 :
        mo = re.search('(\w+)', tmp[0])
        if mo :
            varname = mo.groups()[0].lower() + str(label)
            label = label + 1
            return p + ' ' + varname
    else :
        return p

def parseOneFunc(c) :
    '''

    Split the function declare into return type, name and parameters

    Input: A string potentally contains a declare of function

    Output: A dict with "return", "name", and "paramList" fields. The
    former two are both string and the third one is a list of
    strings.
    '''

    c = c.replace('\n', ' ').strip()
    res = dict();
    mo = re.search('(.*) (\w+)\((.*)\)', c)
    if mo :
        moRes = mo.groups()
        res['return'] = moRes[0]
        res['name'] = moRes[1]
        res['paramList'] = [addBackVariableName(e.strip()) for e in moRes[2].strip().split(',') if e.strip() != '']
    return res

def getListParamName(ss) :
    '''

    Get a list of all parameter's variable name. i.e. strip out the type
    info.

    Input: a list of strings from "paramList". Inside, each string
    potentially contains one declare

    Output: a list of corresponding variables
    '''

    ret = list()
    for s in ss :
        mo = re.search('(\w+$)', s.split('=')[0].strip())
        if mo :
            ret.append(mo.groups()[0])
    return ret

def parseApiFromFile(fname) :
    '''

    Parse all interfaces from a particular file. It assumes all API are
    marked by modifier 'virtual'
    '''

    with open(fname, 'rt') as f :
        res = list()
        codes = ' '.join(f.readlines()).split('virtual ')
        for c in codes[1:] :  # skip header
            if c[0] == '~' :  # ignore destructor
                continue
            res.append(parseOneFunc(c))
        return res

def genFuncDeclare(pres, modifier='') :
    '''
    Generate a function declare


    Input:
          pres : a dict contains function parsing results. It is of same format as return of "parseOneFunc"

          modifier: The modifier of the function.

    Output: A string of function declare.
    '''

    ret = modifier + ' ' + pres['return'] + ' ' + pres['name'] + '(' + ', '.join(pres['paramList']) + ')'
    return ret.strip()

def genFuncBody(pres, delegator, empty = False) :
    '''
    Generate function body for APIs in EClient and EWrapper

    Input:
          pres : a dict contains function parsing results. It is of same format as return of "parseOneFunc"

          delegator: name of the delegator, which does the real work in the C++ code.

    Output: A string contains function body (the implementation)
    '''
    if empty :
        body = ''
    else :
        body = delegator + '->' + pres['name'] + '(' + ', '.join(getListParamName(pres['paramList'])) + ');'
        if pres['return'] != 'void' :
            body = 'return ' + body
    return '{' + body + '}'


headerPath = 'include/'  #path to the header files which are from IB official website

# parsed API results from EClient.h
resEClient = parseApiFromFile(headerPath + 'EClient.h')

# parsed API results from EWrapper.h
resEWrapper = parseApiFromFile(headerPath + 'EWrapper.h')


def formatForSourceFile(t) :
    ''' ???? '''
    return '\t' + t[0] + '\n' + '\t\t' + ('\n\t\t').join(t[1:])

def extractDataName(fin, st, t = 'struct') :
    '''
    Extract a particular data structure's member variables

    Input:
          fin: input file name

          st:  structure/class's name

          t:   class, struct or enum

    Output: name list of member variables.
    '''

    with open(fin, 'rt') as f :
        ret = list()
        matchString = '\s+%s$' % st
        findFlag = False
        matchString = t + matchString
        tmpRet = list()
        for l in f.readlines() :
            ll = l.strip().split('{')[0]
            mo = re.search(matchString, ll.strip())
            if mo :
                findFlag = True
            if findFlag and '};' in l :
                break;
            if  findFlag :
                if t != 'enum' :
                    tmpl = l.strip().split('//')
                    l = tmpl[0].strip()
                    if l and l.strip()[-1] == ';' and 'typedef' not in l and '(' not in l and ')' not in l and '=' not in l:
                        mo2 = re.search('(\w+);$', l.strip())
                        ret.append(mo2.groups()[0])
                else :
                   tmpRet.append(l.strip())
        if t == 'enum' :
            tmp = ' '.join(tmpRet)
            tmp = tmp.split('{')[-1]
            ret = [e.strip() for e in tmp.split(',') if e.strip()]
        return ret


def extractDataStructure() :
    ''' Extract extra data structures for external usage. The info of data
    structures needs to be extracted comes from "other DataStructure". '''

    ret = list()
    for d in otherDataStructure :
        for s in d['name'] :
            nameList = extractDataName(headerPath + d['file'], s, d['type'])
            if d['type'] != 'enum' :
                tmp = ['class_<{0}>("{0}")'.format(s)]
                tmp = tmp + ['.def_readwrite("{0}", &{1}::{0})'.format(n, s) for n in nameList]
            else :
                tmp = ['enum_<{0}>("{0}")'.format(s)]
                tmp = tmp + ['.value("{0}", {0})'.format(n, s) for n in nameList]
            tmp.append(';')
            ret.append(formatForSourceFile(tmp))
    return ret


def extractIBClient() :
    ''' extract all API for IBClient and return the formated source code '''

    ret = ['class_<IBClientWrapper, boost::noncopyable>("IBClient")']
    ret = ret + ['.def("{0}", &IBClient::{0})'.format(p['name']) for p in resEClient]
    ret = ret + ['.def("{0}", &IBClient::{0}, &IBClientWrapper::default_{0})'.format(p['name']) for p in resEWrapper]
    ret = ret + ['.def("{0}", &IBClient::{0}, &IBClientWrapper::default_{0})'.format(p['name']) for p in customizedAPI]
    ret.append(";")
    return formatForSourceFile(ret)

def genIBClientHeaderFile() :
    ''' Generate IBClient.hpp '''

    with open('IBClient.hpp', 'wt') as f :
        apiEClient = [genFuncDeclare(p) + genFuncBody(p, 'm_pClient') for p in resEClient]
        apiEClientExtra = [genFuncDeclare(p) + genFuncBody(p, 'm_pClient') for p in extraAPI]
        apiEWrapper = [genFuncDeclare(p, "virtual") + genFuncBody(p, '', True) for p in resEWrapper]
        f.write(ibClientHeader)
        f.write('\n\t//API of EClient\n\t')
        f.write('\n\t'.join(apiEClient))
        f.write('\n\n\t//API of EClient (extra)\n\t')
        f.write('\n\t'.join(apiEClientExtra))
        f.write('\n\n\t//API of EWraper (Callbacks)\n\t')
        f.write('\n\t'.join(apiEWrapper))
        f.write('\n\n\t//API of EClient (customized)\n\t')
        f.write(customizedCode)
        f.write(ibClientTail)

def genIBClientWrapperHeaderFile() :
    ''' Generate IBClientWrapper.hpp '''

    with open('IBClientWrapper.hpp', 'wt') as f :
        overrides = list()
        for p in resEWrapper + customizedAPI:
            str0 = p['name']
            str1 = '(' + ', '.join(p['paramList']) + ')'
            str2 = p['name'] + '(' + ', '.join(getListParamName(p['paramList'])) + ')'
            str3 = p['return']
            if str3 != 'void' :
                str4 = 'return '
                str5 = ''
            else :
                str4 = ''
                str5 = '\n' + '\t' * 3 + 'return;'
            overrides.append(wrapperTemplate.format(str0, str1, str2, str3, str4, str5))
        f.write(ibClientWrapperHeader)
        f.write('\n'.join(overrides))
        f.write(ibClientWrapperTail)


def genIBrokerSourceFile() :
    ''' Generate IBroker.cpp '''

    with open('IBroker.cpp', 'wt') as f :
        f.write(ibrokerHead)
        f.write('\n\n'.join(extractDataStructure()))
        f.write('\n\n')
        f.write(extractIBClient())
        f.write(ibrokerTail)


if __name__ == '__main__' :
    genIBClientHeaderFile()
    genIBClientWrapperHeaderFile()
    genIBrokerSourceFile()
