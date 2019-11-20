from PyQt5 import QtWidgets, QtCore
from random import randint


class SynthDialog(QtWidgets.QDialog):

    WIDTH = 400
    HEIGHT = 600

    def __init__(self, parent, track = None, *args, **kwargs):
        super(SynthDialog, self).__init__(parent, *args, **kwargs)
        self.setWindowTitle('Synth Dialog')
        self.setGeometry(parent.x() + 0.5 * (parent.width() - self.WIDTH), parent.y() + 0.5 * (parent.height() - self.HEIGHT), self.WIDTH, self.HEIGHT)
        self.parent = parent
        self.track = track

        self.layout = QtWidgets.QVBoxLayout()

        self.nameLayout = QtWidgets.QHBoxLayout()
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

        self.layout.addWidget(QtWidgets.QLabel('Synth Instruments:', self))

        self.synthList = QtWidgets.QListView(self)
        self.synthList.setModel(self.parent.synthModel)
        self.layout.addWidget(self.synthList)

        self.buttonGrid = QtWidgets.QGridLayout()

        self.randomSynthButton = QtWidgets.QPushButton('Random Synth', self)
        self.buttonGrid.addWidget(self.randomSynthButton, 0, 0)

        self.randomizeParametersButton = QtWidgets.QPushButton('Randomize Parameters!', self)
        self.buttonGrid.addWidget(self.randomizeParametersButton, 0, 1)

        self.previewModuleButton = QtWidgets.QPushButton('Preview Module', self)
        self.previewModuleButton.setEnabled(track is not None and not track.isEmpty())
        self.buttonGrid.addWidget(self.previewModuleButton, 1, 1)

        self.hardcopySynthButton = QtWidgets.QPushButton('HardCopy Synth', self)
        self.buttonGrid.addWidget(self.hardcopySynthButton, 1, 0)

        self.layout.addLayout(self.buttonGrid)

        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)

        self.randomSynthButton.clicked.connect(self.selectRandomSynth)
        self.randomizeParametersButton.clicked.connect(self.randomizeSynthParameters)
        self.previewModuleButton.clicked.connect(self.parent.renderModule)
        self.hardcopySynthButton.clicked.connect(self.parent.hardcopySynth)

        self.init()

    def init(self):
        self.nameEdit.setText(self.track.synthName)
        if self.track.synthName in self.parent.synthModel.synthList():
            synthIndex = self.parent.synthModel.synthList().index(self.track.synthName)
            self.selectSynth(synthIndex)

    def synthName(self):
        try:
            index = self.synthList.selectedIndexes()[0].row()
            return self.parent.synthModel.synthList()[index]

        except IndexError:
            return None

    def selectSynth(self, index):
        self.synthList.setCurrentIndex(self.parent.synthModel.createIndex(index, 0))

    def selectRandomSynth(self):
        self.selectSynth(randint(0, self.parent.synthModel.rowCount() - 1))

    def clickOther(self, button):
        if button == self.buttonBox.button(QtWidgets.QDialogButtonBox.Reset):
            self.init()

    def randomizeSynthParameters(self):
        self.parent.randomizeSynatizer()