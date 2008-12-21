
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
        qf.fromString(Settings.get(k))
        return qf
    
    def set(self, k, v):
        p = self.get(k)
        if p == v:
            return
        self.setValue(k, QVariant(cPickle.dumps(v)))
        self.emit(SIGNAL("change"))
        self.emit(SIGNAL("change_" + k), v)



Settings = AmphSettings()


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
                    lambda x: Settings.set(setting, True if x == QCheckBox.On else False))

class PreferenceWidget(QWidget):
    def __init__(self):
        super(PreferenceWidget, self).__init__()
    
        self.font_lbl = QLabel()

        self.setLayout(AmphBoxLayout([
            ["Typer font is", self.font_lbl, AmphButton("Change...", self.setFont), None],
            ["Data is considered too old to be included in analysis after",
                SettingsEdit("history"), "days", None],
            ["Try to limit texts and lessons to between", SettingsEdit("min_chars"),
                "and", SettingsEdit("max_chars"), "characters", None], 
            ["When selecting easy/difficult texts, scan a sample of",
                SettingsEdit('num_rand'), "texts", None], 
            None,
            "... more shit to come here"
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
