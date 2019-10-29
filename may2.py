#########################################################################
## This is the PyQt rewrite from aMaySyn. It is aMay2yn.
## by QM / Team210
#########################################################################

import sys
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QAction, QVBoxLayout, QGroupBox, QSplitter, QFileDialog, \
    QDoubleSpinBox, QCheckBox, QLabel,QInputDialog, QLineEdit, QMessageBox, QStackedLayout
from PyQt5.QtCore import Qt, pyqtSignal, QItemSelectionModel, QFile, QTextStream, QStringListModel, QBuffer, QIODevice
from PyQt5.QtGui import QFontDatabase, QIcon, QColor
from PyQt5.QtMultimedia import QAudioOutput, QAudioFormat, QAudioDeviceInfo, QAudio
from copy import deepcopy
from functools import partial
from os import path
from time import sleep
from random import uniform, choice
from numpy import clip
from shutil import move, copyfile
import json
import re

from May2TrackWidget import May2TrackWidget
from May2PatternWidget import May2PatternWidget
from May2SynthWidget import May2SynthWidget
from may2TrackModel import TrackModel
from may2PatternModel import PatternModel
from may2Objects import Track, Pattern, decodeTrack, decodePattern, SYNTHTYPE, DRUMTYPE
from May2ynatizer import synatize, synatize_build
from May2ynBuilder import May2ynBuilder
from SFXGLWidget import SFXGLWidget
from SettingsDialog import SettingsDialog
from PatternDialogs import ImportPatternDialog
from may2Style import notACrime

globalStateFile = 'global.state'
defaultSynFile = 'default.syn'

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setGeometry(320, 0, 1600, 1000)
        self.setWindowTitle('aMay2yn')
        self.setWindowIcon(QIcon('./qm_avatar32.gif'))

        self.initLayout()
        self.initSignals()
        self.initModelView()
        self.initState()
        self.setStyleSheet(notACrime)

        self.initAMay2yn()
        self.initAudio()

        self.show()

        self.shiftPressed = False
        self.ctrlPressed = False
        self.altPressed = False

       # print(QFontDatabase.addApplikationFont(':/RobotoMonomRegular.ttf')) # could pedistribute, but then I should Read about its LICENSE first

    def initLayout(self):
        self.initToolBar()

        self.trackWidget = May2TrackWidget(self)
        self.trackGroupLayout = QVBoxLayout()
        self.trackGroupLayout.addWidget(self.trackWidget)
        self.trackGroup = QGroupBox()
        self.trackGroup.setLayout(self.trackGroupLayout)

        self.synthPatternWidget = May2PatternWidget(self)
        self.drumPatternWidget = May2PatternWidget(self, drumMode = True)
        self.patternWidget = self.synthPatternWidget
        self.patternGroupLayout = QStackedLayout()
        self.patternGroupLayout.addWidget(self.synthPatternWidget)
        self.patternGroupLayout.addWidget(self.drumPatternWidget)
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
        self.toolBar = self.addToolBar('Main')
        self.toolBar.setMovable(False)

        newAction = QAction(QIcon.fromTheme('document-new'), 'New', self)
        newAction.setShortcut('Ctrl+N')
        loadAction = QAction(QIcon.fromTheme('document-open'), 'Load .mayson', self)
        loadAction.setShortcut('Ctrl+L')
        saveAction = QAction(QIcon.fromTheme('document-save'), 'Save .mayson', self)
        saveAction.setShortcut('Ctrl+S')
        saveAsAction = QAction(QIcon.fromTheme('document-save-as'), 'Save .mayson As...', self)
        saveAsAction.setShortcut('Ctrl+Shift+S')
        undoAction = QAction(QIcon.fromTheme('edit-undo'), 'Undo', self)
        undoAction.setShortcut('Ctrl+Z')
        redoAction = QAction(QIcon.fromTheme('edit-redo'), 'Redo', self)
        redoAction.setShortcut('Shift+Ctrl+Z')
        settingsAction = QAction(QIcon.fromTheme('preferences-system'), 'Settings', self)
        settingsAction.setShortcut('F3')
        renderModuleAction = QAction(QIcon.fromTheme('media-playback-start'), 'RenderModule', self)
        renderModuleAction.setShortcut('Ctrl+T')
        renderSongAction = QAction(QIcon.fromTheme('media-playback-start'), 'RenderSong', self)
        renderSongAction.setShortcut('Ctrl+Enter')
        stopPlaybackAction = QAction(QIcon.fromTheme('media-playback-stop'), 'Stop Playback', self)
        stopPlaybackAction.setShortcut('Enter')
        importPatternAction = QAction(QIcon('./icon_lmms_import.png'), 'Import LMMS Patterns', self)
        importPatternAction.setShortcut('Ctrl+I')

        newAction.triggered.connect(self.newSong)
        loadAction.triggered.connect(self.loadAndImportMayson)
        saveAction.triggered.connect(self.exportMayson)
        saveAsAction.triggered.connect(partial(self.exportMayson, saveAs = True))
        undoAction.triggered.connect(partial(self.loadUndoStep, relativeStep = +1))
        redoAction.triggered.connect(partial(self.loadUndoStep, relativeStep = -1))
        settingsAction.triggered.connect(self.openSettingsDialog)
        renderModuleAction.triggered.connect(self.renderModule)
        renderSongAction.triggered.connect(self.renderSong)
        stopPlaybackAction.triggered.connect(self.stopPlayback)
        importPatternAction.triggered.connect(self.openImportPatternDialog)

        self.toolBar.addAction(newAction)
        self.toolBar.addAction(loadAction)
        self.toolBar.addAction(saveAction)
        self.toolBar.addAction(saveAsAction)
        self.toolBar.addSeparator()
        self.toolBar.addAction(undoAction)
        self.toolBar.addAction(redoAction)
        self.toolBar.addAction(settingsAction)
        self.toolBar.addSeparator()
        self.toolBar.addWidget(QLabel('   Module: '))
        self.toolBar.addAction(renderModuleAction)
        self.toolBar.addWidget(QLabel(' All: '))
        self.toolBar.addAction(renderSongAction)
        self.toolBar.addAction(stopPlaybackAction)

        self.toolBar.addWidget(QLabel('  ', self))
        self.beatOffsetCheckBox = QCheckBox('From: ', self)
        self.beatOffsetCheckBox.setChecked(True)
        self.toolBar.addWidget(self.beatOffsetCheckBox)

        self.beatOffsetSpinBox = QDoubleSpinBox(self)
        self.beatOffsetSpinBox.setDecimals(0)
        self.beatOffsetSpinBox.setSingleStep(1)
        self.beatOffsetSpinBox.setRange(0, 999)
        self.beatOffsetSpinBox.setPrefix('Beat ')
        self.beatOffsetSpinBox.setMinimumWidth(120)
        self.beatOffsetSpinBox.setEnabled(True)
        self.toolBar.addWidget(self.beatOffsetSpinBox)

        self.toolBar.addWidget(QLabel('  ', self))
        self.beatStopCheckBox = QCheckBox('To: ', self)
        self.toolBar.addWidget(self.beatStopCheckBox)

        self.beatStopSpinBox = QDoubleSpinBox(self)
        self.beatStopSpinBox.setDecimals(0)
        self.beatStopSpinBox.setSingleStep(1)
        self.beatStopSpinBox.setRange(0, 999)
        self.beatStopSpinBox.setPrefix('Beat ')
        self.beatStopSpinBox.setMinimumWidth(120)
        self.beatStopSpinBox.setEnabled(False)
        self.toolBar.addWidget(self.beatStopSpinBox)

        self.toolBar.addWidget(QLabel('  ', self))
        self.writeWavCheckBox = QCheckBox('Write .WAV', self)
        self.toolBar.addWidget(self.writeWavCheckBox)

        self.useSequenceCheckBox = QCheckBox('Use Sequence', self)
        self.toolBar.addWidget(self.useSequenceCheckBox)

        self.toolBar.addSeparator()
        self.toolBar.addAction(importPatternAction)

    def initSignals(self):
        self.trackWidget.moduleSelected.connect(self.loadModule)
        self.trackWidget.trackChanged.connect(self.trackChanged)
        self.trackWidget.trackTypeChanged.connect(self.trackTypeChanged)
        self.trackWidget.activated.connect(partial(self.toggleActivated, activateTrack = True))
        self.patternWidget.activated.connect(partial(self.toggleActivated, activatePattern = True))
        self.patternWidget.patternChanged.connect(self.patternChanged)

        self.beatOffsetCheckBox.stateChanged.connect(self.updateRenderRange)
        self.beatOffsetSpinBox.valueChanged.connect(self.updateRenderRange)
        self.beatStopCheckBox.stateChanged.connect(self.updateRenderRange)
        self.beatStopSpinBox.valueChanged.connect(self.updateRenderRange)

        self.writeWavCheckBox.stateChanged.connect(self.updateWriteWav)
        self.useSequenceCheckBox.stateChanged.connect(self.updateUseSequence)

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
            'useSequence': True,
            'extraTimeShift': 0,
            'useOffset': False,
            'useStop': False,
            'numberInputMode': False,
            'numberInput': '',
            'lastNumberInput': '',
            'lastImportPatternFilename': '',
            'lastImportPatternFilter': '',
        }
        # TODO: store Synatize output in self.state? C=
        self.defaultInfo = {
            'BPM': '0:32',
            'B_offset': 0,
            'B_stop': 0,
            'loop': 'none',
            'stereo_delay': 2e-4,
            'level_syn': .5,
            'level_drum': .666,
            'barsPerBeat': 4,
            'beatQuantum': 1/16,
        }
        self.info = deepcopy(self.defaultInfo)
        self.patterns = []
        self.amaysyn = None
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

        self.updateUIfromState()


    def updateUIfromState(self):
        self.trackWidget.updateBpmList(self.info['BPM'])

        self.beatOffsetSpinBox.blockSignals(True)
        self.beatOffsetSpinBox.setValue(self.info.get('B_offset', 0))
        self.beatOffsetSpinBox.blockSignals(False)

        self.beatStopSpinBox.blockSignals(True)
        self.beatStopSpinBox.setValue(self.info.get('B_stop', 0))
        self.beatStopSpinBox.blockSignals(False)

        self.beatOffsetCheckBox.blockSignals(True)
        self.beatOffsetCheckBox.setChecked(self.state.get('useOffset', False))
        self.beatOffsetCheckBox.blockSignals(False)

        self.beatStopCheckBox.blockSignals(True)
        self.beatStopCheckBox.setChecked(self.state.get('useStop', False))
        self.beatStopCheckBox.blockSignals(False)

        self.updateRenderRange()

        self.writeWavCheckBox.setChecked(self.state['writeWAV'])
        self.useSequenceCheckBox.setChecked(self.state['useSequence'])

    def updateWriteWav(self, state):
        self.state['writeWAV'] = (state == Qt.Checked)

    def updateUseSequence(self, state):
        self.state['useSequence'] = (state == Qt.Checked)
        if self.amaysyn is not None:
            self.amaysyn.useSequenceTexture = self.state['useSequence']

    def toggleActivated(self, activateTrack = False, activatePattern = False, activateSynth = False):
        self.trackGroup.setObjectName('activated' if activateTrack else '')
        self.trackWidget.active = activateTrack
        self.trackGroup.style().polish(self.trackGroup)

        self.patternGroup.setObjectName('activated' if activatePattern else '')
        self.patternWidget.active = activatePattern
        self.patternGroup.style().polish(self.patternGroup)

        self.synthGroup.setObjectName('activated' if activateSynth else '')
        self.synthWidget.active = activateSynth
        self.synthGroup.style().polish(self.synthGroup)

        if activateTrack:
            self.trackWidget.setFocus()
        elif activatePattern:
            self.patternWidget.setFocus()
        elif activateSynth:
            self.synthWidget.setFocus()


    def newSong(self):
        newTitle, ok = QInputDialog.getText(self, 'New Song', 'Title:', QLineEdit.Normal, '')
        if ok:
            self.setModelsFromData(None)
            self.shufflePatternColors()
            self.state['title'] = newTitle or 'QoolMusic'
            self.state['synFile'] = None # f"{self.globalState['lastDirectory']}/{newTitle}"
            self.globalState['maysonFile'] = None
            self.info = deepcopy(self.defaultInfo)
            self.patternWidget.setPattern(None)
            self.updateUIfromState()

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
            print(f"{self.globalState['maysonFile']} could not be imported. Choose again.")
            self.loadAndImportMayson()
        finally:
            file.close()

        if maysonData == {}:
            return

        for key in maysonData['state']:
            self.state.update({key: maysonData['state'][key]})

        for key in maysonData['info']:
            self.info.update({key: maysonData['info'][key]})

        if 'title' in self.info:
            self.state['title'] = self.info.pop('title')
        if 'title' not in self.state or 'synFile' not in self.state:
            self.state['title'], self.state['synFile'] = self.getTitleAndSynFromMayson(self.globalState['maysonFile'])
        if self.amaysyn is not None:
            self.amaysyn.updateState(title = self.state['title'], info = self.info)

        self.setModelsFromData(maysonData)
        self.shufflePatternColors()

        self.trackWidget.activate()
        tracks = self.trackModel.tracks
        if tracks:
            if tracks[0].modules:
                self.trackWidget.select(tracks[0], tracks[0].modules[0])
            else:
                self.trackWidget.select(tracks[0])


    def exportMayson(self, saveAs = False):
        if saveAs:
            suggestFileName = self.globalState['maysonFile'] or f"{self.state['title']}.mayson"
            filename, _ = QFileDialog.getSaveFileName(self, 'Save new MAYSON file', suggestFileName, 'aMaySyn *.mayson(*.mayson)')
            if filename == '':
                return
            self.globalState['maysonFile'] = filename
            self.globalState['lastDirectory'] = path.dirname(filename)
            oldSynFile = self.state['synFile']
            self.state['title'], self.state['synFile'] = self.getTitleAndSynFromMayson(filename)
            self.ensureSynFile(copySynFile = oldSynFile)
        else:
            self.globalState['maysonFile'] = self.globalState['maysonFile'] or f"{self.state['title']}.mayson"
            self.ensureSynFile()

        data = {
            'state': self.state,
            'info': self.info,
            'tracks': self.trackModel.tracks,
            'patterns': self.patternModel.patterns,
            'synths': self.synthModel.stringList(),
            'drumkit': self.drumModel.stringList(),
        }
        fn = open(self.globalState['maysonFile'], 'w')
        print(f"Export to {self.globalState['maysonFile']}")
        json.dump(data, fn, default = lambda obj: obj.__dict__)
        fn.close()

    def ensureSynFile(self, copySynFile = None):
        synFile = self.state['title'] + '.syn'
        if copySynFile is not None:
            if not path.exists(copySynFile):
                copySynFile = defaultSynFile
                # TODO: prompt whether to overwrite
                copyfile(copySynFile, synFile)
                print(f"Copied {copySynFile} to {synFile}.")
        else:
            if not path.exists(synFile):
                copyfile(defaultSynFile, synFile)
                print(f"Copied {defaultSynFile} to {synFile}.")

    def getTitleAndSynFromMayson(self, maysonFile):
        synFile = '.'.join(maysonFile.split('.')[:-1]) + '.syn'
        title = '.'.join(path.basename(maysonFile).split('.')[:-1])
        return title, synFile

    def reloadSynFile(self):
        self.amaysyn.updateState(title = self.state['title'], synFile = self.state['synFile'])
        self.amaysyn.aMaySynatize()
        self.synthModel.setStringList(self.amaysyn.synthNames)
        self.drumModel.setStringList(self.amaysyn.drumkit)

    def autoSave(self):
        self.autoSaveGlobals()
        print("fully implement autosave.... yet to do")

    def autoSaveGlobals(self):
        file =  open(globalStateFile, 'w')
        json.dump(self.globalState, file)
        file.close()


    def keyPressEvent(self, event):
        key = event.key()
        keytext = event.text()
        self.setModifiers(event)

        if key == Qt.Key_Escape:
            self.close()
        elif key == Qt.Key_F5:
            self.reloadSynFile()
        elif key == Qt.Key_F9:
            self.trackWidget.debugOutput()
        elif key == Qt.Key_F10:
            self.patternWidget.debugOutput()
        elif key == Qt.Key_F11:
            self.synthWidget.debugOutput()

        if self.trackWidget.active:

            if not self.ctrlPressed and not self.shiftPressed:

                if key == Qt.Key_D:
                    self.trackWidget.openSynthDialog()
                elif key == Qt.Key_F:
                    self.setRandomSynth()
                elif key == Qt.Key_M:
                    self.trackWidget.toggleMute()
                elif key == Qt.Key_N:
                    self.trackWidget.toggleSolo()

                elif key == Qt.Key_Down:
                    self.trackWidget.selectTrack(+1)
                elif key == Qt.Key_Up:
                    self.trackWidget.selectTrack(-1)

            elif self.ctrlPressed and not self.shiftPressed:

                if key == Qt.Key_Plus:
                    self.trackModel.addTrack()
                elif key == Qt.Key_Asterisk:
                    self.trackModel.cloneTrack()
                elif key == Qt.Key_Minus:
                    self.trackModel.deleteTrack()

            elif self.ctrlPressed and self.shiftPressed:

                if key == Qt.Key_Up:
                    self.trackModel.transposeModule(+12)
                elif key == Qt.Key_Down:
                    self.trackModel.transposeModule(-12)

            self.trackWidget.update()

        elif self.patternWidget.active:

            if not self.shiftPressed and not self.ctrlPressed:

                if key == Qt.Key_V:
                    self.setParameterFromNumberInput('vel')
                elif key == Qt.Key_P:
                    self.setParameterFromNumberInput('pan')
                elif key == Qt.Key_G:
                    self.setParameterFromNumberInput('slide')
                elif key == Qt.Key_X:
                    self.setParameterFromNumberInput('aux')

                if keytext:
                    if keytext.isdigit() or keytext in ['.', '-']:
                        self.setNumberInput(keytext)
                    else:
                        self.setNumberInput()

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
        if data is not None:
            tracks, patterns, synths, drumkit = self.decodeMaysonData(data)
        else:
            tracks = [Track()]
            patterns = [Pattern()]

            self.initAMay2yn()
            self.amaysyn.aMaySynatize(defaultSynFile)
            synths = [synth[2:] for synth in self.amaysyn.synths if synth[0] == SYNTHTYPE]
            drumkit = self.amaysyn.drumkit
            print("init the shit and we have", synths, drumkit)

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

        synths = []
        for synthName in data['synths']:
            if synthName[1] == '_':
                if synthName[0] == SYNTHTYPE:
                    synths.append(synthName[2:])
            else:
                synths.append(synthName)

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
        settingsDialog = SettingsDialog(self)
        if settingsDialog.exec_():
            self.info['bpm'] = settingsDialog.bpmList()
            self.trackWidget.updateBpmList(self.info['bpm'])
            self.info['level_syn'], self.info['level_drum'] = settingsDialog.getLevels()
            self.info['beatQuantum'] = 1/float(settingsDialog.beatQuantumDenominatorSpinBox.value())
            self.info['barsPerBeat'] = settingsDialog.barsPerBeatSpinBox.value()

    def openImportPatternDialog(self):
        importPatternDialog = ImportPatternDialog(self, filename = self.state['lastImportPatternFilename'], filter = self.state['lastImportPatternFilter'])
        if importPatternDialog.exec_():
            for pattern in importPatternDialog.parsedPatterns:
                self.addPattern(pattern)
        self.state['lastImportPatternFilename'] = importPatternDialog.xmlFilename
        self.state['lastImportPatternFilter'] = importPatternDialog.filter
        # self.autosave()

    def updateRenderRange(self):
        self.beatOffsetSpinBox.setRange(0, self.trackModel.totalLength())
        self.beatStopSpinBox.setRange(0, self.trackModel.totalLength())

        useOffset = self.beatOffsetCheckBox.isChecked()
        if useOffset:
            self.beatStopSpinBox.setMinimum(self.beatOffsetSpinBox.value())
        self.beatOffsetSpinBox.setEnabled(useOffset)
        self.info['B_offset'] = self.beatOffsetSpinBox.value() if useOffset else 0
        if self.info['B_offset'] > 0:
            self.trackWidget.addMarker('OFFSET', self.info['B_offset'], unique = True)
        elif self.info['B_offset'] == 0:
            self.trackWidget.removeMarkersContaining('OFFSET')

        useStop = self.beatStopCheckBox.isChecked()
        if useStop:
            self.beatOffsetSpinBox.setMaximum(self.beatStopSpinBox.value())
        self.beatStopSpinBox.setEnabled(useStop)
        self.info['B_stop'] = self.beatStopSpinBox.value() if useStop else 0
        if self.info['B_stop'] > self.info['B_offset']:
            self.trackWidget.addMarker('STOP', self.info['B_stop'], unique = True)
        else:
            self.trackWidget.removeMarkersContaining('STOP')

        self.state['useOffset'] = useOffset and self.info['B_offset'] > 0
        self.state['useStop'] = useStop and self.info['B_stop'] > self.info['B_offset']

        self.trackWidget.update()

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

#    def getPatternLen(self, offset=0):  return self.getPattern(offset).length if self.getPattern(offset) else None
#    def getPatternName(self):           return self.getPattern().name if self.getPattern() else 'None'
#    def getPatternIndex(self):          return self.patterns.index(self.getPattern()) if self.patterns and self.getPattern() and self.getPattern() in self.patterns else -1
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

    def setNumberInput(self, keytext = ''):
        if not keytext:
            self.state['numberInputMode'] = False
        if not self.state['numberInputMode']:
            self.state['numberInput'] = ''
            self.state['numberInputMode'] = True

        if keytext.isdigit():
            self.state['numberInput'] += keytext
        elif keytext == '.' and '.' not in self.state['numberInput']:
            self.state['numberInput'] += keytext
        elif keytext == '-':
            self.state['numberInput'] = ('-' + self.state['numberInput']).replace('--', '')

        self.patternWidget.setNumberInput(self.state['numberInput'])

    def setParameterFromNumberInput(self, parameter):
        if self.state['numberInput']:
            self.state['lastNumberInput'] = self.state['numberInput']
        self.getModulePattern().getNote().setParameter(parameter, self.state['lastNumberInput'])

    def setRandomSynth(self):
        track = self.getTrack()
        if track:
            track.setSynth(type = track.synthType, name = self.getRandomSynthName(track.synthType))

    def getRandomSynthName(self, type):
        if type != SYNTHTYPE or self.synthModel.rowCount() == 0:
            return type
        return choice(self.synthModel.stringList())

###################### MODEL FUNCTIONALITY ########################

    def loadModule(self, module = None):
        patternHash = module.patternHash if module is not None else self.getModulePatternHash()
        if patternHash is None:
            return
        for pattern in self.patternModel.patterns:
            if pattern._hash == patternHash:
                self.patternWidget.setPattern(pattern)
                self.patternWidget.update()
                return

    def trackChanged(self):
        if not self.getTrack().isEmpty():
            self.pushUndoStack()

    def trackTypeChanged(self):
        synthType = self.trackWidget.model.currentTrackType()
        if synthType == DRUMTYPE:
            self.patternWidget = self.drumPatternWidget
        else:
            self.patternWidget = self.synthPatternWidget
        self.patternGroupLayout.setCurrentWidget(self.patternWidget)

    def patternChanged(self):
        self.pushUndoStack()

    def addPattern(self, pattern = None, clone = False):
        index = self.patternModel.getIndexOfPattern(pattern)
        if index is None:
            index = self.patternModel.rowCount() - 1
        if clone:
            self.patternModel.cloneRow(index)
        elif pattern is not None:
            self.patternModel.addRow(index, pattern)
            self.patternColors[pattern._hash] = self.randomColor()


######################### SYNATIZE FUNCTIONALITY #####################

    def hardCopySynth(self):
        pass

    def randomizeSynatizer(self):
        print("this is heavy stuff!")
        # TODO: synatize should tell us which main forms include random content ;)

    def initAMay2yn(self):
        self.amaysyn = May2ynBuilder(self, self.state['synFile'], self.info)
        self.amaysyn.useSequenceTexture = self.state['useSequence']

    def initAudio(self):
        # HARDCODE, make these configurable!
        self.texsize = 512
        self.samplerate = 44100

        self.audioformat = QAudioFormat()
        self.audioformat.setSampleRate(self.samplerate)
        self.audioformat.setChannelCount(2)
        self.audioformat.setSampleSize(32)
        self.audioformat.setCodec('audio/pcm')
        self.audioformat.setByteOrder(QAudioFormat.LittleEndian)
        self.audioformat.setSampleType(QAudioFormat.Float)
        self.audiooutput = QAudioOutput(self.audioformat)
        self.audiooutput.setVolume(1.0)

    def stopPlayback(self):
        self.audiooutput.stop()

    def renderWhateverWasLast(self):
        if self.state['lastRendered'] == 'module':
            self.renderModule()
        elif self.state['lastRendered'] == 'track':
            self.renderTrack()
        else:
            self.renderSong()

    def renderModule(self):
        self.state['lastRendered'] = 'module'
        track = deepcopy(self.getTrack())
        track.mute = False
        modInfo = deepcopy(self.info)
        modInfo['B_offset'] = self.getModule().getModuleOn()
        modInfo['B_stop'] = self.getModule().getModuleOff()
        self.amaysyn.updateState(title = self.state['title'], info = modInfo)
        self.amaysyn.extra_time_shift = self.state.get('extraTimeShift', 0) # THIS HAS SOME DEBUGGING REASONS
        shader = self.amaysyn.build(tracks = [track], patterns = [self.getModulePattern()])
        self.amaysyn.updateState(info = self.info)
        self.executeShader(shader)

    def renderTrack(self):
        self.state['lastRendered'] = 'track'
        track = self.getTrack()
        restoreMute = track.mute
        track.mute = False
        self.amaysyn.extra_time_shift = self.state.get('extraTimeShift', 0)
        self.amaysyn.updateState(title = self.state['title'], info = self.info)
        shader = self.amaysyn.build(tracks = [track], patterns = self.patternModel.patterns)
        track.mute = restoreMute
        self.executeShader(shader)

    def renderSong(self):
        self.state['lastRendered'] = 'song'
        self.amaysyn.extra_time_shift = self.state.get('extraTimeShift', 0)
        self.amaysyn.updateState(title = self.state['title'], info = self.info)
        shader = self.amaysyn.build(tracks = self.trackModel.tracks, patterns = self.patternModel.patterns)
        self.executeShader(shader)

    def executeShader(self, shader):
        if shader is None:
            print("Called executeShader() with a shader of None. Some stupid shit happened and I will do no more.")
            return
        sequenceLength = len(self.amaysyn.sequence) if self.amaysyn.sequence is not None else 0
        if not self.amaysyn.useSequenceTexture and sequenceLength > pow(2, 14):
            QMessageBox.critical(self, "I CAN'T", f"Either switch to using the Sequence Texture (ask QM), or reduce the sequence size by limiting the offset/stop positions or muting tracks.\nCurrent sequence length is:\n{sequenceLength} > {pow(2,14)}")
            return

        self.bytearray = self.amaysyn.executeShader(shader, self.samplerate, self.texsize, renderWAV = self.state['writeWAV'])
        self.audiobuffer = QBuffer(self.bytearray)
        self.audiobuffer.open(QIODevice.ReadOnly)
        self.audiooutput.stop()
        self.audiooutput.start(self.audiobuffer)

###################################################################

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())