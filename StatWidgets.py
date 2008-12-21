
from __future__ import division, with_statement

import time

from Data import DB
from QtUtil import *
from Text import LessonGeneratorPlain
from Config import *

from PyQt4.QtCore import *
from PyQt4.QtGui import *



class WordModel(AmphModel):
    def signature(self):
        self.words = []
        return (["Item", "Speed", "Accuracy", "Viscosity", "Count", "Mistakes", "Impact"],
                [None, "%.1f wpm", "%.1f%%", "%.1f", None, None, "%.1f"])

    def populateData(self, idx):
        if len(idx) != 0:
            return []

        return self.words

    def setData(self, words):
        self.words = map(list, words)
        self.reset()




class StringStats(QWidget):
    def __init__(self, *args):
        super(StringStats, self).__init__(*args)

        self.model = WordModel()
        tw = AmphTree(self.model)
        tw.setIndentation(0)
        tw.setUniformRowHeights(True)
        tw.setRootIsDecorated(False)
        self.stats = tw

        ob = SettingsCombo('ana_which', [
                    ('wpm asc', 'slowest'),
                    ('wpm desc', 'fastest'),
                    ('viscosity asc', 'least fluid'),
                    ('viscosity asc', 'most fluid'),
                    ('accuracy asc', 'least accurate'),
                    ('misses desc', 'most mistyped'),
                    ('total desc', 'most common'),
                    ('damage desc', 'most damaging'),
                    ])

        wc = SettingsCombo('ana_what', ['keys', 'trigrams', 'words'])
        lim = SettingsEdit('ana_many')
        self.w_count = SettingsEdit('ana_count')

        self.connect(Settings, SIGNAL("change_ana_which"), self.update)
        self.connect(Settings, SIGNAL("change_ana_what"), self.update)
        self.connect(Settings, SIGNAL("change_ana_many"), self.update)
        self.connect(Settings, SIGNAL("change_ana_count"), self.update)
        self.connect(Settings, SIGNAL("history"), self.update)

        self.setLayout(AmphBoxLayout([
                ["Display statistics about the", ob, wc, None, AmphButton("Update List", self.update)],
                ["Limit list to", lim, "items and don't show items with a count less than", self.w_count,
                    None, AmphButton("Send List to Lesson Generator",
                         lambda: self.emit(SIGNAL("lessonStrings"), [x[0] for x in self.model.words]))],
                (self.stats, 1)
            ]))

    def update(self, *arg):

        ord = Settings.get('ana_which')
        cat = Settings.get('ana_what')
        limit = Settings.get('ana_many')
        count = Settings.get('ana_count')
        hist = time.time() - Settings.get('history') * 86400.0

        sql = """select data,12.0/time as wpm,
            100.0-100.0*misses/cast(total as real) as accuracy,
            viscosity,total,misses,
            total*time*time*(1.0+misses/total) as damage
                from
                    (select data,agg_median(time) as time,agg_median(viscosity) as viscosity,
                    sum(count) as total,sum(mistakes) as misses
                    from statistic where w >= ? and type = ? group by data)
                where total >= ?
                order by %s limit %d""" % (ord, limit)

        self.model.setData(DB.fetchall(sql, (hist, cat, count)))

