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
from random import uniform
from numpy import clip
from shutil import move, copyfile
import json

from May2TrackWidget import May2TrackWidget
from May2PatternWidget import May2PatternWidget
from May2SynthWidget import May2SynthWidget
from may2TrackModel import TrackModel
from may2PatternModel import PatternModel
from may2Objects import decodeTrack, decodePattern
from may2Style import notACrime

globalStateFile = 'global.state'
defaultSynFile = 'default.syn'

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setGeometry(320, 0, 1600, 1000)
        self.setWindowTitle('aMay2yn')
        self.setWindowIcon(QIcon('./qm_avatar32.gif'))

        self.initToolBar()
        self.initLayouts()
        self.initSignals()
        self.initModelView()
        self.initState()
        self.setStyleSheet(notACrime)

        self.show()

        self.shiftPressed = False
        self.ctrlPressed = False
        self.altPressed = False

        # print(QFontDatabase.addApplicationFont(':/RobotoMono-Regular.ttf')) # could redistribute, but then I should read about its LICENSE first

    def initLayouts(self):
        self.trackWidget = May2TrackWidget(self)
        self.trackGroupLayout = QVBoxLayout()
        self.trackGroupLayout.addWidget(self.trackWidget)
        self.trackGroup = QGroupBox()
        self.trackGroup.setLayout(self.trackGroupLayout)

        self.patternWidget = May2PatternWidget(self)
        self.patternGroupLayout = QVBoxLayout()
        self.patternGroupLayout.addWidget(self.patternWidget)
        self.patternGroup = QGroupBox()
        self.patternGroup.setLayout(self.patternGroupLayout)

        self.synthWidget = May2SynthWidget(self)
        self.synthGroupLayout = QVBoxLayout()
        self.synthGroupLayout.addWidget(self.synthWidget)
        self.synthGroup = QGroupBox()
        self.synthGroup.setLayout(self.synthGroupLayout)

        self.upperLayout = QSplitter(self)
        self.upperLayout.setOrientation(Qt.Vertical)
        self.upperLayout.addWidget(self.trackGroup)
        self.upperLayout.addWidget(self.patternGroup)
        self.upperLayout.setSizes([400,500])

        self.mainLayout = QVBoxLayout()
        self.mainLayout.addWidget(self.upperLayout, 6)
        self.mainLayout.addWidget(self.synthGroup, 1)

        self.centralWidget = QWidget(self)
        self.centralWidget.setLayout(self.mainLayout)
        self.setCentralWidget(self.centralWidget)


    def initToolBar(self):
        self.toolBar = self.addToolBar("Shit")
        self.toolBar.setMovable(False)

        loadAction = QAction(QIcon.fromTheme('document-open'), 'Load .mayson', self)
        loadAction.setShortcut('Ctrl+L')
        loadAction.triggered.connect(self.loadAndImportMayson)
        saveAction = QAction(QIcon.fromTheme('document-save'), 'Save .mayson', self)
        saveAction.setShortcut('Ctrl+S')
        saveAction.triggered.connect(self.exportMayson)
        undoAction = QAction(QIcon.fromTheme('edit-undo'), 'Undo', self)
        undoAction.setShortcut('Ctrl+Z')
        undoAction.triggered.connect(partial(self.loadUndoStep, relativeStep = +1))
        redoAction = QAction(QIcon.fromTheme('edit-redo'), 'Redo', self)
        redoAction.setShortcut('Shift+Ctrl+Z')
        redoAction.triggered.connect(partial(self.loadUndoStep, relativeStep = -1))
        settingsAction = QAction(QIcon.fromTheme('preferences-system'), 'Settings', self)
        settingsAction.triggered.connect(self.openSettingsDialog)
        renderModuleAction = QAction(QIcon.fromTheme('media-playback-start'), 'RenderModule', self)
        renderModuleAction.setShortcut('Ctrl+T')
        renderModuleAction.triggered.connect(self.renderModule)
        renderTrackAction = QAction(QIcon.fromTheme('media-playback-start'), 'RenderTrack', self)
        renderTrackAction.setShortcut('Ctrl+Enter')
        renderTrackAction.triggered.connect(self.renderTrack)

        self.toolBar.addAction(loadAction)
        self.toolBar.addAction(saveAction)
        self.toolBar.addSeparator()
        self.toolBar.addAction(undoAction)
        self.toolBar.addAction(redoAction)
        self.toolBar.addAction(settingsAction)
        self.toolBar.addSeparator()
        self.toolBar.addAction(renderModuleAction)
        self.toolBar.addAction(renderTrackAction)


    def initSignals(self):
        self.trackWidget.moduleSelected.connect(self.loadModule)
        self.trackWidget.trackChanged.connect(self.trackChanged)
        self.trackWidget.activated.connect(partial(self.toggleActivated, activateTrack = True))
        self.patternWidget.activated.connect(partial(self.toggleActivated, activatePattern = True))
        self.patternWidget.patternChanged.connect(self.patternChanged)

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

        if 'maysonFile' not in self.globalState or self.globalState['maysonFile'] == '':
            self.loadAndImportMayson()
        else:
            self.importMayson()

        self.undoStack = []
        self.undoStep = 0
        self.pushUndoStack()


    def toggleActivated(self, activateTrack = False, activatePattern = False, activateSynth = False):
        self.trackGroup.setObjectName('activated' if activateTrack else '')
        self.trackWidget.active = activateTrack
        self.trackGroup.style().polish(self.trackGroup)

        self.patternGroup.setObjectName('activated' if activatePattern else '')
        self.patternWidget.active = activatePattern
        self.patternGroup.style().polish(self.patternGroup)

        self.synthGroup.setObjectName('activated' if activatePattern else '')
        self.synthWidget.active = activateSynth
        self.synthGroup.style().polish(self.synthGroup)


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

        self.setModelsFromData(maysonData)
        self.shufflePatternColors()

        self.trackWidget.activate()
        tracks = self.trackModel.tracks
        if tracks:
            if tracks[0].modules:
                self.trackWidget.select(tracks[0], tracks[0].modules[0])
            else:
                self.trackWidget.select(tracks[0])

    def exportMayson(self):
        json_filename = f"{self.state['title']}.mayson"
        data = {
            'state': self.state,
            'info': self.info,
            'tracks': self.trackModel.tracks,
            'patterns': self.patternModel.patterns,
            'synths': self.synthModel.stringList(),
            'drumkit': self.drumModel.stringList(),
        }
        fn = open(json_filename, 'w')
        json.dump(data, fn, default = lambda obj: obj.__dict__)
        fn.close()
        self.ensureSynFile()

    def ensureSynFile(self):
        synfile = self.getInfo('title') + '.syn'
        if not path.exists(synfile):
            copyfile(self.defaultSynFile, synfile)
            print(f"Copied {self.defaultSynFile} to {synfile}. For future reference.")

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
        self.setModifiers(event)

        if key == Qt.Key_Escape:
            self.close()
        elif key == Qt.Key_F9:
            self.trackWidget.debugOutput()
        elif key == Qt.Key_F10:
            self.patternWidget.debugOutput()
        elif key == Qt.Key_F11:
            self.synthWidget.debugOutput()

        if self.trackWidget.active:
            if key == Qt.Key_D:
                self.trackWidget.openSynthDialog()
            elif key == Qt.Key_M:
                self.trackWidget.toggleMute()
            elif key == Qt.Key_N:
                self.trackWidget.toggleSolo()

            elif key == Qt.Key_Down:
                self.trackWidget.selectTrack(+1)
            elif key == Qt.Key_Up:
                self.trackWidget.selectTrack(-1)

            if self.ctrlPressed:

                if key == Qt.Key_Plus:
                    self.trackModel.addTrack()
                elif key == Qt.Key_Asterisk:
                    self.trackModel.cloneTrack()
                elif key == Qt.Key_Minus:
                    self.trackModel.deleteTrack()

            self.trackWidget.update()

        elif self.patternWidget.active:
            pass

        # elif self.synthWidget.active:
        #     pass


    def keyReleaseEvent(self, event):
        self.setModifiers(event)

    def mouseReleaseEvent(self, event):
        self.setModifiers()

    def setModifiers(self, event = None):
        if event is None:
            self.shiftPressed = False
            self.ctrlPressed = False
            self.altPressed = False
        else:
            self.shiftPressed = event.modifiers() & Qt.ShiftModifier
            self.ctrlPressed = event.modifiers() & Qt.ControlModifier
            self.altPressed = event.modifiers() & Qt.AltModifier

    def closeEvent(self, event):
        QApplication.quit()


    def setModelsFromData(self, data):
        tracks, patterns, synths, drumkit = self.decodeMaysonData(data)
        self.trackModel.setTracks(tracks)
        self.patternModel.setPatterns(patterns)
        self.synthModel.setStringList(synths)
        self.drumModel.setStringList(drumkit)

        self.trackModel.layoutChanged.emit()
        self.patternModel.layoutChanged.emit()
        self.synthModel.layoutChanged.emit()
        self.drumModel.layoutChanged.emit()


    def decodeMaysonData(self, data):
        """
        We have some cleaning up to do. I used to save whole patterns in the track modules.
        Now I just want to store the hash of each pattern, stored in pattern._hash
        But they have to match! (Until now, identity was maintained by unique names.)
        """
        patterns = []
        for encodedPattern in data['patterns']:
            pattern = decodePattern(encodedPattern)
            patterns.append(pattern)

        tracks = []
        for encodedTrack in data['tracks']:
            track = decodeTrack(encodedTrack)
            # now we take care of the module / pattern hash issue
            for module in track.modules:
                for pattern in patterns:
                    if module.patternName == pattern.name:
                        module.setPattern(pattern)
            tracks.append(track)

        synths = [synthName[2:] for synthName in data['synths'] if synthName[0] == 'I']
        drumkit = data['drumkit']
        return tracks, patterns, synths, drumkit


    def pushUndoStack(self):
        if self.undoStep > 0:
            self.undoStack = self.undoStack[:-self.undoStep]
            self.undoStep = 0
        self.state.update({
            'currentTrackIndex': self.trackModel.currentTrackIndex,
            'currentModuleIndex': self.getTrack().currentModuleIndex,
            'currentNoteIndex': self.getModulePattern().currentNoteIndex,
        })
        undoObject = {
            'state': self.state,
            'info': self.info,
            'tracks': self.trackModel.tracks,
            'patterns': self.patternModel.patterns,
            'synths': self.synthModel.stringList(),
            'drumkit': self.drumModel.stringList()
        }
        self.undoStack.append(json.dumps(undoObject, default = lambda obj: obj.__dict__))

    def loadUndoStep(self, relativeStep):
        maxUndoStep = len(self.undoStack) - 1
        self.undoStep = clip(self.undoStep + relativeStep, 0, maxUndoStep)
        undoObject = json.loads(self.undoStack[maxUndoStep - self.undoStep])
        self.state = undoObject['state']
        self.info = undoObject['info']
        self.setModelsFromData(undoObject)
        self.resetWidgets()

    def openSettingsDialog(self):
        pass


############################### HELPERS ############################

    def getTrack(self):
        return self.trackModel.currentTrack()

    def getLastTrack(self):
        return self.trackModel.track(-1)

    def getModule(self, offset = 0):
        return self.getTrack().getModule(offset) if self.getTrack() else None

    def getModulePattern(self):
        if self.getModule() is None or self.getModule().patternHash is None:
            return None
        return self.patternModel.getPatternOfHash(self.getModule().patternHash)

    def getModulePatternIndex(self):
        if self.getModule() is None or self.getModule().patternHash is None:
            return None
        return self.patternModel.getPatternIndexOfHash(self.getModule().patternHash)

    def getModulePatternHash(self):
        return self.getModule().patternHash if self.getModule() else None

#    def getModuleTranspose(self):       return self.getModule().transpose if self.getModule() else 0
#    def getInfo(self, key):             return self.info[key] if key in self.info else None
#    def setInfo(self, key, value):      self.info[key] = value

#    def getPatternLen(self, offset=0):  return self.getPattern(offset).length if self.getPattern(offset) else None
#    def getPatternName(self):           return self.getPattern().name if self.getPattern() else 'None'
#    def getPatternIndex(self):          return self.patterns.index(self.getPattern()) if self.patterns and self.getPattern() and self.getPattern() in self.patterns else -1
#    def getPatternSynthType(self):      return self.getPattern().synth_type if self.getPattern() else '_'
#    def getNote(self):                  return self.getPattern().getNote() if self.getPattern() else None
#    def existsPattern(self, pattern):   return pattern in self.patterns


    # THE MOST IMPORTANT FUNCTION!
    def randomColor(self):
        colorHSV = QColor()
        colorHSV.setHsvF(uniform(.05,.95), .8, .88)
        return (colorHSV.red(), colorHSV.green(), colorHSV.blue())

    def shufflePatternColors(self):
        for pattern in self.patternModel.patterns:
            self.patternColors[pattern._hash] = self.randomColor()

    def getPatternColor(self, patternHash):
        if patternHash not in self.patternColors:
            print(f"WARNING: Requested a pattern color for nonexisting pattern hash {patternHash}. Returning black. (But this should never happen!)")
            return (0, 0, 0)
        return self.patternColors[patternHash]

    def resetWidgets(self):
        self.trackWidget.setTrackModel(self.trackModel)
        self.trackWidget.update()
        self.patternWidget.update()
        self.loadModule()
        self.synthWidget.update()

        if 'currentTrackIndex' in self.state:
            self.trackModel.currentTrackIndex = self.state['currentTrackIndex']
        if 'currentModuleIndex' in self.state:
            self.getTrack().currentModuleIndex = self.state['currentModuleIndex']
        if 'currentNoteIndex' in self.state:
            self.getModulePattern().currentNoteIndex = self.state['currentNoteIndex']


###################### MODEL FUNCTIONALITY ########################

    def loadModule(self, module = None):
        patternHash = module.patternHash if module is not None else self.getModulePatternHash()
        if patternHash is None:
            return
        sanityCheck = 0
        for pattern in self.patternModel.patterns:
            if pattern._hash == patternHash:
                self.patternWidget.setPattern(pattern)
                self.patternWidget.update()
                sanityCheck += 1
        if sanityCheck != 1:
            print(f"wtf? something went wrong with trying to load module {module.patternName} ({module.patternHash}), sanityCheck = {sanityCheck}")

    def trackChanged(self):
        self.pushUndoStack()

    def patternChanged(self):
        self.pushUndoStack()

######################### SYNATIZE FUNCTIONALITY #####################

    def renderModule(self):
        pass

    def renderTrack(self):
        pass

    def hardCopySynth(self):
        pass

    def randomizeSynatizer(self):
        print("this is heavy stuff!")
        # TODO: synatize should tell us which main forms include random content ;)


###################################################################

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())