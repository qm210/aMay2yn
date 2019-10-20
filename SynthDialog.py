from PyQt5 import QtWidgets, QtCore


class SynthDialog(QtWidgets.QDialog):

    WIDTH = 400
    HEIGHT = 600

    def __init__(self, parent, track = None, *args, **kwargs):
        super(SynthDialog, self).__init__(parent, *args, **kwargs)
        self.setWindowTitle('Synth Dialog')
#        self.setGeometry(parent.x() + 0.5 * (parent.width() - self.WIDTH), parent.y() + 0.5 * (parent.height() - self.HEIGHT), self.WIDTH, self.HEIGHT)
        self.parent = parent
        self.track = track

        self.layout = QtWidgets.QVBoxLayout(self)

        self.nameLayout = QtWidgets.QHBoxLayout(self)
        self.nameEdit = QtWidgets.QLineEdit(self)
        self.nameEdit.setPlaceholderText('Synth Name')
        self.changeNameButton = QtWidgets.QPushButton('rename',self)
        self.nameLayout.addWidget(self.nameEdit, 4)
        self.nameLayout.addWidget(self.changeNameButton, 1)
        self.layout.addLayout(self.nameLayout)

        self.buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Reset | QtWidgets.QDialogButtonBox.Cancel, self)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.clicked.connect(self.clickOther)
        self.buttonBox.rejected.connect(self.reject)

        self.drumCheckBox = QtWidgets.QCheckBox('Drum Track', self)
        self.drumCheckBox.stateChanged.connect(self.toggleDrumTrack)
        self.layout.addWidget(self.drumCheckBox)

        self.synthList = QtWidgets.QListView(self)
        self.synthList.setModel(parent.parent.synthModel)
        self.layout.addWidget(self.synthList)

        self.upperButtonBox = QtWidgets.QHBoxLayout(self)
        self.randomSynthButton = QtWidgets.QPushButton('Random Synth', self)
        self.randomizeParametersButton = QtWidgets.QPushButton('Randomize Parameters', self)
        self.upperButtonBox.addWidget(self.randomSynthButton)
        self.upperButtonBox.addWidget(self.randomizeParametersButton)
        self.layout.addLayout(self.upperButtonBox)

        self.previewModuleButton = QtWidgets.QPushButton('Preview Module', self)
        self.layout.addWidget(self.previewModuleButton)

        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)

        self.init()

    def init(self):
        self.nameEdit.setText(self.track.getSynthName())
        isDrumTrack = self.track.isDrumTrack()
        self.drumCheckBox.setChecked(isDrumTrack)
        if not isDrumTrack:
            self.synthList.setCurrentIndex(self.parent.parent.synthModel.createIndex(self.track.current_synth, 0))


    def toggleDrumTrack(self, state):
        self.isDrumTrack = state
        self.synthList.setEnabled(not state)

    def clickOther(self, button):
        if button == self.buttonBox.button(QtWidgets.QDialogButtonBox.Reset):
            self.init()