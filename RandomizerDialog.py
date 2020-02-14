from PyQt5 import QtWidgets, QtCore
from random import random


class RandomizerDialog(QtWidgets.QDialog):

    def __init__(self, parent, *args, **kwargs):
        super(RandomizerDialog, self).__init__(parent, *args, **kwargs)
        self.setWindowTitle('Multi-Randomizer')
        self.parent = parent

        self.layout = QtWidgets.QVBoxLayout(self)

        self.outDirEdit = QtWidgets.QLineEdit(self)
        self.outDirEdit.setText(f"./{self.parent.state['title']}")
        self.layout.addWidget(self.outDirEdit)

        self.numberSpin = QtWidgets.QSpinBox(self)
        self.numberSpin.setRange(1, 9999)
        self.numberSpin.setValue(1)
        self.numberSpin.setPrefix('shuffle ')
        self.numberSpin.setSuffix(' times')
        self.layout.addWidget(self.numberSpin)

        self.buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel, self)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.layout.addWidget(self.buttonBox)

        self.setLayout(self.layout)
