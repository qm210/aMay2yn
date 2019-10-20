from PyQt5 import QtWidgets, QtCore


class SynthDialog(QtWidgets.QDialog):

    def __init__(self, parent, track = None, *args, **kwargs):
        super(SynthDialog, self).__init__(parent, *args, **kwargs)
        self.setWindowTitle('Synth Dialog')
        self.track = track

        self.nameLayout = QtWidgets.QHBoxLayout(self)
        self.nameEdit = QtWidgets.QLineEdit(self)
        self.nameEdit.setPlaceholderText('Synth Name')
        self.nameEdit.setText(self.track.getSynthName())
        self.changeNameButton = QtWidgets.QPushButton(self)
        self.nameLayout.addWidget(self.nameEdit, 4)
        self.nameLayout.addWidget(self.changeNameButton, 1)

        self.buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel, self)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addLayout(self.nameLayout)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)