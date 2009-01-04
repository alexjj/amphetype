
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


def dampen(x, n=10):
    ret = []
    s = sum(x[0:n])
    q = 1/n
    for i in range(n, len(x)):
        ret.append(s*q)
        s += x[i] - x[i-n]
    return ret


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
        self.connect(Settings, SIGNAL('change_chrono_x'), self.updateGraph)
        self.connect(Settings, SIGNAL("change_dampen_graph"), self.updateGraph)

        self.setLayout(AmphBoxLayout([
                ["Show", SettingsEdit("perf_items"), "items from",
                    #SettingsCombo('lesson_stats', ["both", "texts", "lessons"]), "limited to",
                    self.cb_source,
                    "and group by", SettingsCombo('perf_group_by',
                        ["<no grouping>", "%d sessions" % Settings.get('def_group_by'), "sitting", "day"]),
                    None, AmphButton("Update", self.updateData)],
                (t, 1),
                ["Plot", SettingsCombo('graph_what', ((3, 'WPM'), (4, 'accuracy'), (5, 'viscosity'))),
                    SettingsCheckBox("show_xaxis", "Show X-axis"),
                    SettingsCheckBox("chrono_x", "Use time-scaled X-axis"),
                    SettingsCheckBox("dampen_graph", "Dampen graph values"), None],
                (self.plot, 1)
            ]))

        self.connect(Settings, SIGNAL("change_perf_items"), self.updateData)
        self.connect(Settings, SIGNAL("change_perf_group_by"), self.updateData)
        self.connect(Settings, SIGNAL("change_lesson_stats"), self.updateData)

    def updateGraph(self):
        pc = Settings.get('graph_what')
        y = map(lambda x:x[pc], self.model.rows)

        if Settings.get("chrono_x"):
            x = map(lambda x:x[1], self.model.rows)
        else:
            x = range(len(y))
            x.reverse()

        if Settings.get("dampen_graph"):
            y = dampen(y, Settings.get('dampen_average'))
            x = dampen(x, Settings.get('dampen_average'))

        self.p = Plotters.Plot(x, y)
        self.plot.setScene(self.p)

    def refreshSources(self):
        self.editflag = True
        self.cb_source.clear()
        self.cb_source.addItem("<ALL>")
        self.cb_source.addItem("<LAST TEXT>")
        self.cb_source.addItem("<ALL TEXTS>")
        self.cb_source.addItem("<ALL LESSONS>")

        for id, v in DB.fetchall('select rowid,abbreviate(name,30) from source order by name'):
            self.cb_source.addItem(v, QVariant(id))
        self.editflag = False

    def updateData(self, *args):
        if self.editflag:
            return
        where = []
        if self.cb_source.currentIndex() <= 0:
            pass
        elif self.cb_source.currentIndex() == 1: # last text
            where.append('r.text_id = (select text_id from result order by w desc limit 1)')
        elif self.cb_source.currentIndex() == 2: # all texts
            where.append('s.discount is null')
        elif self.cb_source.currentIndex() == 3: # all lessons texts
            where.append('s.discount is not null')
        else:
            s = self.cb_source.itemData(self.cb_source.currentIndex())
            where.append('r.source = %d' % s.toInt()[0])

        if len(where) > 0:
            where = 'where ' + ' and '.join(where)
        else:
            where = ""

        g = Settings.get('perf_group_by')
        if g == 0: # no grouping
            sql = '''select text_id,w,s.name,wpm,100.0*accuracy,viscosity
                from result as r left join source as s on (r.source = s.rowid)
                %s %s
                order by w desc limit %d'''
        elif g:
            sql = '''select agg_first(text_id),avg(r.w) as w,count(r.rowid) || ' result(s)',agg_median(r.wpm),
                        100.0*agg_median(r.accuracy),agg_median(r.viscosity)
                from result as r left join source as s on (r.source = s.rowid)
                %s %s
                order by w desc limit %d'''

        group = ''
        if g == 1: # by Settings.get('def_group_by')
            DB.resetCounter()
            gn = Settings.get('def_group_by')
            if gn <= 1:
                gn = 1
            group = "group by cast(counter()/%d as int)" % gn
        elif g == 2: # by sitting
            mis = Settings.get('minutes_in_sitting') * 60.0
            DB.resetTimeGroup()
            group = "group by time_group(%f, r.w)" % mis
        elif g == 3: # by day
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
