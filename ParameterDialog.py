from random import random
from PyQt5 import QtWidgets, QtCore


class ParameterDialog(QtWidgets.QDialog):

    def __init__(self, parent, pattern, parameterType, *args, **kwargs):
        super(ParameterDialog, self).__init__(parent, *args, **kwargs)
        self.setWindowTitle('Note Parameter Automation')
        self.parent = parent
        self.pattern = pattern

        self.layout = QtWidgets.QVBoxLayout(self)

        self.typeList = QtWidgets.QComboBox(self)
        self.typeList.addItems(['vel', 'slide', 'pan', 'aux'])
        parameterIndex = self.typeList.findText(parameterType, QtCore.Qt.MatchFixedString)
        self.typeList.setCurrentIndex(parameterIndex if parameterIndex > 0 else 0)
        self.layout.addWidget(self.typeList)

        self.fromSpin = QtWidgets.QDoubleSpinBox(self)
        self.fromSpin.setRange(0, 999)
        self.fromSpin.setValue(0)
        self.toSpin = QtWidgets.QDoubleSpinBox(self)
        self.toSpin.setRange(0, 999)
        self.toSpin.setValue(self.pattern.length)
        self.beatLayout = QtWidgets.QHBoxLayout()
        self.beatLayout.addWidget(QtWidgets.QLabel('Beat Interval: '))
        self.beatLayout.addWidget(self.fromSpin)
        self.beatLayout.addWidget(self.toSpin)
        self.layout.addLayout(self.beatLayout)

        self.linearValueStartSpin = QtWidgets.QDoubleSpinBox(self)
        self.linearValueStartSpin.setRange(-999, 999)
        self.linearValueStartSpin.setValue(0)
        self.linearValueStopSpin = QtWidgets.QDoubleSpinBox(self)
        self.linearValueStopSpin.setRange(-999, 999)
        self.linearValueStopSpin.setValue(0)
        self.linearValueLayout = QtWidgets.QHBoxLayout()
        self.linearValueLayout.addWidget(QtWidgets.QLabel('Linear Value Interval: '))
        self.linearValueLayout.addWidget(self.linearValueStartSpin)
        self.linearValueLayout.addWidget(self.linearValueStopSpin)
        self.layout.addLayout(self.linearValueLayout)

        self.randomValueStartSpin = QtWidgets.QDoubleSpinBox(self)
        self.randomValueStartSpin.setRange(-999, 999)
        self.randomValueStartSpin.setValue(0)
        self.randomValueStopSpin = QtWidgets.QDoubleSpinBox(self)
        self.randomValueStopSpin.setRange(-999, 999)
        self.randomValueStopSpin.setValue(0)
        self.randomValueLayout = QtWidgets.QHBoxLayout()
        self.randomValueLayout.addWidget(QtWidgets.QLabel('Random Value Interval: '))
        self.randomValueLayout.addWidget(self.randomValueStartSpin)
        self.randomValueLayout.addWidget(self.randomValueStopSpin)
        self.layout.addLayout(self.randomValueLayout)

        self.precisionSpin = QtWidgets.QSpinBox(self)
        self.precisionSpin.setRange(0, 3)
        self.precisionSpin.setValue(0)
        self.precisionSpin.setSuffix(' digits')
        self.layout.addWidget(self.precisionSpin)

        self.buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel, self)
        self.buttonBox.accepted.connect(self.applyParameters)
        self.buttonBox.rejected.connect(self.reject)
        self.layout.addWidget(self.buttonBox)

        self.setLayout(self.layout)


    def applyParameters(self):

        def valueFunction(progress):
            linearValue = (1 - progress) * self.linearValueStartSpin.value() + progress * self.linearValueStopSpin.value()
            randomValue = self.randomValueStartSpin.value() + random() * (self.randomValueStopSpin.value() - self.randomValueStartSpin.value())
            return round(linearValue + randomValue, self.precisionSpin.value())

        self.parameterType = self.typeList.currentText()

        for note in self.pattern.notes:
            progress = (note.note_on - self.fromSpin.value()) / (self.toSpin.value() - self.fromSpin.value())
            if progress < 0 or progress >= 1:
                continue
            note.setParameter(self.parameterType, valueFunction(progress))

        self.accept()
