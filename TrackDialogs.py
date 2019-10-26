from PyQt5 import QtWidgets, QtCore
from may2Objects import SYNTHTYPE, DRUMTYPE, NONETYPE


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