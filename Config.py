
from __future__ import with_statement

import cPickle
from QtUtil import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *


class AmphSettings(QSettings):

    defaults = {
            "typer_font": str(QFont("Arial", 14).toString()),
            "min_wpm": 40.0,
            "min_acc": 80.0,
            "history": 30.0,
            "min_chars": 220,
            "max_chars": 600,
            "lesson_stats": 0,
            "perf_group_by": 0,
            "perf_items": 100,
            "text_regex": r"",
            "select_method": 0,
            "num_rand": 50,
            "graph_what": 3,
            "req_space": True,
            "show_last": True,
            "show_xaxis": False,
            "chrono_x": False,
            "quiz_right_fg": "#000000",
            "quiz_right_bg": "#ffffff",
            "quiz_wrong_fg": "#ffffff",
            "quiz_wrong_bg": "#000000",

            "ana_which": "wpm asc",
            "ana_what": 0,
            "ana_many": 30,
            "ana_count": 1,

            "gen_copies": 3,
            "gen_take": 2,
            "gen_mix": 'c',
            #"gen_stats": False,
            "str_clear": 's',
            "str_extra": 10,
            "str_what": 'e'
        }

    def __init__(self, *args):
        super(AmphSettings, self).__init__(QSettings.IniFormat, QSettings.UserScope, "Amphetype", "Amphetype")

    def get(self, k):
        v = self.value(k)
        if not v.isValid():
            return self.defaults[k]
        return cPickle.loads(str(v.toString()))

    def getFont(self, k):
        qf = QFont()
        qf.fromString(self.get(k))
        return qf

    def getColor(self, k):
        return QColor(self.get(k))

    def set(self, k, v):
        p = self.get(k)
        if p == v:
            return
        self.setValue(k, QVariant(cPickle.dumps(v)))
        self.emit(SIGNAL("change"))
        self.emit(SIGNAL("change_" + k), v)



Settings = AmphSettings()


class SettingsColor(AmphButton):
    def __init__(self, key, text):
        self.key_ = key
        super(SettingsColor, self).__init__(Settings.get(key), self.pickColor)
        self.updateIcon()

    def pickColor(self):
        color = QColorDialog.getColor(Settings.getColor(self.key_), self)
        if not color.isValid():
            return
        Settings.set(self.key_, unicode(color.name()))
        self.updateIcon()

    def updateIcon(self):
        pix = QPixmap(32, 32)
        c = Settings.getColor(self.key_)
        pix.fill(c)
        self.setText(Settings.get(self.key_))
        self.setIcon(QIcon(pix))



class SettingsEdit(AmphEdit):
    def __init__(self, setting):
        val = Settings.get(setting)
        typ = type(val)
        validator = None
        if isinstance(val, float):
            validator = QDoubleValidator
        elif isinstance(val, (int, long)):
            validator = QIntValidator
        if validator is None:
            self.fmt = lambda x: x
        else:
            self.fmt = lambda x: "%g" % x
        super(SettingsEdit, self).__init__(
                            self.fmt(val),
                            lambda: Settings.set(setting, typ(self.text())),
                            validator=validator)
        self.connect(Settings, SIGNAL("change_" + setting), lambda x: self.setText(self.fmt(x)))


class SettingsCombo(QComboBox):
    def __init__(self, setting, lst, *args):
        super(SettingsCombo, self).__init__(*args)

        prev = Settings.get(setting)
        self.idx2item = []
        for i in range(len(lst)):
            if isinstance(lst[i], basestring):
                # not a tuple, use index as key
                k, v = i, lst[i]
            else:
                k, v = lst[i]
            self.addItem(v)
            self.idx2item.append(k)
            if k == prev:
                self.setCurrentIndex(i)

        self.connect(self, SIGNAL("activated(int)"),
                    lambda x: Settings.set(setting, self.idx2item[x]))

        #self.connect(Settings, SIGNAL("change_" + setting),
        #            lambda x: self.setCurrentIndex(self.item2idx[x]))

class SettingsCheckBox(QCheckBox):
    def __init__(self, setting, *args):
        super(SettingsCheckBox, self).__init__(*args)
        self.setCheckState(Qt.Checked if Settings.get(setting) else Qt.Unchecked)
        self.connect(self, SIGNAL("stateChanged(int)"),
                    lambda x: Settings.set(setting, True if x == Qt.Checked else False))

class PreferenceWidget(QWidget):
    def __init__(self):
        super(PreferenceWidget, self).__init__()

        self.font_lbl = QLabel()

        self.setLayout(AmphBoxLayout([
            ["Typer font is", self.font_lbl, AmphButton("Change...", self.setFont), None],
            ["Data is considered too old to be included in analysis after",
                SettingsEdit("history"), "days.", None],
            ["Try to limit texts and lessons to between", SettingsEdit("min_chars"),
                "and", SettingsEdit("max_chars"), "characters.", None],
            ["When selecting easy/difficult texts, scan a sample of",
                SettingsEdit('num_rand'), "texts.", None],
            [SettingsCheckBox('req_space', "Make SPACE mandatory before each session."),
                ("(Unchecking this and not starting texts by pressing space will reduce the accuracy (very slightly) of the measurements for the first key, word, and trigram of every text.)\n", 1)],
            [SettingsCheckBox('show_last', "Show last result(s) above text in the Typer.")],
            [AmphGridLayout([
                ["Typer Colors", "Text Color", "Background"],
                ["Correct Input", SettingsColor('quiz_right_fg', "Foreground"),
                        SettingsColor('quiz_right_bg', "Background")],
                ["Wrong Input", SettingsColor('quiz_wrong_fg', "Foreground"),
                        SettingsColor('quiz_wrong_bg', "Background")],
                [1+1j,1+2j,2+1j,2+2j]
            ]), None],
            None
        ]))

        self.updateFont()

    def setFont(self):
        font, ok = QFontDialog.getFont(Settings.getFont('typer_font'), self)
        Settings.set("typer_font", unicode(font.toString()))
        self.updateFont()

    def updateFont(self):
        self.font_lbl.setText(Settings.get("typer_font"))
        qf = Settings.getFont('typer_font')
        self.font_lbl.setFont(qf)
