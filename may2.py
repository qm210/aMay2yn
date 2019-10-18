#########################################################################
## This is the PyQt rewrite from aMaySyn. It is aMay2yn.
## by QM / Team210
#########################################################################

import sys
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QAction, QVBoxLayout, QGroupBox, QSplitter, QFileDialog
from PyQt5.QtCore import Qt, pyqtSignal, QItemSelectionModel, QFile, QTextStream, QStringListModel
from PyQt5.QtGui import QFontDatabase, QIcon, QColor
from copy import deepcopy
from functools import partial
from os import path
from time import sleep
import json

from May2TrackWidget import May2TrackWidget
from May2PatternWidget import May2PatternWidget
from May2SynthWidget import May2SynthWidget
from may2Models import *
from may2Objects import *
from may2Style import noCrime

globalStateFile = 'global.state'

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setGeometry(320, 0, 1600, 1000)
        self.setWindowTitle('aMay2yn')
        self.setWindowIcon(QIcon('./qm_avatar32.gif'))

        self.initMenu()
        self.initLayouts()
        self.initSignals()
        self.initModelView()
        self.initState()
        self.setStyleSheet(noCrime)

        self.show()

        # print(QFontDatabase.addApplicationFont(':/RobotoMono-Regular.ttf')) # could redistribute, but then I should read about its LICENSE first

    def initLayouts(self):
        self.trackWidget = May2TrackWidget(self)
        self.trackGroupLayout = QVBoxLayout(self)
        self.trackGroupLayout.addWidget(self.trackWidget)
        self.trackGroup = QGroupBox(self)
        self.trackGroup.setLayout(self.trackGroupLayout)

        self.patternWidget = May2PatternWidget(self)
        self.patternGroupLayout = QVBoxLayout(self)
        self.patternGroupLayout.addWidget(self.patternWidget)
        self.patternGroup = QGroupBox(self)
        self.patternGroup.setLayout(self.patternGroupLayout)

        self.synthWidget = May2SynthWidget(self)
        self.synthGroupLayout = QVBoxLayout(self)
        self.synthGroupLayout.addWidget(self.synthWidget)
        self.synthGroup = QGroupBox(self)
        self.synthGroup.setLayout(self.synthGroupLayout)

        self.upperLayout = QSplitter(self)
        self.upperLayout.setOrientation(Qt.Vertical)
        self.upperLayout.addWidget(self.trackGroup)
        self.upperLayout.addWidget(self.patternGroup)

        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.addWidget(self.upperLayout, 6)
        self.mainLayout.addWidget(self.synthGroup, 1)

        self.centralWidget = QWidget(self)
        self.centralWidget.setLayout(self.mainLayout)
        self.setCentralWidget(self.centralWidget)


    def initMenu(self):
        loadAction = QAction(QIcon.fromTheme('document-open'), '&Load .mayson', self)
        loadAction.setShortcut('Ctrl+L')
        loadAction.triggered.connect(self.loadAndImportMayson)

        self.toolBar = self.addToolBar("Shit")
        self.toolBar.setMovable(False)
        self.toolBar.addAction(loadAction)


    def initSignals(self):
        self.trackWidget.moduleSelected.connect(self.loadModule)


    def initModelView(self):
        self.trackModel = TrackModel()
        self.patternModel = PatternModel()
        self.synthModel = QStringListModel()
        self.drumModel = QStringListModel()

        self.trackWidget.setTrackModel(self.trackModel)


    def initState(self): # mixing autoLoad functionality in here... for now.
        self.globalState = {
            'maysonFile': '',
            'lastDirectory': None,
        }
        self.state = {
            'autoReimport': False,
            'autoRender': False,
            'lastRendered': '',
            'writeWAV': False,
            'selectedTrack': 0,
            'selectedModule': 0,
            'extraTimeShift': 0,
        }
        self.info = {}
        self.patterns = []
        self.synths = []
        self.drumkit = []
        self.amaysyn = None
        self.fileObserver = None
        self.patternColors = {}

        loadGlobalState = {}
        try:
            file = open(globalStateFile, 'r')
            loadGlobalState = json.load(file)
            file.close()
        except FileNotFoundError:
            pass

        for key in loadGlobalState:
            self.globalState[key] = loadGlobalState[key]

        print("GLOBAL STATE", self.globalState, loadGlobalState)

        if 'maysonFile' not in self.globalState or self.globalState['maysonFile'] == '':
            self.loadAndImportMayson()
        else:
            self.importMayson()


    def applyStateToUI(self):
        pass # for now


    def loadAndImportMayson(self):
        name, _ = QFileDialog.getOpenFileName(self, 'Load MAYSON file', '', 'aMaySyn *.mayson(*.mayson)')
        if name == '':
            return
        self.globalState['maysonFile'] = name
        self.globalState['lastDirectory'] = path.dirname(name)
        self.state['title'], self.state['synFile'] = self.getTitleAndSynFromMayson(name)
        self.autoSave()
        self.importMayson()


    def importMayson(self):
        maysonData = {}
        try:
            file = open(self.globalState['maysonFile'], 'r')
            maysonData = json.load(file)
        except FileNotFoundError:
            print(f"{self.globalState['maysonFile']} could not be imported. make sure that it exists, or choose another one.")
            self.loadAndImportMayson()
        except json.decoder.JSONDecodeError:
            print(f"{self.globalState['maysonFile']} is changing right now, pause for 1 sec...")
            sleep(1)
            self.importMayson()
        finally:
            file.close()

        if maysonData == {}:
            return

        self.info = maysonData['info']
        if 'title' not in self.state or 'synFile' not in self.state:
            self.state['title'], self.state['synFile'] = self.getTitleAndSynFromMayson(self.globalState['maysonFile'])
        self.info.update({'title': self.state['title']})
        if self.amaysyn is not None:
            self.amaysyn.updateState(info = self.info)

        tracks, patterns, synths, drumkit = self.decodeAndProcessMaysonData(maysonData)
        self.trackModel.setTracks(tracks)
        self.patternModel.setPatterns(patterns)
        self.synthModel.setStringList(synths)
        self.drumModel.setStringList(drumkit)

        self.trackModel.layoutChanged.emit()
        self.patternModel.layoutChanged.emit()

        self.synthModel.layoutChanged.emit()
        self.drumModel.layoutChanged.emit()

        self.applyStateToUI()


    def getTitleAndSynFromMayson(self, maysonFile):
        synFile = '.'.join(maysonFile.split('.')[:-1]) + '.syn'
        title = '.'.join(path.basename(maysonFile).split('.')[:-1])
        return title, synFile

    def autoSave(self):
        self.autoSaveGlobals()
        print("fully implement autosave.... yet to do")

    def autoSaveGlobals(self):
        file =  open(globalStateFile, 'w')
        json.dump(self.globalState, file)
        file.close()


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


    def closeEvent(self, event):
        QApplication.quit()


    def decodeAndProcessMaysonData(self, data):
        """
        We have some cleaning up to do. I used to save whole patterns in the track modules.
        Now I just want to store the hash of each pattern, stored in pattern._hash
        But they have to match! (Until now, identity was maintained by unique names.)
        """
        patterns = []
        for encodedPattern in data['patterns']:
            pattern = decodePattern(encodedPattern)
            patterns.append(pattern)
            self.patternColors[pattern._hash] = self.randomColor()

        tracks = []
        for encodedTrack in data['tracks']:
            track = decodeTrack(encodedTrack)
            # now we take care of the module / pattern hash issue
            for module in track.modules:
                for pattern in patterns:
                    if module.patternName == pattern.name:
                        module.setPattern(pattern)
            tracks.append(track)

        synths = data['synths']
        drumkit = data['drumkit']

        return tracks, patterns, synths, drumkit


############################### HELPERS ############################

    # THE MOST IMPORTANT FUNCTION!
    def randomColor(self):
        colorHSV = QColor()
        colorHSV.setHsvF(random.uniform(.05,.95), .8, .88)
        return (colorHSV.red(), colorHSV.green(), colorHSV.blue())

    def getPatternColor(self, patternHash):
        if patternHash not in self.patternColors:
            print(f"WARNING: Requested a pattern color for nonexisting pattern hash {patternHash}. Returning random color. (But this should never happen!)")
            return self.randomColor()
        return self.patternColors[patternHash]


###################### MODEL FUNCTIONALITY ########################

    def loadModule(self, module):
        sanityCheck = 0
        for pattern in self.patternModel.patterns:
            if pattern._hash == module.patternHash:
                self.patternWidget.setPattern(pattern)
                self.patternWidget.update()
                sanityCheck += 1
        if sanityCheck != 1:
            print(f"wtf? something went wrong with trying to load {module.patternName} ({module.patternHash}), sanityCheck = {sanityCheck}")

###################################################################

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())