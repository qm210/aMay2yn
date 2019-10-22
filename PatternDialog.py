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

        if module is None and pattern is None and beat is None:
            print("called PatternDialog but gave neither module, nor pattern & beat")
            return

        self.layout = QtWidgets.QVBoxLayout(self)

        self.topLayout = QtWidgets.QHBoxLayout()
        self.modOnSpinner = QtWidgets.QSpinBox(self)
        self.modOnSpinner.setRange(0, 9999)
        self.modOnSpinner.setPrefix('Start @ Beat ')
        self.topLayout.addWidget(self.modOnSpinner)

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

        self.modOnSpinner.valueChanged.connect(self.moveModule)
        self.patternList.selectionModel().currentChanged.connect(self.selectPattern)
        self.newPatternButton.clicked.connect(self.newPattern)
        self.importPatternButton.clicked.connect(self.openImportPatternDialog)

        self.init(module)

        # TODO: think about introducing a separate module volume

    def init(self, module):
        if module is not None:
            self.module = module
        else:
            self.module = may2Objects.Module(mod_on = self.initBeat, pattern = self.getPattern())

        self.modOnSpinner.setValue(self.module.mod_on)
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
        self.init(self.module)

    def moveModule(self):
        if self.module is not None:
            beat = self.modOnSpinner.value()
            self.module.move(beat)
            self.checkCollisions()

    def newPattern(self):
        # self.patternModel.addPattern()
        # then update pattern list and select new
        pass

    def getPattern(self):
        self.update()
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