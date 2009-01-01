
from __future__ import with_statement, division

import os
import sys


# Get command-line --database argument before importing
# modules which count on database support
from Config import Settings

import optparse
opts = optparse.OptionParser()
opts.add_option("-d", "--database", metavar="FILE", help="use database FILE")
v = opts.parse_args()[0]

if v.database is not None:
    Settings.set('db_name', v.database)

from Data import DB
from Quizzer import Quizzer
from StatWidgets import StringStats
from TextManager import TextManager
from Performance import PerformanceHistory
from Config import PreferenceWidget
from Lesson import LessonGenerator
from Widgets.Database import DatabaseWidget

from PyQt4.QtCore import *
from PyQt4.QtGui import *

QApplication.setStyle('cleanlooks')


class TyperWindow(QMainWindow):
    def __init__(self, *args):
        super(TyperWindow, self).__init__(*args)

        self.setWindowTitle("Amphetype")

        tabs = QTabWidget()

        quiz = Quizzer()
        tabs.addTab(quiz, "Typer")

        tm = TextManager()
        self.connect(quiz, SIGNAL("wantText"), tm.nextText)
        self.connect(tm, SIGNAL("setText"), quiz.setText)
        self.connect(tm, SIGNAL("gotoText"), lambda: tabs.setCurrentIndex(0))
        tabs.addTab(tm, "Sources")

        ph = PerformanceHistory()
        self.connect(tm, SIGNAL("refreshSources"), ph.refreshSources)
        self.connect(quiz, SIGNAL("statsChanged"), ph.updateData)
        self.connect(ph, SIGNAL("setText"), quiz.setText)
        self.connect(ph, SIGNAL("gotoText"), lambda: tabs.setCurrentIndex(0))
        tabs.addTab(ph, "Performance")

        st = StringStats()
        self.connect(st, SIGNAL("lessonStrings"), lambda x: tabs.setCurrentIndex(4))
        tabs.addTab(st, "Analysis")

        lg = LessonGenerator()
        self.connect(st, SIGNAL("lessonStrings"), lg.addStrings)
        self.connect(lg, SIGNAL("newLessons"), lambda: tabs.setCurrentIndex(1))
        self.connect(lg, SIGNAL("newLessons"), tm.addTexts)
        self.connect(quiz, SIGNAL("wantReview"), lg.wantReview)
        self.connect(lg, SIGNAL("newReview"), tm.newReview)
        tabs.addTab(lg, "Lesson Generator")

        dw = DatabaseWidget()
        tabs.addTab(dw, "Database")

        pw = PreferenceWidget()
        tabs.addTab(pw, "Preferences")

        ab = AboutWidget()
        tabs.addTab(ab, "About/Help")

        self.setCentralWidget(tabs)

        tm.nextText()

    def sizeHint(self):
        return QSize(650, 400)

class AboutWidget(QTextBrowser):
    def __init__(self, *args):
        html = "about.html file missing!"
        try:
            html = open("about.html", "r").read()
        except:
            pass
        super(AboutWidget, self).__init__(*args)
        self.setHtml(html)
        self.setOpenExternalLinks(True)
        #self.setMargin(40)
        self.setReadOnly(True)

app = QApplication(sys.argv)

w = TyperWindow()
w.show()

app.exec_()

print "exit"
DB.commit()


