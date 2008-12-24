
from __future__ import with_statement, division

import time
from itertools import *
import operator

from Data import DB
from Config import *
from QtUtil import *

import Widgets.Plotters as Plotters

from PyQt4.QtCore import *
from PyQt4.QtGui import *

#from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
#from matplotlib.figure import Figure



def dampen(n, data):
    last = []
    for x in data:
        last.append(x)
        if len(last) == n:
            yield (sum(last)/n)
            last.pop(0)

def with_halves(data):
    p = None
    for x in data:
        if p is not None:
            yield (x+p)/2
        yield x


def smooth(data):
    smooth = [1, 6, 15, 20]
    n = len(smooth)
    total = sum(smooth)

    res = [0] * n
    for i in range(n):
        res[i] = imap(lambda x:x*smooth[i], data)

    last = []
    for x in data:
        last.append(x)
        if len(last) == n:
            yield sum(imap(operator.mul, last, smooth))/total
        last.pop(0)



class ResultModel(AmphModel):
    def signature(self):
        self.source = None
        self.data_ = []
        self.hidden = 1
        return (["When", "Source", "WPM", "Accuracy", "Viscosity"],
                [self.formatWhen, None, "%.1f", "%.1f%%", "%.1f"])

    def populateData(self, idx):
        if len(idx) > 0:
            return []

        return self.data_

    def setData(self, d):
        self.data_ = d
        self.reset()

    def formatWhen(self, w):
        d = time.time() - w

        if d < 60.0:
            return "%.1fs" % d
        d /= 60.0
        if d < 60.0:
            return "%.1fm" % d
        d /= 60.0
        if d < 24.0:
            return "%.1fh" % d
        d /= 24.0
        if d < 7.0:
            return "%.1fd" % d
        d /= 7.0
        if d < 52.0:
            return "%.1fw" % d
        d /= 52.0
        return "%.1fy" % d


class PerformanceHistory(QWidget):
    def __init__(self, *args):
        super(PerformanceHistory, self).__init__(*args)

        self.plotcol = 3
        self.plot = Plotters.Plotter()

        self.editflag = False
        self.model = ResultModel()

        self.cb_source = QComboBox()
        self.refreshSources()
        self.connect(self.cb_source, SIGNAL("currentIndexChanged(int)"), self.updateData)

        t = AmphTree(self.model)
        t.setUniformRowHeights(True)
        t.setRootIsDecorated(False)
        t.setIndentation(0)
        self.connect(t, SIGNAL("doubleClicked(QModelIndex)"), self.doubleClicked)
        self.connect(Settings, SIGNAL('change_graph_what'), self.updateGraph)
        self.connect(Settings, SIGNAL('change_show_xaxis'), self.updateGraph)

        self.setLayout(AmphBoxLayout([
                ["Show", SettingsEdit("perf_items"), "items for",
                    SettingsCombo('lesson_stats', ["both", "texts", "lessons"]), "limited to", self.cb_source,
                    "and group by", SettingsCombo('perf_group_by', ["single sessions", "10 sessions", "days"]),
                    None, AmphButton("Update", self.updateData)],
                (t, 1),
                ["Plot", SettingsCombo('graph_what', ((3, 'WPM'), (4, 'accuracy'), (5, 'viscosity'))),
                    SettingsCheckBox("show_xaxis", "Show X-axis"), None],
                (self.plot, 1)
            ]))

        self.connect(Settings, SIGNAL("change_perf_items"), self.updateData)
        self.connect(Settings, SIGNAL("change_perf_group_by"), self.updateData)
        self.connect(Settings, SIGNAL("change_lesson_stats"), self.updateData)

    def updateGraph(self):
        pc = Settings.get('graph_what')
        y = map(lambda x:x[pc], self.model.rows)
        y.reverse()

        self.plot.setScene(Plotters.Plot(y))

    def refreshSources(self):
        self.editflag = True
        self.cb_source.clear()
        self.cb_source.addItem("<ALL>")
        self.cb_source.addItem("<LAST TEXT>")

        for id, v in DB.fetchall('select rowid,abbreviate(name,30) from source order by name'):
            self.cb_source.addItem(v, QVariant(id))
        self.editflag = False

    def updateData(self, *args):
        if self.editflag:
            return
        where = []
        if self.cb_source.currentIndex() <= 0:
            pass
        elif self.cb_source.currentIndex() == 1:
            where.append('r.text_id = (select text_id from result order by w desc limit 1)')
        else:
            s = self.cb_source.itemData(self.cb_source.currentIndex())
            where.append('r.source = %d' % s.toInt()[0])

        s = Settings.get('lesson_stats')
        if s == 0:
            pass
        elif s == 1: # texts
            where.append('s.discount is null')
        else: # s == 2: # lessons
            where.append('s.discount is not null')

        if len(where) > 0:
            where = 'where ' + ' and '.join(where)
        else:
            where = ""

        g = Settings.get('perf_group_by')
        if g == 0: # no grouping
            sql = '''select text_id,w,s.name,wpm,100.0*accuracy,viscosity from result as r
                left join source as s on (r.source = s.rowid)
                %s %s
                order by w desc limit %d'''
        else:
            sql = '''select agg_first(text_id),avg(r.w) as w,count(distinct r.source) || ' source(s)',agg_median(r.wpm),
                        100.0*agg_median(r.accuracy),agg_median(r.viscosity)
                from result as r
                left join source as s on (r.source = s.rowid)
                %s %s
                order by w desc limit %d'''

        group = ''
        if g == 1: # by 10
            DB.resetCounter()
            group = "group by cast(counter()/10 as int)"
        elif g == 2: # by days
            group = "group by cast((r.w+4*3600)/86400 as int)"

        n = Settings.get("perf_items")

        sql = sql % (where, group, n)

        self.model.setData(map(list, DB.fetchall(sql)))
        self.updateGraph()

    def doubleClicked(self, idx):
        r = self.model.rows[idx.row()]

        v = DB.fetchone('select id,source,text from text where id = ?', None, (r[0], ))
        if v == None:
            return # silently ignore

        self.emit(SIGNAL("setText"), v)
        self.emit(SIGNAL("gotoText"))
