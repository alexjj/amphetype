# -*- coding: UTF-8 -*-

from __future__ import with_statement, division


#import psyco
import platform
import collections
import time
import re

from Data import Statistic, DB
from Config import Settings

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from QtUtil import *


if platform.system() == "Windows":
    # hack hack, hackity hack
    timer = time.clock
    timer()
else:
    timer = time.time


class Typer(QTextEdit):
    def __init__(self, *args):
        super(Typer, self).__init__(*args)

        self.connect(self, SIGNAL("textChanged()"), self.checkText)
        self.palettes = {'wrong': QPalette(Qt.black), \
            'right': QPalette(Qt.white),
            'inactive': QPalette(Qt.black, Qt.lightGray, Qt.lightGray, Qt.darkGray, \
                                 Qt.gray, Qt.black, Qt.lightGray)}
        #self.setLineWrapMode(QTextEdit.NoWrap)
        self.target = None

    def sizeHint(self):
        return QSize(600, 10)

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.emit(SIGNAL("cancel"))
        return QTextEdit.keyPressEvent(self, e)

    def setTarget(self,  text):
        self.editflag = True
        self.target = text
        self.when = [0] * (len(self.target)+1)
        self.times = [0] * len(self.target)
        self.mistake = [False] * len(self.target)
        self.mistakes = {} #collections.defaultdict(lambda: [])
        self.where = 0
        self.clear()
        self.setPalette(self.palettes['inactive'])
        self.setText(self.getWaitText())
        self.selectAll()
        self.editflag = False

    def getWaitText(self):
        if Settings.get('req_space'):
            return "Press SPACE and then immediately start typing the text\n" + \
                    "Press ESCAPE to restart with a new text at any time"
        else:
            return "Press ESCAPE to restart with a new text at any time"

    def checkText(self):
        if self.target is None or self.editflag:
            return

        v = unicode(self.toPlainText())
        if self.when[0] == 0:
            space = len(v) > 0 and v[-1] == u" "
            req = Settings.get('req_space')

            self.editflag = True
            if space:
                self.when[0] = timer()
                self.clear()
                self.setPalette(self.palettes['right'])
            elif req:
                self.setText(self.getWaitText())
                self.selectAll()
            self.editflag = False

            if req or space:
                return
            else:
                self.when[0] = -1

        y = 0
        for y in xrange(min(len(v), len(self.target)), -1, -1):
            if v[0:y] == self.target[0:y]:
                break
        lcd = v[0:y]
        self.where = y

        if self.when[y] == 0 and y == len(v):
            self.when[y] = timer()
            if y > 0:
                self.times[y-1] = self.when[y] - self.when[y-1]

        if lcd == self.target:
            self.emit(SIGNAL("done"))
            return

        if y < len(v) and y < len(self.target):
            self.mistake[y] = True
            self.mistakes[y] = self.target[y] + v[y]

        if v == lcd:
            self.setPalette(self.palettes['right'])
        else:
            self.setPalette(self.palettes['wrong'])

    def getMistakes(self):
        inv = collections.defaultdict(lambda: 0)
        for p, m in self.mistakes.iteritems():
            inv[m] += 1
        return inv

    def getStats(self):
        if self.when[0] == -1:
            t = self.times[1:]
            t.sort(reverse=True)
            v = DB.fetchone('select time from statistic where type = 0 and data = ? order by rowid desc limit 1', (t[len(t)//5], ), (self.target[0], ))
            self.times[0] = v[0]
            self.when[0] = self.when[1] - self.times[0]
            print "interpolated as", self.times[0]
        return self.when[self.where]-self.when[0], self.where, self.times, self.mistake, self.getMistakes()

class Quizzer(QWidget):
    def __init__(self, *args):
        super(Quizzer, self).__init__(*args)

        self.typer = Typer()
        self.label = WWLabel()
        #self.label.setFrameStyle(QFrame.Raised | QFrame.StyledPanel)
        #self.typer.setBuddy(self.label)
        #self.info = QLabel()
        self.connect(self.typer,  SIGNAL("done"), self.done)
        self.connect(self.typer,  SIGNAL("cancel"), SIGNAL("wantText"))
        self.connect(Settings, SIGNAL("change_typer_font"), lambda x: self.readjust)

        self.text = ('','', 0, None)

        layout = QVBoxLayout()
        #layout.addWidget(self.info)
        #layout.addSpacing(20)
        layout.addWidget(self.label)
        layout.addWidget(self.typer)
        self.setLayout(layout)
        self.readjust()

    def readjust(self):
        f = QFont()
        f.fromString(Settings.get("typer_font"))
        self.label.setFont(f)
        self.typer.setFont(f)

    def setText(self, text):
        self.text = text
        self.label.setText(self.text[2].replace(u"\n", u"↵\n"))
        self.typer.setTarget(self.text[2])
        self.typer.setFocus()

    def done(self):
        now = time.time()
        elapsed, chars, times, mis, mistakes = self.typer.getStats()

        assert chars == len(self.text[2])

        accuracy = 1.0 - len(filter(None, mis)) / chars
        spc = elapsed / chars
        viscosity = sum(map(lambda x: ((x-spc)/spc)**2, times)) / chars

        DB.execute('insert into result (w,text_id,source,wpm,accuracy,viscosity) values (?,?,?,?,?,?)',
                   (now, self.text[0], self.text[1], 12.0/spc, accuracy, viscosity))

        self.emit(SIGNAL("statsChanged"))

        stats = collections.defaultdict(Statistic)
        visc = collections.defaultdict(Statistic)
        text = self.text[2]

        for c, t, m in zip(text, times, mis):
            stats[c].append(t, m)
            visc[c].append(((t-spc)/spc)**2)

        def gen_tup(s, e):
            perch = sum(times[s:e])/(e-s)
            visc = sum(map(lambda x: ((x-perch)/perch)**2, times[s:e]))/(e-s)
            return (text[s:e], perch, len(filter(None, mis[s:e])), visc)

        for tri, t, m, v in [gen_tup(i, i+3) for i in xrange(0, chars-2)]:
            stats[tri].append(t, m > 0)
            visc[tri].append(v)

        regex = re.compile(r"(\w|'(?![A-Z]))+(-\w(\w|')*)*")

        for w, t, m, v in [gen_tup(*x.span()) for x in regex.finditer(text) if x.end()-x.start() > 3]:
            stats[w].append(t, m > 0)
            visc[w].append(v)

        def type(k):
            if len(k) == 1:
                return 0
            elif len(k) == 3:
                return 1
            return 2

        vals = []
        for k, s in stats.iteritems():
            v = visc[k].median()
            vals.append( (s.median(), v*100.0, now, len(s), s.flawed(), type(k), k) )

        DB.executemany_('''insert into statistic (time,viscosity,w,count,mistakes,type,data) values (?,?,?,?,?,?,?)''', vals)
        DB.executemany_('insert into mistake (w,target,mistake,count) values (?,?,?,?)',
                    [(now, k[0], k[1], v) for k, v in mistakes.iteritems()])

        if 12.0/spc < Settings.get("min_wpm") or accuracy < Settings.get("min_acc")/100.0:
            self.setText(self.text)
        else:
            self.emit(SIGNAL("wantText"))

