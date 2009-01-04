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

        self.setPalettes()

        self.connect(self, SIGNAL("textChanged()"), self.checkText)
        #self.setLineWrapMode(QTextEdit.NoWrap)
        self.connect(Settings, SIGNAL("change_quiz_wrong_fg"), self.setPalettes)
        self.connect(Settings, SIGNAL("change_quiz_wrong_bg"), self.setPalettes)
        self.connect(Settings, SIGNAL("change_quiz_right_fg"), self.setPalettes)
        self.connect(Settings, SIGNAL("change_quiz_right_bg"), self.setPalettes)
        self.target = None

    def sizeHint(self):
        return QSize(600, 10)

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.emit(SIGNAL("cancel"))
        return QTextEdit.keyPressEvent(self, e)

    def setPalettes(self):
        self.palettes = {
            'wrong': QPalette(Qt.black,
                Qt.lightGray, Qt.lightGray, Qt.darkGray, Qt.gray,
                Settings.getColor("quiz_wrong_fg"), Qt.white, Settings.getColor("quiz_wrong_bg"), Qt.yellow),
            'right': QPalette(Qt.black,
                Qt.lightGray, Qt.lightGray, Qt.darkGray, Qt.gray,
                Settings.getColor("quiz_right_fg"), Qt.yellow, Settings.getColor("quiz_right_bg"), Qt.yellow),
            'inactive': QPalette(Qt.black, Qt.lightGray, Qt.lightGray, Qt.darkGray,
                                 Qt.gray, Qt.black, Qt.lightGray)}
        self.setPalette(self.palettes['inactive'])

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
        return self.when[self.where]-self.when[0], self.where, self.times, self.mistake, self.getMistakes()

class Quizzer(QWidget):
    def __init__(self, *args):
        super(Quizzer, self).__init__(*args)

        self.result = QLabel()
        self.typer = Typer()
        self.label = WWLabel()
        self.result.setVisible(Settings.get("show_last"))
        #self.label.setFrameStyle(QFrame.Raised | QFrame.StyledPanel)
        #self.typer.setBuddy(self.label)
        #self.info = QLabel()
        self.connect(self.typer,  SIGNAL("done"), self.done)
        self.connect(self.typer,  SIGNAL("cancel"), SIGNAL("wantText"))
        self.connect(Settings, SIGNAL("change_typer_font"), self.readjust)
        self.connect(Settings, SIGNAL("change_show_last"), self.result.setVisible)

        self.text = ('','', 0, None)

        layout = QVBoxLayout()
        #layout.addWidget(self.info)
        #layout.addSpacing(20)
        layout.addWidget(self.result, 0, Qt.AlignRight)
        layout.addWidget(self.label, 1, Qt.AlignBottom)
        layout.addWidget(self.typer, 1)
        self.setLayout(layout)
        self.readjust()

    def readjust(self):
        f = Settings.getFont("typer_font")
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

        v2 = DB.fetchone("""select agg_median(wpm),agg_median(acc) from
            (select wpm,100.0*accuracy as acc from result order by w desc limit %d)""" % Settings.get('def_group_by'), (0.0, 100.0))
        self.result.setText("Last: %.1fwpm (%.1f%%), last 10 average: %.1fwpm (%.1f%%)"
            % ((12.0/spc, 100.0*accuracy) + v2))

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

        is_lesson = DB.fetchone("select discount from source where rowid=?", (None,), (self.text[1], ))[0]

        if Settings.get('use_lesson_stats') or not is_lesson:
            DB.executemany_('''insert into statistic
                (time,viscosity,w,count,mistakes,type,data) values (?,?,?,?,?,?,?)''', vals)
            DB.executemany_('insert into mistake (w,target,mistake,count) values (?,?,?,?)',
                    [(now, k[0], k[1], v) for k, v in mistakes.iteritems()])

        if is_lesson:
            mins = (Settings.get("min_lesson_wpm"), Settings.get("min_lesson_acc"))
        else:
            mins = (Settings.get("min_wpm"), Settings.get("min_acc"))

        if 12.0/spc < mins[0] or accuracy < mins[1]/100.0:
            self.setText(self.text)
        elif not is_lesson and Settings.get('auto_review'):
            ws = filter(lambda x: x[5] == 2, vals)
            if len(ws) == 0:
                self.emit(SIGNAL("wantText"))
                return
            ws.sort(key=lambda x: (x[4],x[0]), reverse=True)
            i = 0
            while ws[i][4] != 0:
                i += 1
            i += (len(ws) - i) // 4

            self.emit(SIGNAL("wantReview"), map(lambda x:x[6], ws[0:i]))
        else:
            self.emit(SIGNAL("wantText"))

