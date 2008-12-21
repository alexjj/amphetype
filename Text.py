# -*- coding: UTF-8 -*-

from __future__ import division, with_statement

#import psyco
import re
import codecs
import random
import textwrap
from Config import Settings
from itertools import *
from PyQt4.QtCore import *

abbreviations = set(map(unicode, [
'jr', 'mr', 'mrs', 'ms', 'dr', 'prof', 'sr', "sen","rep","sens", "reps",'gov', "attys", "atty", 'supt', 
'det', 'rev', 'col','gen', 'lt', 'cmdr', 'adm', 'capt', 'sgt', 'cpl', 'maj', 
'dept', 'univ', 'assn', 'bros', 'inc', 'ltd', 'co', 'corp', 
'arc', 'al', 'ave', "blvd", "bld",'cl', 'ct', 'cres', 'dr', "expy", "exp", 'dist', 'mt', 'ft',
"fwy", "fy",  "hway", "hwy",'la', "pde", "pd", 'pl', 'plz', 'rd', 'st', 'tce',
'Ala' , 'Ariz', 'Ark', 'Cal', 'Calif', 'Col', 'Colo', 'Conn',
'Del', 'Fed' , 'Fla', 'Ga', 'Ida', 'Id', 'Ill', 'Ind', 'Ia',
'Kan', 'Kans', 'Ken', 'Ky' , 'La', 'Me', 'Md', 'Is', 'Mass', 
'Mich', 'Minn', 'Miss', 'Mo', 'Mont', 'Neb', 'Nebr' , 'Nev',
'Mex', 'Okla', 'Ok', 'Ore', 'Penna', 'Penn', 'Pa'  , 'Dak',
'Tenn', 'Tex', 'Ut', 'Vt', 'Va', 'Wash', 'Wis', 'Wisc', "Wy",
'Wyo', 'USAFA', 'Alta' , 'Man', 'Ont', u'Qué', 'Sask', 'Yuk', 
'jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec','sept', 
'vs', 'etc', 'no', 'esp', 'eg', 'ie', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12',
'avg', 'viz', 'm', 'mme']))

class SentenceSplitter(object):
    sen = re.compile(r"""(?:(?: |^)[^\w. ]*(?P<pre>\w+)[^ .]*\.+|[?!]+)['"]?(?= +(?:[^ a-z]|$))|$""")

    def __init__(self, text):
        self.string = text
    
    def __iter__(self):
        p = [0]
        return ifilter(None, imap(lambda x: self.pars(p, x), self.sen.finditer(self.string)))
    
    def pars(self, p, mat):
        if mat.group('pre') and self.isAbbreviation(mat.group('pre')):
            return None
        p.append(mat.end())
        return self.string[p[-2]:p[-1]].strip()

    def isAbbreviation(self, s):
        ls = s.lower()
        return ls in abbreviations or s in abbreviations


class LessonMiner(QObject):
    def __init__(self, fname, width=85, min_chars=220):
        super(LessonMiner, self).__init__()
        #print time.clock()
        with codecs.open(fname, "r", "utf_8_sig") as f:
            self.paras = self.paras(f)
        self.lessons = None
        self.min_chars = min_chars
        self.width = width

    def doIt(self):
        self.lessons = []
        backlog = []
        backlen = 0
        i = 0
        for p in self.paras:
            if len(backlog) > 0:
                backlog.append(None)
            for s in p:
                backlog.append(s)
                backlen += len(s)
                if backlen >= self.min_chars:
                    self.lessons.append(self.popFormat(backlog))
                    backlen = 0
            i += 1
            self.emit(SIGNAL("progress(int)"), int(100 * i/len(self.paras)))
        if backlen > 0:
            self.lessons.append(self.popFormat(backlog))
    
    def popFormat(self, lst):
        #print lst
        ret = []
        p = []
        while len(lst) > 0:
            s = lst.pop(0)
            if s is not None:
                p.append(s)
            else:
                ret.append( #textwrap.fill(
                                        u' '.join(p)) #, self.width))
                p = []
        if len(p) > 0:
            ret.append( #textwrap.fill(
                                       u' '.join(p)) #, self.width))
        #print ret
        return u'\n'.join(ret)

    def __iter__(self):
        if self.lessons is None:
            self.doIt()
        return iter(self.lessons)
    
    def paras(self, f):
        p = []
        ps = []
        for l in f:
            l = l.strip()
            if l <> '':
                p.append(l)
            elif len(p) > 0:
                ps.append(SentenceSplitter(u" ".join(p)))
                p = []
        if len(p) > 0:
            ps.append(SentenceSplitter(u" ".join(p)))
        return ps


def to_lessons(sentences):
    backlog = []
    backlen = 0
    min_chars = Settings.get('min_chars')
    max_chars = Settings.get('max_chars')
    sweet_size = 3*(min_chars + max_chars) // 4
    
    for s in sentences:
        ssplit = []
        while len(s) > sweet_size:
            idx = s.find(' ', sweet_size)
            if idx == -1:
                break
            if idx != -1:
                ssplid.append(s[:idx])
                s = s[idx+1:]
        ssplit.append(s)
        for xs in ssplit:
            backlog.append(xs)
            backlen += len(xs)
            if backlen >= min_chars:
                yield u' '.join(backlog)
                backlog = []
                backlen = 0
    if backlen > 0:
        yield u' '.join(backlog)



class LessonGeneratorPlain(object):
    def __init__(self, words, per_lesson=12, repeats=4, width=85):
        while (0 < len(words) % per_lesson < per_lesson / 2):
            per_lesson += 1
        
        self.lessons = []
        wcopy = words[:]
        while wcopy:
            lesson = wcopy[0:per_lesson] * repeats
            wcopy[0:per_lesson] = []
            random.shuffle(lesson)
            self.lessons.append( #textwrap.fill(
                                                u' '.join(lesson)) #, width))

    def __iter__(self):
        return iter(self.lessons)





if __name__ == '__main__':
    import sys
    for x in LessonMiner(sys.argv[1]):
        print "--%s--" % x




