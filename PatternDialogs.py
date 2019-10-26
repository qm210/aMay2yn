from PyQt5 import QtWidgets, QtCore
from random import randint
from copy import deepcopy
from math import ceil
import xml.etree.ElementTree as ET

import may2Objects


class PatternDialog(QtWidgets.QDialog):

    WIDTH = 600
    HEIGHT = 800

    def __init__(self, parent, track, module = None, pattern = None, beat = None, *args, **kwargs):
        super(PatternDialog, self).__init__(parent, *args, **kwargs)
        self.setWindowTitle('Pattern Dialog')
        self.setGeometry(parent.x() + 0.5 * (parent.width() - self.WIDTH), parent.y() + 0.5 * (parent.height() - self.HEIGHT), self.WIDTH, self.HEIGHT)
        self.parent = parent
        self.track = track
        self.synthType = track.synthType
        self.patternModel = self.createFilteredModel()
        self.patternIndex = self.patternModel.getIndexOfPattern(pattern) if pattern is not None \
            else self.patternModel.getPatternIndexOfHash(module.patternHash) if module is not None else 0
        self.initPatternIndex = self.patternIndex
        self.initBeat = beat if module is None else module.mod_on
        self.initTranspose = 0 if module is None else module.transpose

        if module is None and pattern is None and beat is None:
            print("called PatternDialog but gave neither module, nor pattern & beat")
            return

        self.layout = QtWidgets.QVBoxLayout(self)

        self.topLayout = QtWidgets.QHBoxLayout()
        self.modOnSpinBox = QtWidgets.QSpinBox(self)
        self.modOnSpinBox.setRange(0, 9999)
        self.modOnSpinBox.setPrefix('Start @ Beat ')
        self.topLayout.addWidget(self.modOnSpinBox)

        self.transposeSpinBox = QtWidgets.QSpinBox(self)
        self.transposeSpinBox.setRange(-96, 96)
        self.transposeSpinBox.setPrefix('transpose ')
        self.transposeSpinBox.setSuffix(' semitones')
        self.transposeSpinBox.setSingleStep(12)
        self.transposeSpinBox.setEnabled(self.track.synthType == may2Objects.SYNTHTYPE)
        self.topLayout.addWidget(self.transposeSpinBox)

        self.layout.addLayout(self.topLayout)

        self.modOnCollisionLabel = QtWidgets.QLabel('MODULE COLLISION!')
        self.modOnCollisionLabel.setStyleSheet('QLabel {color: red;}')
        self.modOnCollisionLabel.hide()
        self.modOnCollisionPlaceHolder = QtWidgets.QLabel('')
        self.layout.addWidget(self.modOnCollisionLabel)
        self.layout.addWidget(self.modOnCollisionPlaceHolder)

        self.buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Reset | QtWidgets.QDialogButtonBox.Cancel, self)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.clicked.connect(self.clickOther)
        self.buttonBox.rejected.connect(self.cancel)
        self.okButton = self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok)
        if module is None:
            self.okButton.setText('New')
            self.okButton.setEnabled(False)

        self.patternList = QtWidgets.QListView(self)
        self.patternList.setModel(self.patternModel)
        self.layout.addWidget(self.patternList)

        self.buttonGrid = QtWidgets.QGridLayout()

        self.newPatternButton = QtWidgets.QPushButton('New Pattern', self)
        self.clonePatternButton = QtWidgets.QPushButton('Clone Pattern', self)
        self.purgeEmptyButton = QtWidgets.QPushButton('Purge Empty', self)
        self.purgeUnusedbutton = QtWidgets.QPushButton('Purge Unused', self)

        self.buttonGrid.addWidget(self.newPatternButton, 0, 0)
        self.buttonGrid.addWidget(self.clonePatternButton, 0, 1)
        self.buttonGrid.addWidget(self.purgeEmptyButton, 1, 0)
        self.buttonGrid.addWidget(self.purgeUnusedbutton, 1, 1)
        self.layout.addLayout(self.buttonGrid)

        self.importPatternButton = QtWidgets.QPushButton('Import LMMS patterns', self)
        self.layout.addWidget(self.importPatternButton)

        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)

        self.modOnSpinBox.valueChanged.connect(self.moveModule)
        self.transposeSpinBox.valueChanged.connect(self.transposeModule)
        self.patternList.selectionModel().currentChanged.connect(self.selectPattern)
        self.newPatternButton.clicked.connect(self.newPattern)
        self.clonePatternButton.clicked.connect(self.clonePattern)
        self.importPatternButton.clicked.connect(self.openImportPatternDialog)

        self.init(module)

        # TODO: think about introducing a separate module volume

    def init(self, module):
        if module is not None:
            self.module = module
        else:
            self.module = may2Objects.Module(mod_on = self.initBeat, pattern = self.getPattern())

        self.modOnSpinBox.setValue(self.module.mod_on)
        self.transposeSpinBox.setValue(self.module.transpose)
        if self.patternModel.rowCount() > 0:
            self.patternIndex = self.patternModel.getPatternIndexOfHash(self.module.patternHash)
            self.patternList.setCurrentIndex(self.patternModel.createIndex(self.patternIndex, 0))

    def createFilteredModel(self):
        if self.parent is None or self.synthType is None:
            return None
        return self.parent.patternModel.createFilteredModel(self.synthType)

    def clickOther(self, button):
        if button == self.buttonBox.button(QtWidgets.QDialogButtonBox.Reset):
            self.reset()

    def reset(self):
        self.module.move(self.initBeat)
        self.patternIndex = self.initPatternIndex
        self.module.setPattern(self.getPattern())
        self.module.transpose = self.initTranspose
        self.init(self.module)

    def moveModule(self, value):
        self.module.move(value)
        self.checkCollisions()

    def transposeModule(self, value):
        self.module.transpose = value

    def newPattern(self):
        newPatternDialog = NewPatternDialog(self, self.track.synthType)
        if newPatternDialog.exec_():
            pattern = newPatternDialog.createPattern()
            self.parent.addPattern(pattern)
            self.module.setPattern(pattern)
            self.accept()

    def clonePattern(self):
        self.parent.addPattern(self.getPattern(), clone = True)
        self.accept()

    def getPattern(self):
        return self.patternModel.patterns[self.patternIndex] if self.patternModel.rowCount() > 0 else None

    def selectPattern(self, current, previous):
        self.patternIndex = current.row()
        self.module.setPattern(self.getPattern())
        self.checkCollisions()
        self.okButton.setEnabled(True)

    def checkCollisions(self):
        collision = self.module.collidesWithAnyOf(self.track.modules)
        self.modOnCollisionLabel.setVisible(collision)
        self.modOnCollisionPlaceHolder.setVisible(not collision)

    def openImportPatternDialog(self):
        self.parent.openImportPatternDialog()
        print('u here')
        self.patternModel.replaceDataFromModel(self.createFilteredModel())

    def cancel(self):
        self.reset()
        self.reject()


class NewPatternDialog(QtWidgets.QDialog):

    def __init__(self, parent, type, *args, **kwargs):
        super(NewPatternDialog, self).__init__(parent, *args, **kwargs)
        self.setWindowTitle('New Pattern')
        self.parent = parent
        self.synthType = type

        self.layout = QtWidgets.QVBoxLayout(self)

        self.nameEdit = QtWidgets.QLineEdit(self)
        self.nameEdit.setPlaceholderText('Pattern Name')
        self.layout.addWidget(self.nameEdit)

        self.lengthSpin = QtWidgets.QSpinBox(self)
        self.lengthSpin.setRange(1, 999)
        self.lengthSpin.setValue(4)
        self.lengthSpin.setSuffix(' Beats')
        self.layout.addWidget(self.lengthSpin)

        if self.synthType == may2Objects.SYNTHTYPE:
            typeLabel = 'Instrument Synth'
        elif self.synthType == may2Objects.DRUMTYPE:
            typeLabel = 'Drum Synth'
        else:
            typeLabel = 'Undefined'
        self.layout.addWidget(QtWidgets.QLabel(f'Type: {typeLabel}'))

        self.buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel, self)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.layout.addWidget(self.buttonBox)

        self.setLayout(self.layout)

    def createPattern(self):
        return may2Objects.Pattern(
            name = self.nameEdit.text(),
            length = self.lengthSpin.value(),
            synthType = self.synthType
        )


class ImportPatternDialog(QtWidgets.QDialog):

    WIDTH = 500
    HEIGHT = 800

    xmlFilename = None
    patternData = []
    parsedPatterns = []
    selectedIndices = []

    LMMS_scalenotes = 192
    LMMS_scalebars = 4
    LMMS_transpose = -12

    def __init__(self, parent, **kwargs):
        self.lastFilename = kwargs.pop('filename', '')
        self.filter = kwargs.pop('filter', '')
        super(ImportPatternDialog, self).__init__(**kwargs)
        self.setGeometry(parent.x() + 0.5 * (parent.width() - self.WIDTH), parent.y() + 0.5 * (parent.height() - self.HEIGHT), self.WIDTH, self.HEIGHT)
        self.parent = parent
        self.importPatternModel = QtCore.QStringListModel()

        self.layout = QtWidgets.QVBoxLayout(self)

        self.editFilename = QtWidgets.QLineEdit(self)
        self.editFilter = QtWidgets.QLineEdit(self)
        self.patternList = QtWidgets.QListView(self)
        self.patternList.setModel(self.importPatternModel)
        self.patternList.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

        self.openFileButton = QtWidgets.QPushButton('...', self)
        self.parseButton = QtWidgets.QPushButton('Parse', self)
        self.clearButton = QtWidgets.QPushButton('Clear', self)

        self.filenameLayout = QtWidgets.QHBoxLayout()
        self.filenameLayout.addWidget(self.editFilename, 12)
        self.filenameLayout.addWidget(self.openFileButton, 1)

        self.parseLayout = QtWidgets.QHBoxLayout()
        self.parseLayout.addWidget(self.parseButton)
        self.parseLayout.addWidget(self.clearButton)

        self.buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel, self)
        self.buttonBox.accepted.connect(self.parsePatternsAndAccept)
        self.buttonBox.rejected.connect(self.rejected)

        self.importButton = self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok)
        self.importButton.setText('Import!')
        self.importButton.setEnabled(False)
        self.importButton.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        self.layout.addWidget(QtWidgets.QLabel('Filename:', self))
        self.layout.addLayout(self.filenameLayout)
        self.layout.addLayout(self.parseLayout)
        self.layout.addWidget(QtWidgets.QLabel('Filter:', self))
        self.layout.addWidget(self.editFilter)
        self.layout.addWidget(QtWidgets.QLabel('Available Patterns:', self))
        self.layout.addWidget(self.patternList)
        self.layout.addWidget(self.buttonBox)

        self.setLayout(self.layout)

        self.openFileButton.clicked.connect(self.openFileDialog)
        self.parseButton.clicked.connect(self.parseFile)
        self.clearButton.clicked.connect(self.clearFile)
        self.patternList.selectionModel().selectionChanged.connect(self.updateSelectedIndices)
        self.editFilename.textChanged.connect(self.setFilenameAndParse)
        self.editFilter.textChanged.connect(self.setFilterAndParse)

        if self.lastFilename:
            self.editFilename.setText(self.lastFilename)
            self.editFilter.setText(self.filter)
            self.parseFile()

    def setFilenameAndParse(self, text):
        self.xmlFilename = text
        self.parseFile()

    def setFilterAndParse(self, text):
        self.filter = text
        self.parseFile()

    def setData(self, patternData = []):
        self.patternData = patternData
        patternListLabels = []
        for element in patternData:
            patternListLabels.append(element['text'].replace('@', ' @ '))
        self.importPatternModel.setStringList(patternListLabels)
        self.selectedIndices = []

    def openFileDialog(self):
        # TODO: accept MMPZ files and use qUncompress()
        name, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Load LMMS file', '', 'uncompressed LMMS file *.mmp(*.mmp)')
        if name:
            self.editFilename.setText(name)

    def updateSelectedIndices(self, selection, deselection):
        for index in selection.indexes():
            self.selectedIndices.append(index.row())
        for index in deselection.indexes():
            self.selectedIndices.remove(index.row())
        self.selectedIndices.sort()
        self.importButton.setEnabled(len(self.selectedIndices) > 0)

    def parseFile(self):
        try:
            test = open(self.xmlFilename, 'r')
            head = test.read(5)
            if head != '<?xml':
                raise TypeError
            test.close()
        except FileNotFoundError:
            QtWidgets.QMessageBox.warning(self, 'File not found', f'File was not found:\n{self.XML_filename}')
            self.setData()
            self.editFilename.selectAll()
            return
        except TypeError:
            QtWidgets.QMessageBox.warning(self, 'File Error', f'File seems not to be valid XML:\n{self.XML_filename}')
            self.setData()
            self.editFilename.selectAll()
            return

        XML_root = ET.parse(self.xmlFilename).getroot()
        parseData = []
        for element in XML_root.iter():
                if element.tag == 'pattern':
                        elem_name = element.attrib['name'] or '<noname>'
                        if self.filter.lower() in elem_name[0:len(self.filter)].lower():
                            elem_pos = float(element.attrib['pos'])/self.LMMS_scalenotes
                            parseData.append({'text': f"{elem_name}@{elem_pos}", 'name': elem_name, 'pos': elem_pos, 'element': element})
        parseData.sort(key = lambda item: (item['name'], item['pos']))
        self.setData(parseData)

    def clearFile(self):
        self.setData()
        self.editFilename.clear()
        self.editFilename.setFocus()

    def parsePatternsAndAccept(self):
        self.parsedPatterns = []
        for selectedIndex in self.selectedIndices:
            xmlData = self.patternData[selectedIndex]
            selected_pattern = may2Objects.Pattern(name = xmlData['text'], synthType = may2Objects.SYNTHTYPE)
            pattern_length = 1
            for elementNote in xmlData['element']:
                if elementNote.tag == 'note':
                    note_on = float(elementNote.attrib['pos'])/self.LMMS_scalenotes
                    note_len = float(elementNote.attrib['len'])/self.LMMS_scalenotes
                    selected_pattern.notes.append(
                        may2Objects.Note(
                            note_on    = note_on,
                            note_len   = note_len,
                            note_pitch = int(float(elementNote.attrib['key']) + self.LMMS_transpose),
                            note_pan   = int(float(elementNote.attrib['pan'])),
                            note_vel   = int(float(elementNote.attrib['vol'])),
                            note_slide = 0)
                        )
                    pattern_length = max(pattern_length, ceil(note_on + note_len))
            selected_pattern.length = pattern_length
            self.parsedPatterns.append(selected_pattern)
            print(f"pattern {xmlData['text']} imported. ({len(selected_pattern.notes)} notes)")
        self.accept()

