from PyQt5 import QtWidgets, QtCore
from may2Pattern import SYNTHTYPE, DRUMTYPE, NONETYPE


class TrackSettingsDialog(QtWidgets.QDialog):

    WIDTH = 200
    HEIGHT = 200

    def __init__(self, parent, track, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.setWindowTitle('Track')
        self.setGeometry(parent.x() + 0.5 * (parent.width() - self.WIDTH), parent.y() + 0.5 * (parent.height() - self.HEIGHT), self.WIDTH, self.HEIGHT)
        self.parent = parent
        self.initName = track.name
        self.initVolume = 100 * track.volume
        self.initMute = track.mute
        self.initSolo = False # TODO: implement

        self.layout = QtWidgets.QVBoxLayout(self)

        self.mainFormLayout = QtWidgets.QFormLayout()

        self.nameEdit = QtWidgets.QLineEdit(self)
        self.mainFormLayout.addRow('Track Name:', self.nameEdit)

        self.volumeSpinBox = QtWidgets.QSpinBox(self)
        self.volumeSpinBox.setSuffix(' %')
        self.volumeSpinBox.setRange(0, 999)
        self.mainFormLayout.addRow('Volume:', self.volumeSpinBox)

        self.muteCheckBox = QtWidgets.QCheckBox(self)
        self.mainFormLayout.addRow('Mute?', self.muteCheckBox)

        self.soloCheckBox = QtWidgets.QCheckBox(self)
        self.soloCheckBox.setEnabled(False)
        self.mainFormLayout.addRow('Solo?', self.soloCheckBox)

        self.layout.addLayout(self.mainFormLayout)

        self.cloneButton = QtWidgets.QPushButton('Clone Track', self)
        self.layout.addWidget(self.cloneButton)

        self.switchRowButton = QtWidgets.QPushButton('Switch Row with Next', self)
        self.layout.addWidget(self.switchRowButton)

        self.buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel | QtWidgets.QDialogButtonBox.Discard, self) # TODO: reset feature?
        self.deleteButton = self.buttonBox.button(QtWidgets.QDialogButtonBox.Discard)
        self.deleteButton.setText('Delete')
        self.layout.addWidget(self.buttonBox)

        self.setLayout(self.layout)

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.cloneButton.clicked.connect(self.cloneTrack)
        self.switchRowButton.clicked.connect(self.switchRowWithNext)
        self.deleteButton.clicked.connect(self.deleteTrack)

        self.init()

    def init(self):
        self.nameEdit.setText(self.initName)
        self.volumeSpinBox.setValue(self.initVolume)
        self.muteCheckBox.setChecked(QtCore.Qt.Checked if self.initMute else QtCore.Qt.Unchecked)

    def getName(self):
        return self.nameEdit.text()

    def getVolume(self):
        return 0.01 * self.volumeSpinBox.value()

    def getMute(self):
        return self.muteCheckBox.isChecked()

    def cloneTrack(self):
        # TODO: not my best style, but I have little time until Vortex IV
        self.parent.trackModel.cloneTrack()
        self.reject()

    def switchRowWithNext(self):
        self.parent.trackModel.switchRows()
        self.reject()

    def deleteTrack(self):
        self.parent.trackModel.deleteTrack()
        self.reject()

class TrackTypeDialog(QtWidgets.QDialog):

    def __init__(self, parent, *args, **kwargs):
        super(TrackTypeDialog, self).__init__(parent, *args, **kwargs)

        self.layout = QtWidgets.QVBoxLayout()

        self.chosenType = NONETYPE

        self.synthTypeButton = QtWidgets.QPushButton('SYNTH TRACK', self)
        self.drumTypeButton = QtWidgets.QPushButton('DRUM TRACK', self)
        self.noneTypeButton = QtWidgets.QPushButton('NONETYPE TRACK', self)

        self.layout.addWidget(self.synthTypeButton)
        self.layout.addWidget(self.drumTypeButton)
        self.layout.addWidget(self.noneTypeButton)

        self.synthTypeButton.clicked.connect(self.chooseSynthType)
        self.drumTypeButton.clicked.connect(self.chooseDrumType)
        self.noneTypeButton.clicked.connect(self.accept)

        self.setLayout(self.layout)

    def chooseSynthType(self):
        self.chosenType = SYNTHTYPE
        self.accept()

    def chooseDrumType(self):
        self.chosenType = DRUMTYPE
        self.accept()
