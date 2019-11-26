from PyQt5 import QtWidgets, QtCore
import re


class SettingsDialog(QtWidgets.QDialog):

    WIDTH = 500
    HEIGHT = 140

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.setWindowTitle('Settings')
        self.setGeometry(parent.x() + 0.5 * (parent.width() - self.WIDTH), parent.y() + 0.5 * (parent.height() - self.HEIGHT), self.WIDTH, self.HEIGHT)
        self.parent = parent
        self.initBpmList = self.parent.info.get('BPM', '')

        self.layout = QtWidgets.QVBoxLayout(self)

        self.layout.addWidget(QtWidgets.QLabel('BPM List (pairs of beat:bpm)', self))
        self.bpmEdit = QtWidgets.QLineEdit(self)
        self.bpmEdit.setPlaceholderText('e.g. 0:30 8:31 16:25 ...')
        self.layout.addWidget(self.bpmEdit)

        self.bpmListCorrectLabel = QtWidgets.QLabel('BPM LIST VALID', self)
        self.bpmListIncorrectLabel = QtWidgets.QLabel('BPM LIST INVALID', self)
        self.bpmListIncorrectLabel.setStyleSheet('QLabel {color: red;}')
        self.bpmListIncorrectLabel.hide()
        self.layout.addWidget(self.bpmListCorrectLabel)
        self.layout.addWidget(self.bpmListIncorrectLabel)

        self.line1 = QtWidgets.QFrame(self)
        self.line1.setFrameShape(QtWidgets.QFrame.HLine)
        self.layout.addWidget(self.line1)

        self.formLayout = QtWidgets.QFormLayout()

        self.levelSynSpinBox = QtWidgets.QDoubleSpinBox(self)
        self.levelSynSpinBox.setRange(0, 9.999)
        self.levelSynSpinBox.setDecimals(2)
        self.levelSynSpinBox.setStepType(QtWidgets.QAbstractSpinBox.AdaptiveDecimalStepType)
        self.levelSynSpinBox.setValue(self.parent.info['level_syn'])
        self.formLayout.addRow(QtWidgets.QLabel('Global Synth Level: '), self.levelSynSpinBox)

        self.levelDrumSpinBox = QtWidgets.QDoubleSpinBox(self)
        self.levelDrumSpinBox.setRange(0, 9.999)
        self.levelDrumSpinBox.setDecimals(2)
        self.levelDrumSpinBox.setStepType(QtWidgets.QAbstractSpinBox.AdaptiveDecimalStepType)
        self.levelDrumSpinBox.setValue(self.parent.info['level_drum'])
        self.formLayout.addRow(QtWidgets.QLabel('Global Drum Level: '), self.levelDrumSpinBox)

        self.beatQuantumDenominatorSpinBox = QtWidgets.QSpinBox(self)
        self.beatQuantumDenominatorSpinBox.setValue(int(1/self.parent.info['beatQuantum']))
        self.beatQuantumDenominatorSpinBox.setRange(1, 256)
        self.formLayout.addRow(QtWidgets.QLabel('Beat Quantum: 1/'), self.beatQuantumDenominatorSpinBox)

        self.barsPerBeatSpinBox = QtWidgets.QSpinBox(self)
        self.barsPerBeatSpinBox.setRange(1, 16)
        self.barsPerBeatSpinBox.setValue(self.parent.info['barsPerBeat'])
        self.formLayout.addRow(QtWidgets.QLabel('Bars Per Beat: '), self.barsPerBeatSpinBox)

        self.synFileEdit = QtWidgets.QLineEdit(self)
        self.synFileEdit.setPlaceholderText('Enter path to .syn file (if not existing, will use <title>.syn or default.syn)')
        self.synFileEdit.setText(self.parent.state.get('synFile', ''))
        self.formLayout.addRow(QtWidgets.QLabel('.syn File: '), self.synFileEdit)

        self.layout.addLayout(self.formLayout)

        self.buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel, self)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.layout.addWidget(self.buttonBox)

        self.setLayout(self.layout)

        self.bpmEdit.textChanged.connect(self.checkBpmList)
        self.bpmEdit.setText(self.initBpmList)

    def bpmList(self):
        newBpmList = self.bpmEdit.text().strip()
        return newBpmList if self.checkBpmList(newBpmList) else self.initBpmList

    def checkBpmList(self, text):
        tryBpmList = self.bpmEdit.text().strip() + ' '
        regEx = re.match(r"([\d\.]+:[\d\.]+ +)+", tryBpmList)
        valid = regEx is not None and (regEx.group() == tryBpmList)
        if valid:
            bpms = tryBpmList.split()
            bpmDict = {}
            for pair in bpms:
                beat, bpm = pair.split(':')
                if beat not in bpmDict:
                    bpmDict.update({beat:bpm})
                else:
                    valid = False
                    break
        self.bpmListCorrectLabel.setVisible(valid)
        self.bpmListIncorrectLabel.setVisible(not valid)
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(valid)
        return valid

    def getLevels(self):
        return (self.levelSynSpinBox.value(), self.levelDrumSpinBox.value())