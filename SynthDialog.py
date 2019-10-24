from PyQt5 import QtWidgets, QtCore
from random import randint
import may2Objects


class SynthDialog(QtWidgets.QDialog):

    WIDTH = 400
    HEIGHT = 600

    def __init__(self, parent, synthModel, track = None, *args, **kwargs):
        super(SynthDialog, self).__init__(parent, *args, **kwargs)
        self.setWindowTitle('Synth Dialog')
        self.setGeometry(parent.x() + 0.5 * (parent.width() - self.WIDTH), parent.y() + 0.5 * (parent.height() - self.HEIGHT), self.WIDTH, self.HEIGHT)
        self.parent = parent
        self.track = track
        self.synthModel = synthModel
        self.synthType = track.synthType if track is not None else may2Objects.NONETYPE

        self.layout = QtWidgets.QVBoxLayout(self)

        self.nameLayout = QtWidgets.QHBoxLayout(self)
        self.nameEdit = QtWidgets.QLineEdit(self)
        self.nameEdit.setPlaceholderText('Synth Name')
        self.renameButton = QtWidgets.QPushButton('rename',self)
        self.nameLayout.addWidget(self.nameEdit, 4)
        self.nameLayout.addWidget(self.renameButton, 1)
        self.layout.addLayout(self.nameLayout)

        self.buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Reset | QtWidgets.QDialogButtonBox.Cancel, self)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.clicked.connect(self.clickOther)
        self.buttonBox.rejected.connect(self.reject)

        self.drumCheckBox = QtWidgets.QCheckBox('Drum Track', self)
        self.drumCheckBox.stateChanged.connect(self.toggleDrumTrack)
        self.drumCheckBox.setEnabled(track is None or track.isEmpty())
        self.layout.addWidget(self.drumCheckBox)

        self.synthList = QtWidgets.QListView(self)
        self.synthList.setModel(self.synthModel)
        self.layout.addWidget(self.synthList)

        self.buttonGrid = QtWidgets.QGridLayout(self)

        self.randomSynthButton = QtWidgets.QPushButton('Random Synth', self)
        self.buttonGrid.addWidget(self.randomSynthButton, 0, 0)

        self.randomizeParametersButton = QtWidgets.QPushButton('Randomize Parameters!', self)
        self.buttonGrid.addWidget(self.randomizeParametersButton, 0, 1)

        self.previewModuleButton = QtWidgets.QPushButton('Preview Module', self)
        self.previewModuleButton.setEnabled(track is not None and not track.isEmpty())
        self.buttonGrid.addWidget(self.previewModuleButton, 1, 1)

        self.hardCopySynthButton = QtWidgets.QPushButton('HardCopy Synth', self)
        self.buttonGrid.addWidget(self.hardCopySynthButton, 1, 0)

        self.layout.addLayout(self.buttonGrid)

        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)

        self.randomSynthButton.clicked.connect(self.selectRandomSynth)
        self.randomizeParametersButton.clicked.connect(self.randomizeSynthParameters)
        self.previewModuleButton.clicked.connect(self.parent.renderModule)
        self.hardCopySynthButton.clicked.connect(self.parent.hardCopySynth)

        self.init()

    def init(self):
        self.nameEdit.setText(self.track.synthName)
        isDrumTrack = self.track.isDrumTrack()
        self.drumCheckBox.setChecked(isDrumTrack)
        if not isDrumTrack:
            synthIndex = self.synthModel.stringList().index(self.track.synthName)
            self.selectSynth(synthIndex)

    def synthName(self):
        index = self.synthList.selectedIndexes()[0].row()
        return self.synthModel.stringList()[index]

    def selectSynth(self, index):
        self.synthList.setCurrentIndex(self.synthModel.createIndex(index, 0))

    def selectRandomSynth(self):
        self.selectSynth(randint(0, self.synthModel.rowCount() - 1))

    def toggleDrumTrack(self, state):
        self.isDrumTrack = state
        self.synthList.setEnabled(not state)
        self.nameEdit.setEnabled(not state)
        self.renameButton.setEnabled(not state)

    def clickOther(self, button):
        if button == self.buttonBox.button(QtWidgets.QDialogButtonBox.Reset):
            self.init()

    def randomizeSynthParameters(self):
        self.parent.randomizeSynatizer()