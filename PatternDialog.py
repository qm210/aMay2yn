from PyQt5 import QtWidgets, QtCore
from random import randint
from copy import deepcopy
import may2Objects


class PatternDialog(QtWidgets.QDialog):

    WIDTH = 600
    HEIGHT = 800

    def __init__(self, parent, patternModel, track, module = None, pattern = None, beat = None, *args, **kwargs):
        super(PatternDialog, self).__init__(parent, *args, **kwargs)
        self.setWindowTitle('Pattern Dialog')
        self.setGeometry(parent.x() + 0.5 * (parent.width() - self.WIDTH), parent.y() + 0.5 * (parent.height() - self.HEIGHT), self.WIDTH, self.HEIGHT)
        self.parent = parent
        self.track = track
        self.patternModel = patternModel
        self.patternIndex = patternModel.getIndexOfPattern(pattern) if pattern is not None else patternModel.getPatternIndexOfHash(module.patternHash)
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
        self.patternIndex = self.patternModel.getPatternIndexOfHash(self.module.patternHash)
        self.patternList.setCurrentIndex(self.patternModel.createIndex(self.patternIndex, 0))

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
        return self.patternModel.patterns[self.patternIndex]

    def selectPattern(self, current, previous):
        self.patternIndex = current.row()
        self.module.setPattern(self.getPattern())
        self.checkCollisions()

    def checkCollisions(self):
        collision = self.module.collidesWithAnyOf(self.track.modules)
        self.modOnCollisionLabel.setVisible(collision)
        self.modOnCollisionPlaceHolder.setVisible(not collision)

    def openImportPatternDialog(self):
        pass

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
