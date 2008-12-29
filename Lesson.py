
from __future__ import with_statement, division

from itertools import *
import random
import time
import codecs
from Data import DB

try:
    import editdist
except ImportError:
    import editdist_fake as editdist

import Text
from Config import *
from QtUtil import *


class StringListWidget(QTextEdit):
    def __init__(self, *args):
        super(StringListWidget, self).__init__(*args)
        self.setWordWrapMode(QTextOption.WordWrap)
        self.setAcceptRichText(False)
        self.delayflag = 0
        self.connect(self, SIGNAL("textChanged()"), self.textChanged)

    def addList(self, lst):
        self.append(u' '.join(lst))

    def getList(self):
        return unicode(self.toPlainText()).split()

    def addFromTyped(self):
        words = [x[0] for x in DB.fetchall('select distinct data from statistic where type = 2 order by random()')]
        self.filterWords(words)

    def addFromFile(self):
        filen = QFileDialog.getOpenFileName()
        if filen == u'':
            return
        try:
            with codecs.open(filen, "r", "utf_8_sig") as f:
                words = f.read().split()
        except Exception, e:
            QMessageBox.warning(self, "Couldn't Read File", str(e))
            return
        random.shuffle(words)

        self.filterWords(words)

    def filterWords(self, words):
        n = Settings.get('str_extra')
        w = Settings.get('str_what')
        if w == 'r': # random
            pass
        else:
            control = self.getList()
            if len(control) == 0:
                return
            if w == 'e': # encompassing
                stream = map(lambda x: (sum([x.count(c) for c in control]), x), words)
                #print "str:", list(stream)[0:10]
                preres = list(islice(ifilter(lambda x: x[0]>0, stream), 4*n))
                #print "pre:", preres
                preres.sort(key=lambda x: x[0], reverse=True)
                words = map(lambda x: x[1], preres)
            else: # similar
                words = ifilter(lambda x:
                    0 < min([
                            editdist.distance(x.encode('latin1', 'replace'),
                                              y.encode('latin1', 'replace'))/max(len(y), len(x))
                                for y in control]) < .26, words)

        if Settings.get('str_clear') == 'r': # replace = clear
            self.clear()

        self.addList(islice(words, n))

    def textChanged(self):
        if self.delayflag > 0:
            self.delayflag += 1
            return

        self.emit(SIGNAL("updated"))
        self.delayflag = 1
        QTimer.singleShot(500, self.revertFlag)

    def revertFlag(self):
        if self.delayflag > 1:
            self.emit(SIGNAL("updated"))
        self.delayflag = 0

class LessonGenerator(QWidget):
    def __init__(self, *args):
        super(LessonGenerator, self).__init__(*args)

        self.strings = StringListWidget()
        self.sample = QTextEdit()
        self.sample.setWordWrapMode(QTextOption.WordWrap)
        self.sample.setAcceptRichText(False)
        self.les_name = QLineEdit()

        self.setLayout(AmphBoxLayout([
            ["Welcome to Amphetype's automatic lesson generator!"],
            [" You can retrieve a list of words/keys/trigrams to practice from the Analysis tab, import from an external file, or even type in your own (separated by space).\n"""],
            10,
            ["In generating lessons, I will make", SettingsEdit("gen_copies"),
                "copies the list below and divide them into sublists of size",
                SettingsEdit("gen_take"), "(0 for all).", None],
            ["I will then", SettingsCombo("gen_mix", [('c',"concatenate"), ('m',"commingle")]),
                "corresponding sublists into atomic building blocks which are fashioned into lessons according to your lesson size preferences.",  None],
            [
                ([
                    (self.strings, 1),
                    [SettingsCombo('str_clear', [('s', "Supplement"), ('r', "Replace")]), "list with",
                        SettingsEdit("str_extra"),
                        SettingsCombo('str_what', [('e','encompassing'), ('s','similar'), ('r','random')]),
                        "words from", AmphButton("a file", self.strings.addFromFile),
                        "or", AmphButton("analysis database", self.strings.addFromTyped), None]
                ], 1),
                ([
                    "Lessons (separated by empty lines):",
                    (self.sample, 1),
                    [None, AmphButton("Add to Sources", self.acceptLessons), "with name", self.les_name]
                ], 1)
            ]
        ]))

        self.connect(Settings, SIGNAL("change_gen_take"), self.generatePreview)
        self.connect(Settings, SIGNAL("change_gen_copies"), self.generatePreview)
        self.connect(Settings, SIGNAL("change_gen_mix"), self.generatePreview)
        self.connect(self.strings, SIGNAL("updated"), self.generatePreview)

    def generatePreview(self):
        words = self.strings.getList()
        copies = Settings.get('gen_copies')
        take = Settings.get('gen_take')
        mix = Settings.get('gen_mix')

        sentences = []
        while len(words) > 0:
            sen = words[0:take] * copies
            words[0:take] = []

            if mix == 'm': # mingle
                random.shuffle(sen)
            sentences.append(u' '.join(sen))

        self.sample.clear()
        for x in Text.to_lessons(sentences):
            self.sample.append(x + "\n\n")

    def acceptLessons(self):

        name = unicode(self.les_name.text())
        if not name:
            name = "<Lesson %s>" % time.strftime("%y-%m-%d %H:%M")

        lessons = filter(None, [x.strip() for x in unicode(self.sample.toPlainText()).split("\n\n")])

        if len(lessons) == 0:
            QMessageBox.information(self, "No Lessons", "Generate some lessons before you try to add them!")
            return

        self.emit(SIGNAL("newLessons"), name, lessons, True)

    def addStrings(self, *args):
        self.strings.addList(*args)

