#########################################################################
## This is the PyQt rewrite from aMaySyn. It is aMay2yn.
## by QM / Team210
#########################################################################

import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QGroupBox, QSplitter
from PyQt5.QtCore import Qt, pyqtSignal, QItemSelectionModel, QFile, QTextStream
from copy import deepcopy
from functools import partial
from os import path
import json

from May2TrackWidget import *
from May2PatternWidget import *
from May2SynthWidget import *


class MainWindow(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle('aMaynWindow')
        self.setGeometry(320, 0, 1600, 1000)
        self.show()
        self.initLayouts()
        self.initSignals()
        self.initModelView()
        self.initDefaults()

    def initLayouts(self):
        self.trackWidget = May2TrackWidget(self)
        self.trackGroupLayout = QVBoxLayout(self)
        self.trackGroupLayout.addWidget(self.trackWidget)
        self.trackGroup = QGroupBox('Track Shit', self)
        self.trackGroup.setLayout(self.trackGroupLayout)

        self.patternWidget = May2PatternWidget(self)
        self.patternGroupLayout = QVBoxLayout(self)
        self.patternGroupLayout.addWidget(self.patternWidget)
        self.patternGroup = QGroupBox('Pattern Shit', self)
        self.patternGroup.setLayout(self.patternGroupLayout)

        self.synthWidget = May2SynthWidget(self)
        self.synthGroupLayout = QVBoxLayout(self)
        self.synthGroupLayout.addWidget(self.synthWidget)
        self.synthGroup = QGroupBox('Synthi / Render Shit', self)
        self.synthGroup.setLayout(self.synthGroupLayout)

        self.upperLayout = QSplitter(self)
        self.upperLayout.setOrientation(Qt.Vertical)
        self.upperLayout.addWidget(self.trackGroup)
        self.upperLayout.addWidget(self.patternGroup)
        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.addWidget(self.upperLayout, 6)
        self.mainLayout.addWidget(self.synthGroup, 1)
        self.setLayout(self.mainLayout)


    def initSignals(self):
        pass


    def initModelView(self):
        pass


    def initDefaults(self):
        pass


    def initData(self):
        pass


    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Escape:
            self.close()

        elif key == Qt.Key_F9:
            self.trackWidget.debugOutput()

        elif key == Qt.Key_F10:
            self.patternWidget.debugOutput()

        elif key == Qt.Key_F11:
            self.synthWidget.debugOutput()




if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())