#########################################################################
## This is the PyQt rewrite from aMaySyn. It is aMay2yn.
## by QM / Team210
#########################################################################

import re
import sys
import json
from math import ceil
from copy import deepcopy
from functools import partial
from os import path
from random import uniform, choice
from shutil import copyfile
from datetime import datetime
from numpy import clip
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QAction, QVBoxLayout, QGroupBox, QSplitter, QFileDialog, \
    QDoubleSpinBox, QCheckBox, QLabel,QInputDialog, QLineEdit, QMessageBox, QStackedLayout
from PyQt5.QtCore import Qt, QStringListModel, QBuffer, QIODevice
from PyQt5.QtGui import QIcon, QColor, QPainter
from PyQt5.QtMultimedia import QAudioOutput, QAudioFormat

from May2TrackWidget import May2TrackWidget
from May2PatternWidget import May2PatternWidget
from May2SynthWidget import May2SynthWidget
from may2TrackModel import TrackModel
from may2PatternModel import PatternModel
from may2SynthModel import SynthModel
from may2Pattern import *
from may2Note import Note
from may2Encoding import *
from May2ynBuilder import May2ynBuilder
from SettingsDialog import SettingsDialog
from PatternDialogs import ImportPatternDialog
from ParameterDialog import ParameterDialog
from RandomizerDialog import RandomizerDialog
from may2Utils import findFreeSerial, printDebug
from may2Style import notACrime, deactivatedColor

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
        self.initAudio()

        self.show()

        self.setModifiers(None)

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

        self.mainSplitLayout = QSplitter(self)
        self.mainSplitLayout.setOrientation(Qt.Vertical)
        self.mainSplitLayout.addWidget(self.trackGroup)
        self.mainSplitLayout.addWidget(self.patternGroup)
        self.mainSplitLayout.addWidget(self.synthGroup)
        self.mainSplitLayout.setSizes([400,500,150])

        self.mainLayout = QVBoxLayout()
        self.mainLayout.addWidget(self.mainSplitLayout)

        self.centralWidget = QWidget(self)
        self.centralWidget.setLayout(self.mainLayout)
        self.setCentralWidget(self.centralWidget)


    def initToolBar(self):
        self.toolBar = self.addToolBar('Main')
        self.toolBar.setMovable(False)
        self.toolBar.setContextMenuPolicy(Qt.PreventContextMenu)

        newAction = QAction(QIcon.fromTheme('document-new'), 'New', self)
        newAction.setShortcut('Ctrl+N')
        newAction.triggered.connect(self.newSong)
        self.toolBar.addAction(newAction)

        loadAction = QAction(QIcon.fromTheme('document-open'), 'Load .mayson', self)
        loadAction.setShortcut('Ctrl+L')
        loadAction.triggered.connect(self.loadAndImportMayson)
        self.toolBar.addAction(loadAction)

        saveAction = QAction(QIcon.fromTheme('document-save'), 'Save .mayson', self)
        saveAction.setShortcut('Ctrl+S')
        saveAction.triggered.connect(self.exportMayson)
        self.toolBar.addAction(saveAction)

        saveAsAction = QAction(QIcon.fromTheme('document-save-as'), 'Save .mayson As...', self)
        saveAsAction.setShortcut('Ctrl+Shift+S')
        saveAsAction.triggered.connect(partial(self.exportMayson, saveAs = True))
        self.toolBar.addAction(saveAsAction)

        self.toolBar.addSeparator()

        undoAction = QAction(QIcon.fromTheme('edit-undo'), 'Undo', self)
        undoAction.setShortcut('Ctrl+Z')
        undoAction.triggered.connect(partial(self.loadUndoStep, relativeStep = +1))
        self.toolBar.addAction(undoAction)
        redoAction = QAction(QIcon.fromTheme('edit-redo'), 'Redo', self)
        redoAction.setShortcut('Shift+Ctrl+Z')
        redoAction.triggered.connect(partial(self.loadUndoStep, relativeStep = -1))
        self.toolBar.addAction(redoAction)
        settingsAction = QAction(QIcon.fromTheme('preferences-system'), 'Settings', self)
        settingsAction.setShortcut('F3')
        settingsAction.triggered.connect(self.openSettingsDialog)
        self.toolBar.addAction(settingsAction)

        self.toolBar.addSeparator()

        reloadSynAction = QAction(QIcon('./icon_reloadSyn.png'), 'Reload .syn File', self)
        reloadSynAction.setShortcut('F5')
        reloadSynAction.triggered.connect(self.loadSynFile)
        self.toolBar.addAction(reloadSynAction)

        randomizeAllAction = QAction(QIcon('./icon_randomize.png'), 'Shuffle All Random Values', self)
        randomizeAllAction.setShortcut('F4')
        randomizeAllAction.triggered.connect(self.reshuffleAllRandomValues)
        self.toolBar.addAction(randomizeAllAction)

        randomizeAllManyTimesAction = QAction(QIcon('./icon_randomize_many.png'), 'Shuffle All Random Variables Multiple Times', self)
        randomizeAllManyTimesAction.setShortcut('Ctrl+F4')
        randomizeAllManyTimesAction.triggered.connect(self.reshuffleAllRandomValuesManyTimes)
        self.toolBar.addAction(randomizeAllManyTimesAction)

        self.toolBar.addSeparator()

        renderModuleAction = QAction(QIcon.fromTheme('media-playback-start'), 'RenderModule', self)
        renderModuleAction.setShortcut('Ctrl+T')
        renderModuleAction.triggered.connect(self.renderModule)
        self.toolBar.addWidget(QLabel('   Module: '))
        self.toolBar.addAction(renderModuleAction)

        renderSongAction = QAction(QIcon.fromTheme('media-playback-start'), 'RenderSong', self)
        renderSongAction.setShortcut('Ctrl+Shift+T')
        renderSongAction.triggered.connect(self.renderSong)
        self.toolBar.addWidget(QLabel(' All: '))
        self.toolBar.addAction(renderSongAction)

        stopPlaybackAction = QAction(QIcon.fromTheme('media-playback-stop'), 'Stop Playback', self)
        stopPlaybackAction.setShortcut('Enter')
        stopPlaybackAction.triggered.connect(self.stopPlayback)
        self.toolBar.addAction(stopPlaybackAction)

        self.toolBar.addWidget(QLabel('  ', self))
        self.beatOffsetCheckBox = QCheckBox('From Beat ', self)
        self.beatOffsetCheckBox.setChecked(True)
        self.toolBar.addWidget(self.beatOffsetCheckBox)

        self.beatOffsetSpinBox = QDoubleSpinBox(self)
        self.beatOffsetSpinBox.setDecimals(0)
        self.beatOffsetSpinBox.setSingleStep(1)
        self.beatOffsetSpinBox.setRange(0, 999)
        self.beatOffsetSpinBox.setMinimumWidth(120)
        self.beatOffsetSpinBox.setEnabled(True)
        self.toolBar.addWidget(self.beatOffsetSpinBox)

        self.toolBar.addWidget(QLabel('  ', self))
        self.beatStopCheckBox = QCheckBox('To ', self)
        self.toolBar.addWidget(self.beatStopCheckBox)

        self.beatStopSpinBox = QDoubleSpinBox(self)
        self.beatStopSpinBox.setDecimals(0)
        self.beatStopSpinBox.setSingleStep(1)
        self.beatStopSpinBox.setRange(0, 999)
        self.beatStopSpinBox.setMinimumWidth(120)
        self.beatStopSpinBox.setEnabled(False)
        self.toolBar.addWidget(self.beatStopSpinBox)

        self.toolBar.addWidget(QLabel('  ', self))
        self.writeWavCheckBox = QCheckBox('Write .WAV', self)
        self.toolBar.addWidget(self.writeWavCheckBox)

        self.loopCheckBox = QCheckBox('Loop', self)
        self.toolBar.addWidget(self.loopCheckBox)

        self.useSequenceCheckBox = QCheckBox('Use Sequence', self)
        self.toolBar.addWidget(self.useSequenceCheckBox)

        self.toolBar.addSeparator()

        importPatternAction = QAction(QIcon('./icon_lmms_import.png'), 'Import LMMS Patterns', self)
        importPatternAction.setShortcut('Ctrl+I')
        importPatternAction.triggered.connect(self.openImportPatternDialog)
        self.toolBar.addAction(importPatternAction)

        self.toolBar.addSeparator()

        renderNoteAction = QAction(QIcon.fromTheme('media-playback-start'), 'Render Note', self)
        renderNoteAction.setShortcut('Ctrl+B')
        renderNoteAction.triggered.connect(self.renderNote)
        self.toolBar.addWidget(QLabel('  Note:'))
        self.toolBar.addAction(renderNoteAction)

        renderFileAction = QAction(QIcon.fromTheme('media-playback-start'), 'Render File', self)
        renderFileAction.setShortcut('Ctrl+W')
        renderFileAction.triggered.connect(self.renderFile)
        self.renderFilePathEdit = QLineEdit(self)
        self.toolBar.addWidget(QLabel('File: '))
        self.toolBar.addWidget(self.renderFilePathEdit)
        self.toolBar.addAction(renderFileAction)


    def initSignals(self):
        self.trackWidget.moduleSelected.connect(self.loadModule)
        self.trackWidget.trackSelected.connect(self.trackSelected)
        self.trackWidget.trackChanged.connect(self.trackChanged)
        self.trackWidget.trackTypeChanged.connect(self.trackTypeChanged)
        self.trackWidget.activated.connect(partial(self.toggleActivated, activateTrack = True))
        self.synthPatternWidget.activated.connect(partial(self.toggleActivated, activatePattern = True))
        self.synthPatternWidget.patternChanged.connect(self.synthPatternChanged)
        self.drumPatternWidget.activated.connect(partial(self.toggleActivated, activatePattern = True))
        self.drumPatternWidget.patternChanged.connect(self.drumPatternChanged)
        self.synthWidget.paramChanged.connect(self.paramChanged)
        self.synthWidget.randomsChanged.connect(self.randomsChanged)

        self.beatOffsetCheckBox.stateChanged.connect(self.updateRenderRange)
        self.beatOffsetSpinBox.valueChanged.connect(self.updateRenderRange)
        self.beatStopCheckBox.stateChanged.connect(self.updateRenderRange)
        self.beatStopSpinBox.valueChanged.connect(self.updateRenderRange)

        self.writeWavCheckBox.stateChanged.connect(self.updateWriteWav)
        self.loopCheckBox.stateChanged.connect(self.updateLoop)
        self.useSequenceCheckBox.stateChanged.connect(self.updateUseSequence)


    def initModelView(self):
        self.trackModel = TrackModel()
        self.patternModel = PatternModel()
        self.synthModel = SynthModel()
        self.drumModel = QStringListModel()

        self.trackWidget.setTrackModel(self.trackModel)


    def initState(self): # mixing autoLoad functionality in here... for now.
        self.globalState = {
            'maysonFile': '',
            'lastDirectory': None,
            'argGivenTitle': None,
            'deactivated': False,
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
            'lastChangedParameterType': '',
            'lastImportPatternFilename': '',
            'lastImportPatternFilter': '',
            'synFileTimestamp': None,
            'forceSynFile': False,
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
            'masterSynthCodeL': 'sL',
            'masterSynthCodeR': 'sR',
            'masterCodeL': 'masterL',
            'masterCodeR': 'masterR',
            'timeCode': 'time',
        }
        self.info = deepcopy(self.defaultInfo)
        self.patterns = []
        self.amaysyn = None

        self.patternColors = {}

        self.globalState['argGivenTitle'] = sys.argv[1].split('.')[0] if len(sys.argv) > 1 else None

        if self.globalState['argGivenTitle'] is not None:
            self.globalState.update({
                'maysonFile': f"{self.globalState['argGivenTitle']}.mayson",
                'lastDirectory': './'
            })
            self.autoSaveGlobals()
        else:
            loadGlobalState = {}
            try:
                file = open(globalStateFile, 'r')
                loadGlobalState = json.load(file)
                file.close()
            except FileNotFoundError:
                pass

            self.globalState.update(loadGlobalState)

        if 'maysonFile' not in self.globalState or self.globalState['maysonFile'] == '':
            self.loadAndImportMayson()
        else:
            self.importMayson()

        self.undoStack = []
        self.undoStep = 0
        self.pushUndoStack()

        self.initPurgeMap()

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

    def updateLoop(self, state):
        self.info['loop'] = 'seamless' if state == Qt.Checked else 'none'

    def updateUseSequence(self, state):
        self.state['useSequence'] = (state == Qt.Checked)
        if self.amaysyn is not None:
            self.amaysyn.useSequenceTexture = self.state['useSequence']

    def activateNext(self):
        self.toggleActivated(
            activateTrack = self.patternWidget.active,
            activatePattern = self.trackWidget.active,
        )

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

        printDebug(self.trackWidget.active, self.patternWidget.active, self.synthPatternWidget.active, self.drumPatternWidget.active, "...", self.patternWidget == self.synthPatternWidget, self.patternWidget == self.drumPatternWidget)

        if activateTrack:
            self.trackWidget.setFocus()
        elif activatePattern:
            self.patternWidget.setFocus()
        elif activateSynth:
            self.synthWidget.setFocus()

    def toggleGlobalDeactivedState(self, active = None):
        if active is None:
            self.globalState['deactivated'] = not self.globalState.get('deactivated', True)
        else:
            self.globalState['deactivated'] = not active
        self.repaint()

    def newSong(self, title = None):
        proceed = title is not None
        if not proceed:
            title, proceed = QInputDialog.getText(self, 'New Song', 'Title:', QLineEdit.Normal, '')
        if not proceed:
            return
        self.state['title'] = title or 'QoolMusic'
        self.globalState['maysonFile'] = f"{self.state['title']}.mayson"
        self.info = deepcopy(self.defaultInfo)
        self.state['forceSynFile'] = False
        self.ensureSynFile()
        self.setModelsFromData(None)
        self.shufflePatternColors()
        self.patternWidget.setPattern(None)
        self.updateUIfromState()

    def loadAndImportMayson(self):
        name, _ = QFileDialog.getOpenFileName(self, 'Load MAYSON file', '', 'aMaySyn *.mayson(*.mayson)')
        if name == '':
            if self.state.get('title', None) is None:
                self.newSong()
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
            maysonData = json.load(file, cls = MaysonDecoder)
        except FileNotFoundError:
            if self.globalState['argGivenTitle'] is not None:
                self.newSong(title = self.globalState['argGivenTitle'])
            else:
                print(f"{self.globalState['maysonFile']} could not be imported. Choose again.")
                self.loadAndImportMayson()
        else:
            file.close()

        if maysonData == {}:
            return

        for key in maysonData.get('state', []):
            self.state.update({key: maysonData['state'][key]})

        for key in maysonData.get('info', []):
            self.info.update({key: maysonData['info'][key]})

        if 'title' in self.info:
            self.state['title'] = self.info.pop('title')
        if 'title' not in self.state or 'synFile' not in self.state:
            self.state['title'], self.state['synFile'] = self.getTitleAndSynFromMayson(self.globalState['maysonFile'])
        if self.amaysyn is not None:
            self.amaysyn.updateState(title = self.state['title'], synFile = self.state['synFile'], info = self.info)

        self.updateAMay2yn()
        self.setModelsFromData(maysonData)
        self.checkSynFileTimestamp()
        self.renderFilePathEdit.setText(f"{self.state['title']}.glsl")
        self.shufflePatternColors()

        self.trackWidget.activate()
        tracks = self.trackModel.tracks
        if tracks:
            if tracks[0].modules:
                self.trackWidget.select(tracks[0], tracks[0].modules[0])
            else:
                self.trackWidget.select(tracks[0])


    def exportMayson(self, saveAs = False):
        self.toggleGlobalDeactivedState(active = False)
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
            'synths': self.synthModel.synths,
            'drumkit': self.drumModel.stringList(),
            'paramOverrides': self.synthModel.paramOverrides,
            'randomValues': self.synthModel.randomValues,
        }
        fn = open(self.globalState['maysonFile'], 'w')
        print(f"Export to {self.globalState['maysonFile']}")
        json.dump(data, fn, cls = MaysonEncoder)
        fn.close()
        self.toggleGlobalDeactivedState(active = True)

    def ensureSynFile(self, copySynFile = None):
        if self.state['forceSynFile']:
            return

        synFile = f"{self.globalState['lastDirectory']}{self.state['title']}.syn"
        self.state['synFile'] = synFile

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

    def checkSynFileTimestamp(self):
        actualTimestamp = self.getActualSynFileTimestamp()
        storedTimestamp = self.state.get('synFileTimestamp', None)
        if storedTimestamp != actualTimestamp:
            if storedTimestamp is None:
                question = f"Seems you never loaded this .syn file, ever.\n\nLoad {self.state['synFile']}?"
            else:
                stringActual = datetime.fromtimestamp(actualTimestamp).strftime("%Y/%m/%d %H:%M:%S")
                stringStored = datetime.fromtimestamp(storedTimestamp).strftime("%Y/%m/%d %H:%M:%S")
                question = f"Stored Timestamp: {stringStored}.\nActual Timestamp: {stringActual}\n\nReload {self.state['synFile']}?"
            query = QMessageBox.question(self, 'Load .syn?', question, QMessageBox.Yes | QMessageBox.No)
            if query == QMessageBox.Yes:
                self.loadSynFile()
                self.autoSave()
                # for now, there's no way to change the syn parameters in the program (only defined params and randoms). but eventually, it would go like this:
                # store the "overwrites"
                # when loading, parse each object anyway
                # find the differences, especially when they collide with overwrites
                # ask the user about them

    def getTitleAndSynFromMayson(self, maysonFile):
        synFile = '.'.join(maysonFile.split('.')[:-1]) + '.syn'
        title = '.'.join(path.basename(maysonFile).split('.')[:-1])
        return title, synFile

    def loadSynFile(self):
        self.toggleGlobalDeactivedState(active = False)
        print("LOAD:", self.state['title'], self.state['synFile'])
        if self.amaysyn is not None:
            self.amaysyn.updateState(title = self.state['title'], synFile = self.state['synFile'])
            self.amaysyn.tokenizeSynFile()
            self.amaysyn.parseSynths(skipExisting = False)
            self.patternModel.updateDrumPatterns(self.amaysyn.drumkitMap)
        self.synthModel.setSynths(self.amaysyn.synths)
        self.drumModel.setStringList(self.amaysyn.drumkit)
        self.state['synFileTimestamp'] = self.getActualSynFileTimestamp()
        self.toggleGlobalDeactivedState(active = True)

    def autoSave(self):
        self.autoSaveGlobals()
        print("fully implement autosave.... yet to do")

    def autoSaveGlobals(self):
        file = open(globalStateFile, 'w')
        json.dump(self.globalState, file)
        file.close()


    def keyPressEvent(self, event):
        key = event.key()
        keytext = event.text()
        self.setModifiers(event)

        if key == Qt.Key_Escape:
            self.close()

        if self.noModifiers:

            if key == Qt.Key_F1:
                self.shufflePatternColors()
            elif key == Qt.Key_F9:
                self.trackWidget.debugOutput()
            elif key == Qt.Key_F10:
                self.patternWidget.debugOutput()
            elif key == Qt.Key_F11:
                self.synthWidget.debugOutput()
            elif key == Qt.Key_F12:
                self.debugOutput()

        elif self.ctrlPressed and not self.shiftPressed:

            if key == Qt.Key_Tab:
                self.activateNext()

            elif key == Qt.Key_Return:
                self.renderWhateverWasLast()

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
                elif key == Qt.Key_Right:
                    self.trackWidget.selectModuleOnTrack(+1)
                elif key == Qt.Key_Left:
                    self.trackWidget.selectModuleOnTrack(-1)
                elif key == Qt.Key_Home:
                    self.trackWidget.selectFirstModuleOnTrack()
                elif key == Qt.Key_End:
                    self.trackWidget.selectLastModuleOnTrack()

                elif key == Qt.Key_C:
                    self.trackWidget.cloneCurrentModuleNearby()
                elif key == Qt.Key_Delete:
                    self.trackWidget.deleteCurrentModule()


            elif self.ctrlPressed and not self.shiftPressed:

                if key == Qt.Key_Plus:
                    self.trackModel.addTrack()
                elif key == Qt.Key_Asterisk:
                    self.trackModel.cloneTrack()
                elif key == Qt.Key_Minus:
                    self.trackModel.deleteTrack()

                elif key == Qt.Key_Left:
                    self.trackModel.moveAllModules(-1)
                elif key == Qt.Key_Right:
                    self.trackModel.moveAllModules(+1)

                elif key == Qt.Key_H:
                    self.rehashPattern()


            elif not self.ctrlPressed and self.shiftPressed:

                if key == Qt.Key_Left:
                    self.trackModel.moveCurrentModule(-1)
                elif key == Qt.Key_Right:
                    self.trackModel.moveCurrentModule(+1)
                elif key == Qt.Key_Up:
                    self.trackWidget.moveCurrentModuleToTrack(-1)
                elif key == Qt.Key_Down:
                    self.trackWidget.moveCurrentModuleToTrack(+1)


            elif self.ctrlPressed and self.shiftPressed:

                if key == Qt.Key_Up:
                    self.trackModel.transposeModule(+12)
                elif key == Qt.Key_Down:
                    self.trackModel.transposeModule(-12)
                elif key == Qt.Key_Left:
                    self.trackModel.moveAllModulesFromBeatOn(-1, self.getModuleOn())
                elif key == Qt.Key_Right:
                    self.trackModel.moveAllModulesFromBeatOn(+1, self.getModuleOn())

            self.trackWidget.update()

        elif self.patternWidget.active:

            if not self.ctrlPressed and not self.shiftPressed:

                if key == Qt.Key_Right:
                    self.patternWidget.selectNextNote(+1)
                elif key == Qt.Key_Left:
                    self.patternWidget.selectNextNote(-1)

                elif key == Qt.Key_V:
                    self.setParameterFromNumberInput('vel')
                elif key == Qt.Key_P:
                    self.setParameterFromNumberInput('pan')
                elif key == Qt.Key_G:
                    self.setParameterFromNumberInput('slide')
                elif key == Qt.Key_X:
                    self.setParameterFromNumberInput('aux')

                elif key == Qt.Key_Delete:
                    self.patternWidget.deleteNote(self.getNote())

                if keytext:
                    if keytext.isdigit() or keytext in ['.', '-']:
                        self.setNumberInput(keytext)
                    else:
                        self.setNumberInput()

            elif self.ctrlPressed and not self.shiftPressed:

                if key == Qt.Key_Right:
                    self.changePatternLength(+1)
                elif key == Qt.Key_Left:
                    self.changePatternLength(-1)

                elif key == Qt.Key_P:
                    self.openParameterDialog()

            elif not self.ctrlPressed and self.shiftPressed:

                if key == Qt.Key_Right:
                    self.patternWidget.moveAllNotes(+1)
                elif key == Qt.Key_Left:
                    self.patternWidget.moveAllNotes(-1)
                elif key == Qt.Key_Up:
                    self.patternWidget.shiftAllNotes(+1)
                elif key == Qt.Key_Down:
                    self.patternWidget.shiftAllNotes(-1)

            elif self.ctrlPressed and self.shiftPressed:

                if key == Qt.Key_Right:
                    self.patternWidget.stretchAllNotes(+1)
                elif key == Qt.Key_Left:
                    self.patternWidget.stretchAllNotes(-1)


        elif self.synthWidget.active:
            pass


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
            self.shiftPressed = event.modifiers() & Qt.ShiftModifier == Qt.ShiftModifier
            self.ctrlPressed = event.modifiers() & Qt.ControlModifier == Qt.ControlModifier
            self.altPressed = event.modifiers() & Qt.AltModifier == Qt.AltModifier
        self.noModifiers = not self.shiftPressed and not self.ctrlPressed and not self.altPressed

    def paintEvent(self, event):
        if self.globalState['deactivated']:
            qp = QPainter()
            qp.begin(self)
            qp.fillRect(event.rect().left(), event.rect().top(), event.rect().width(), event.rect().height(), deactivatedColor)
            qp.end()

    def closeEvent(self, event):
        QApplication.quit()


    def setModelsFromData(self, data):
        if data is not None:
            tracks, patterns, synths, drumkit, paramOverrides, randomValues = self.decodeMaysonData(data)
        else:
            self.updateAMay2yn()
            self.amaysyn.tokenizeSynFile()
            self.amaysyn.parseSynths(skipExisting = True)
            tracks = [Track()]
            patterns = [Pattern()]
            synths = self.amaysyn.synths
            drumkit = self.amaysyn.drumkit
            paramOverrides = {}
            randomValues = {}

        self.trackModel.setTracks(tracks)
        self.patternModel.setPatterns(patterns)
        self.synthModel.setSynths(synths)
        self.synthModel.paramOverrides = paramOverrides
        self.synthModel.randomValues = randomValues
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
                    if module.patternHash == pattern._hash:
                        module.setPattern(pattern)
            tracks.append(track)

        self.amaysyn.tokenizeSynFile()

        synths = []
        forbiddenNames = ['D_Drums', 'G_GFX', '__None']
        for encodedSynth in data['synths']:
            if encodedSynth['name'] in forbiddenNames:
                continue
            synth = decodeSynth(encodedSynth)
            self.amaysyn.parseSingleSynth(synth.name)
            nodeTree = self.amaysyn.getNodeTreeIfMainSrcMatches(synth.name, synth.mainSrc)
            if nodeTree is not None:
                synth.nodeTree = nodeTree
            synths.append(synth)

        drumkit = data['drumkit']

        paramOverrides = {}
        if 'paramOverrides' in data:
            for paramID in data['paramOverrides']:
                param = decodeParam(data['paramOverrides'][paramID])
                paramOverrides[paramID] = param

        randomValues = {}
        if 'randomValues' in data:
            for randomID in data['randomValues']:
                randomValue = decodeRandomValue(data['randomValues'][randomID])
                randomValues[randomID] = randomValue

        return tracks, patterns, synths, drumkit, paramOverrides, randomValues


    def pushUndoStack(self):
        if self.undoStep > 0:
            self.undoStack = self.undoStack[:-self.undoStep]
            self.undoStep = 0
        self.state.update({
            'currentTrackIndex': self.trackModel.currentTrackIndex,
            'currentModuleIndex': self.getTrack().currentModuleIndex if self.getTrack() is not None else None,
            'currentNoteIndex': self.getModulePattern().currentNoteIndex if self.getModulePattern() is not None else None,
        })
        undoObject = {
            'state': self.state,
            'info': self.info,
            'tracks': self.trackModel.tracks,
            'patterns': self.patternModel.patterns,
            'synths': self.synthModel.synths,
            'drumkit': self.drumModel.stringList(),
            'paramOverrides': self.synthModel.paramOverrides,
            'randomValues': self.synthModel.randomValues
        }
        self.undoStack.append(json.dumps(undoObject, cls = MaysonEncoder))

    def loadUndoStep(self, relativeStep):
        self.toggleGlobalDeactivedState(active = False)
        maxUndoStep = len(self.undoStack) - 1
        self.undoStep = clip(self.undoStep + relativeStep, 0, maxUndoStep)
        undoObject = json.loads(self.undoStack[maxUndoStep - self.undoStep])
        self.state = undoObject['state']
        self.info = undoObject['info']
        self.setModelsFromData(undoObject)
        self.resetWidgets()
        self.toggleGlobalDeactivedState(active = True)

    def openSettingsDialog(self):
        settingsDialog = SettingsDialog(self)
        if settingsDialog.exec_():
            self.info['BPM'] = settingsDialog.bpmList()
            self.trackWidget.updateBpmList(self.info['BPM'])
            self.info['level_syn'], self.info['level_drum'] = settingsDialog.getLevels()
            self.info['masterCodeL'] = settingsDialog.masterCodeL()
            self.info['masterCodeR'] = settingsDialog.masterCodeR()
            self.info['masterSynthCodeL'] = settingsDialog.masterSynthCodeL()
            self.info['masterSynthCodeR'] = settingsDialog.masterSynthCodeR()
            self.info['timeCode'] = settingsDialog.timeCode()
            self.info['beatQuantum'] = 1/float(settingsDialog.beatQuantumDenominatorSpinBox.value())
            self.info['barsPerBeat'] = settingsDialog.barsPerBeatSpinBox.value()
            settingsDialogSynFile = settingsDialog.synFileEdit.text()
            self.state['forceSynFile'] = path.exists(settingsDialogSynFile)
            if self.state['forceSynFile']:
                if self.state['synFile'] != settingsDialogSynFile:
                    self.state['synFile'] = settingsDialogSynFile
                    self.loadSynFile()

    def openImportPatternDialog(self):
        importPatternDialog = ImportPatternDialog(self, filename = self.state['lastImportPatternFilename'], filter = self.state['lastImportPatternFilter'])
        if importPatternDialog.exec_():
            for pattern in importPatternDialog.parsedPatterns:
                self.addPattern(pattern)
        self.state['lastImportPatternFilename'] = importPatternDialog.xmlFilename
        self.state['lastImportPatternFilter'] = importPatternDialog.filter

    def openParameterDialog(self):
        parameterDialog = ParameterDialog(self, pattern = self.getModulePattern(), parameterType = self.state['lastChangedParameterType'])
        if parameterDialog.exec_():
            self.state['lastChangedParameterType'] = parameterDialog.parameterType
            self.autoSave()

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

    def getModuleOn(self, offset = 0):
        module = self.getModule(offset)
        return module.getModuleOn() if module is not None else None

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

    def getNote(self):
        return self.getModulePattern().getNote()

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
        if 'currentModuleIndex' in self.state and self.getTrack() is not None:
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
            self.state['lastChangedParameterType'] = parameter
        self.getNote().setParameter(parameter, self.state['lastNumberInput'])
        self.patternWidget.select(self.getNote())

    def setRandomSynth(self):
        track = self.getTrack()
        if track:
            track.setSynth(synthType = track.synthType, name = self.getRandomSynthName(track.synthType))

    def getRandomSynthName(self, synthType):
        if synthType != SYNTHTYPE or self.synthModel.rowCount() == 0:
            return synthType
        return choice(self.synthModel.synthList())

    def reshuffleAllRandomValues(self):
        if self.amaysyn is None:
            print("aMay2ynBuilder not initialized. Doesn't work that way, yet...")
            return
        for randomForm in self.amaysyn.stored_randoms:
            randomValue = self.synthModel.randomValues.get(randomForm['id'], RandomValue(randomForm))
            randomValue.reshuffle()
            self.synthModel.setRandomValue(randomValue)

    def getRandom(self, randomID):
        return self.synthModel.randomValues.get(randomID, None)

    def reshuffleAllRandomValuesManyTimes(self):
        dialog = RandomizerDialog(self)
        if dialog.exec_():
            self.writeWavCheckBox.setChecked(True)
            print(self.amaysyn.MODE_renderWav)
            self.amaysyn.initWavOut(dialog.outDirEdit.text())
            self.amaysyn.MODE_justRenderWAV = True
            for number in range(dialog.numberSpin.value()):
                print(f"RANDOMIZE {number + 1} / {dialog.numberSpin.value()}")
                self.reshuffleAllRandomValues()
                self.renderWhateverWasLast()
            self.amaysyn.MODE_justRenderWAV = False

    def getActualSynFileTimestamp(self):
        if self.state.get('synFile', None) is not None:
            return path.getmtime(self.state['synFile'])


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

    def loadSynth(self, synthName):
        if self.getTrack().synthName == self.synthWidget.getSynthName():
            return
        if self.amaysyn is None:
            print("Can't load, AMay2yn is not initialized!")
            return
        if not self.amaysyn.isTokenized():
            print("Can't load, AMay2yn hasn't read a .syn file once yet!")
            return
        self.amaysyn.parseSingleSynth(synthName)
        synth = self.amaysyn.getSynth(synthName)
        if synth is not None:
            self.synthModel.updateSynth(synth) # TODO: technical debt... Actually, the MayzynBuilder (self.amaysyn) shouldn't hold all the Synths as well. Remove when having some time.
        self.synthWidget.setSynth(synth)

    def trackSelected(self, track):
        self.loadSynth(track.synthName)

    def trackChanged(self):
        if not self.getTrack().isEmpty():
            self.pushUndoStack()
        self.loadSynth(self.getTrack().synthName)

    def trackTypeChanged(self):
        synthType = self.trackWidget.model.currentTrackType()
        if synthType == DRUMTYPE:
            self.drumPatternWidget.active = self.patternWidget.active
            self.patternWidget = self.drumPatternWidget
        else:
            self.synthPatternWidget.active = self.patternWidget.active
            self.patternWidget = self.synthPatternWidget
        self.patternGroupLayout.setCurrentWidget(self.patternWidget)

    def synthPatternChanged(self):
        self.pushUndoStack()

    def drumPatternChanged(self):
        self.pushUndoStack()

    def paramChanged(self, param):
        self.synthModel.setParamOverride(param)
        self.pushUndoStack()

    def randomsChanged(self, randomValues):
        self.synthModel.setRandomValues(randomValues)
        self.pushUndoStack()

    def addPattern(self, pattern = None):
        if pattern is None:
            return
        index = self.patternModel.getIndexOfPattern(pattern)
        if index is None:
            index = self.patternModel.rowCount() - 1
        self.patternModel.addRow(index, pattern)
        self.patternColors[pattern._hash] = self.randomColor()

    def purgeUnusedPatterns(self):
        usedPatternHashs = [module.patternHash for track in self.trackModel.tracks for module in track.modules]
        self.patternModel.purgeUnusedPatterns(usedPatternHashs)
        self.purgeDuplicatePatterns()

    def purgeDuplicatePatterns(self):
        self.initPurgeMap()
        for pattern in self.patternModel.patterns[:]:
            if self.lastPurgeMap[pattern._hash] != pattern._hash or pattern.isEmpty():
                continue
            other_patterns = [p for p in self.patternModel.patterns if p != pattern]
            for other_p in other_patterns:
                if other_p.isEmpty():
                    continue
                potentiallyTransposed = pattern.notes[0].note_pitch - other_p.notes[0].note_pitch
                if pattern.isDuplicateOf(other_p, transposed = potentiallyTransposed):
                    for m in self.trackModel.getAllModulesOfHash(other_p._hash):
                        m.setPattern(pattern)
                        m.transpose -= potentiallyTransposed
                    self.patternModel.removePattern(other_p)
                    self.lastPurgeMap[other_p._hash] = pattern._hash
                    print(f"Removed duplicate of {pattern.name}: {other_p.name}")

    def initPurgeMap(self):
        self.lastPurgeMap = {}
        for pattern in self.patternModel.patterns:
            self.lastPurgeMap[pattern._hash] = pattern._hash

    def changePatternLength(self, beatsInc):
        pattern = self.getModulePattern()
        self.patternModel.extendPattern(pattern, beatsInc)
        self.patternWidget.setPattern(self.getModulePattern())
        self.patternWidget.update()
        self.trackWidget.syncModulesToPatternChange(pattern)
        self.pushUndoStack()

######################### SYNATIZE FUNCTIONALITY #####################

    def hardcopySynth(self, synth, randoms):
        if synth.type != SYNTHTYPE:
            print("tried to hardcopy synth that is not a SYNTH type. Can't.")
            return

        nameSuggestion = findFreeSerial(f"{synth.name}.", self.synthModel.synthList())
        name, ok = QInputDialog.getText(self, "Hardcopy Synth", f"Clone '{synth.name}' under new Name:", QLineEdit.Normal, nameSuggestion)
        if not ok:
            return
        try:
            formTemplate = next(form for form in self.amaysyn.last_synatized_forms if form['id'] == synth.name)
            formType = formTemplate['type']
            formMode = formTemplate.get('mode', [])
            formBody = ' '.join(f"{key}={formTemplate[key]}" for key in formTemplate if key not in  ['type', 'id', 'mode'])
            if formMode:
                formBody += ' mode=' + ','.join(formMode)
        except StopIteration:
            print("Current synth is not compiled yet. Do so and try again.")
            return
        except:
            print("Could not CLONE HARD:", synth.name, formTemplate)
            raise
        else:
            with open(self.state['synFile'], mode='a') as synFileHandle:
                synFileHandle.write(f'\n{formType}    {name}    {formBody}')
            self.loadSynFile()


    def randomizeSynatizer(self):
        print("this is heavy stuff!")
        quit() # but when is this called..?
        # TODO: synatize should tell us which main forms include random content ;)

    def updateAMay2yn(self):
        if self.amaysyn is None:
            self.amaysyn = May2ynBuilder(self, title = self.state['title'], synFile = self.state['synFile'], info = self.info)
        else:
            self.amaysyn.updateState(title = self.state['title'], synFile = self.state['synFile'], info = self.info)
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
        elif self.state['lastRendered'] == 'note':
            self.renderNote()
        elif self.state['lastRendered'] == 'file':
            self.renderFile()
        else:
            self.renderSong()

    def renderModule(self, _ = None, synthName = None):
        self.state['lastRendered'] = 'module'
        track = deepcopy(self.getTrack())
        if synthName is not None:
            track.setSynth(name = synthName)
        track.mute = False
        modInfo = deepcopy(self.info)
        modInfo['B_offset'] = self.getModule().getModuleOn()
        modInfo['B_stop'] = self.getModule().getModuleOff()
        self.toggleGlobalDeactivedState(active = False)
        self.amaysyn.updateState(title = self.state['title'], info = modInfo)
        self.amaysyn.extra_time_shift = self.state.get('extraTimeShift', 0) # THIS HAS SOME DEBUGGING REASONS
        shader = self.amaysyn.build(tracks = [track], patterns = [self.getModulePattern()])
        self.amaysyn.updateState(info = self.info)
        self.executeShader(shader)
        self.toggleGlobalDeactivedState(active = True)

    def renderTrack(self):
        self.state['lastRendered'] = 'track'
        anyOverlap = self.trackModel.findModuleOverlap(onlyCurrentTrack = True)
        if anyOverlap is not None:
            QMessageBox.critical(self, 'Overlap!', anyOverlap)
            return
        track = self.getTrack()
        restoreMute = track.mute
        track.mute = False
        self.amaysyn.extra_time_shift = self.state.get('extraTimeShift', 0)
        self.toggleGlobalDeactivedState(active = False)
        self.amaysyn.updateState(title = self.state['title'], info = self.info)
        shader = self.amaysyn.build(tracks = [track], patterns = self.patternModel.patterns)
        track.mute = restoreMute
        self.executeShader(shader)
        self.toggleGlobalDeactivedState(active = True)

    def renderSong(self):
        self.state['lastRendered'] = 'song'
        anyOverlap = self.trackModel.findModuleOverlap()
        if anyOverlap is not None:
            QMessageBox.critical(self, 'Overlap!', anyOverlap)
            return
        self.amaysyn.extra_time_shift = self.state.get('extraTimeShift', 0)
        self.toggleGlobalDeactivedState(active = False)
        self.amaysyn.updateState(title = self.state['title'], info = self.info)
        shader = self.amaysyn.build(tracks = self.trackModel.tracks, patterns = self.patternModel.patterns)
        self.executeShader(shader)
        self.toggleGlobalDeactivedState(active = True)

    def renderNote(self, _ = None, synthName = None):
        self.state['lastRendered'] = 'note'
        track = deepcopy(self.getTrack())
        if synthName is not None:
            track.setSynth(name = synthName)
        track.mute = False
        note = deepcopy(self.getNote())
        if note is None:
            print('No Note Selected')
            return
        note.moveNoteOn(0)
        pattern = Pattern(length = note.note_len + 2)
        pattern.notes = [note]
        track.modules = [Module(0, pattern)]
        modInfo = deepcopy(self.info)
        modInfo['B_offset'] = 0
        modInfo['B_stop'] = pattern.length
        self.toggleGlobalDeactivedState(active = False)
        self.amaysyn.updateState(title = self.state['title'], info = modInfo)
        self.amaysyn.extra_time_shift = 0
        shader = self.amaysyn.build(tracks = [track], patterns = [pattern]) # self.getModulePattern()
        self.amaysyn.updateState(info = self.info)
        self.executeShader(shader)
        self.toggleGlobalDeactivedState(active = True)

    def renderFile(self, _ = None):
        self.state['lastRendered'] = 'file'
        glslFileName = self.renderFilePathEdit.text()
        try:
            glslFile = open(glslFileName)
            glslShader = glslFile.read()
            glslFile.close()
            self.renderFilePathEdit.setStyleSheet("background-color: white;")
        except FileNotFoundError:
            print(f"File {glslFileName} not found.")
            self.renderFilePathEdit.setStyleSheet("background-color: red;")
            return
        tryToReadSongLength = re.findall(r"#define SONGLENGTH [\d\.]+", glslShader, flags=re.MULTILINE)
        songLength = float(tryToReadSongLength[0].split()[-1]) if len(tryToReadSongLength) == 1 else None
        self.toggleGlobalDeactivedState(active = False)
        self.amaysyn.updateState(title = glslFileName.replace('.glsl',''), song_length = songLength)
        self.executeShader(glslShader)
        self.toggleGlobalDeactivedState(active = True)


    def executeShader(self, shader):
        if shader is None:
            print("Called executeShader() with a shader of None.")
            return
        sequenceLength = len(self.amaysyn.sequence) if self.amaysyn.sequence is not None else 0
        if not self.amaysyn.useSequenceTexture and sequenceLength > pow(2, 14):
            QMessageBox.critical(self, "I CAN'T", f"Either switch to using the Sequence Texture (ask QM), or reduce the sequence size by limiting the offset/stop positions or muting tracks.\nCurrent sequence length is:\n{sequenceLength} > {pow(2,14)}")
            return

        self.bytearray = self.amaysyn.executeShader(shader, self.samplerate, self.texsize, renderWAV = self.state['writeWAV'])
        if not self.amaysyn.MODE_justRenderWAV:
            self.audiobuffer = QBuffer(self.bytearray)
            self.audiobuffer.open(QIODevice.ReadOnly)
            self.audiooutput.stop()
            self.audiooutput.start(self.audiobuffer)

###################################################################

    def rehashPattern(self):
        pattern = self.getModulePattern()
        print("speaking of pattern", pattern.name, pattern._hash)
        pattern.rehash()
        self.getModule().patternHash = pattern._hash
        self.patternColors[pattern._hash] = self.randomColor()

        print("rehashed and is now", pattern._hash)


    def debugOutput(self):
        print('\n\n')
        print(self.state['synFile'], self.state['synFileTimestamp'])
        print("SYNTHS:")
        for index, s in enumerate(self.synthModel.synths):
            print(index + 1, s.name, s.type)

        print('\n')
        print("TITLE:", self.state['title'])
        if self.getTrack() is not None:
            print("TRACK NAME:", self.getTrack().name)
            print("TRACK TYPE:", self.getTrack().synthType)
            if self.getTrack().synthType == SYNTHTYPE:
                synthObj = self.amaysyn.getSynth(self.getTrack().synthName)
                if synthObj is not None:
                    synthObj.parseNodeTreeFromSrc(None, None, verbose = True)
                    print("TRACK SYNTH:")
                    synthObj.printNodeTree()
                    print("USED PARAMS:", synthObj.nodeTree.usedParams)
                    print("USED RANDOMS:", synthObj.nodeTree.usedRandoms)

        if self.amaysyn is not None:
            print("\nTIME OF EVERY BEAT:")
            for beat in range(ceil(self.trackModel.totalLength())):
                print("BEAT", beat, "\t TIME", self.amaysyn.getTimeOfBeat_raw(beat, self.info['BPM']))

        print()

        for pattern in self.patternModel.patterns:
            print(pattern._hash, " -- ", pattern.name)

        print()

###################################################################

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())
