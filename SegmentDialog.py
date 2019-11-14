from PyQt5 import QtWidgets, QtCore
from random import randint
from functools import partial

from may2Param import ParamSegment
from may2Utils import findFreeSerial


class SegmentDialog(QtWidgets.QDialog):

    WIDTH = 500
    HEIGHT = 300

    def __init__(self, parent, param, segment = None, *args, **kwargs):
        super(SegmentDialog, self).__init__(parent, *args, **kwargs)
        self.setWindowTitle('Edit Parameter Segment')
        self.setGeometry(parent.x() + 0.5 * (parent.width() - self.WIDTH), parent.y() + 0.5 * (parent.height() - self.HEIGHT), self.WIDTH, self.HEIGHT)
        self.parent = parent
        self.param = param
        self.segment = segment
        self.segType = None
        self.deleteSegment = False

        self.layout = QtWidgets.QVBoxLayout()

        self.nameEdit = QtWidgets.QLineEdit(self)
        self.nameEdit.setPlaceholderText('Segment Name (arbitrary)')
        self.layout.addWidget(self.nameEdit)

        self.rangeLayout = QtWidgets.QHBoxLayout()
        self.fromBeatEdit = QtWidgets.QDoubleSpinBox(self)
        self.fromBeatEdit.setRange(0, 999)
        self.fromBeatEdit.setDecimals(2)
        self.fromBeatEdit.setSingleStep(1)
        self.fromBeatEdit.setPrefix('from ')
        self.toBeatEdit = QtWidgets.QDoubleSpinBox(self)
        self.toBeatEdit.setRange(0, 999)
        self.toBeatEdit.setDecimals(2)
        self.toBeatEdit.setSingleStep(1)
        self.toBeatEdit.setPrefix('to ')
        self.rangeLayout.addWidget(QtWidgets.QLabel('Beat Interval:', self), 4)
        self.rangeLayout.addWidget(self.fromBeatEdit, 3)
        self.rangeLayout.addWidget(self.toBeatEdit, 3)
        self.layout.addLayout(self.rangeLayout)

        self.typeLinearRadio = QtWidgets.QRadioButton("Linear", self)
        self.linearValueFromEdit = QtWidgets.QDoubleSpinBox(self)
        self.linearValueFromEdit.setDecimals(3)
        self.linearValueFromEdit.setSingleStep(.01)
        self.linearValueFromEdit.setPrefix('from ')
        self.linearValueToEdit = QtWidgets.QDoubleSpinBox(self)
        self.linearValueToEdit.setDecimals(3)
        self.linearValueToEdit.setSingleStep(.01)
        self.linearValueToEdit.setPrefix('to ')
        self.linearValueLayout = QtWidgets.QHBoxLayout()
        self.linearValueLayout.addWidget(self.typeLinearRadio, 4)
        self.linearValueLayout.addWidget(self.linearValueFromEdit, 3)
        self.linearValueLayout.addWidget(self.linearValueToEdit, 3)
        self.layout.addLayout(self.linearValueLayout)

        self.typeConstRadio = QtWidgets.QRadioButton("Constant", self)
        self.constValueLayout = QtWidgets.QHBoxLayout()
        self.constValueEdit = QtWidgets.QDoubleSpinBox(self)
        self.constValueEdit.setDecimals(3)
        self.constValueLayout.addWidget(self.typeConstRadio, 4)
        self.constValueLayout.addWidget(self.constValueEdit, 6)
        self.layout.addLayout(self.constValueLayout)

        self.typeLiteralRadio = QtWidgets.QRadioButton("GLSL Code Literal", self)
        self.literalValueLayout = QtWidgets.QHBoxLayout()
        self.literalValueEdit = QtWidgets.QLineEdit(self)
        self.literalValueEdit.setPlaceholderText('some GLSL code here...')
        self.literalValueLayout.addWidget(self.typeLiteralRadio, 4)
        self.literalValueLayout.addWidget(self.literalValueEdit, 6)
        self.layout.addLayout(self.literalValueLayout)

        if segment is None:
            self.buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel, self)
        else:
            self.buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel | QtWidgets.QDialogButtonBox.Discard | QtWidgets.QDialogButtonBox.Reset, self)
            self.buttonBox.button(QtWidgets.QDialogButtonBox.Discard).setText('Delete')
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.clicked.connect(self.clickOther)
        self.buttonBox.rejected.connect(self.reject)
        self.layout.addWidget(self.buttonBox)

        self.okButton = self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok)

        self.setLayout(self.layout)

        self.typeLinearRadio.clicked.connect(partial(self.setType, segType = ParamSegment.LINEAR))
        self.typeConstRadio.clicked.connect(partial(self.setType, segType = ParamSegment.CONST))
        self.typeLiteralRadio.clicked.connect(partial(self.setType, segType = ParamSegment.LITERAL))

        self.init()

    def init(self):
        if self.segment is None:
            self.okButton.setEnabled(False)
            self.linearValueFromEdit.setValue(self.param.default)
            self.linearValueFromEdit.setEnabled(False)
            self.linearValueToEdit.setValue(self.param.default)
            self.linearValueToEdit.setEnabled(False)
            self.constValueEdit.setValue(self.param.default)
            self.constValueEdit.setEnabled(False)
            self.literalValueEdit.setEnabled(False)
            self.nameEdit.setText(findFreeSerial(f"{self.param.id}_seg", self.param.getSegmentList()))
            self.fromBeatEdit.setValue(self.param.getLastSegmentEnd())
            self.toBeatEdit.setValue(self.param.getLastSegmentEnd())
        else:
            self.setType(self.segment.type)
            self.nameEdit.setText(self.segment.id)
            self.fromBeatEdit.setValue(self.segment.beatFrom)
            self.toBeatEdit.setValue(self.segment.beatTo)
            if self.segment.type == ParamSegment.LINEAR:
                self.typeLinearRadio.setChecked(True)
                self.linearValueFromEdit.setValue(self.segment.args['valueFrom'])
                self.linearValueToEdit.setValue(self.segment.args['valueTo'])
            elif self.segment.type == ParamSegment.CONST:
                self.typeConstRadio.setChecked(True)
                self.constValueEdit.setValue(self.segment.args['value'])
            elif self.segment.type == ParamSegment.LITERAL:
                self.typeLiteralRadio.setChecked(True)
                self.literalValueEdit.setText(self.segment.args['value'])


    def setType(self, segType):
        self.segType = segType
        self.okButton.setEnabled(self.segType is not None)
        self.linearValueFromEdit.setEnabled(segType == ParamSegment.LINEAR)
        self.linearValueToEdit.setEnabled(segType == ParamSegment.LINEAR)
        self.constValueEdit.setEnabled(segType == ParamSegment.CONST)
        self.literalValueEdit.setEnabled(segType == ParamSegment.LITERAL)

    def clickOther(self, button):
        if button == self.buttonBox.button(QtWidgets.QDialogButtonBox.Reset):
            self.init()
        if button == self.buttonBox.button(QtWidgets.QDialogButtonBox.Discard):
            self.deleteSegment = True
            self.accept()

    def getSegment(self):
        if self.deleteSegment:
            return None

        newSegment = ParamSegment(id = self.nameEdit.text(), beatFrom = self.fromBeatEdit.value(), beatTo = self.toBeatEdit.value())
        if self.segType == ParamSegment.LINEAR:
            kwargs = {'valueFrom': self.linearValueFromEdit.value(), 'valueTo': self.linearValueToEdit.value()}
        elif self.segType == ParamSegment.CONST:
            kwargs = {'value': self.constValueEdit.value()}
        elif self.segType == ParamSegment.LITERAL:
            kwargs = {'value': self.literalValueEdit.text()}
        else:
            raise ValueError(f"getSegment() called with invalid segment type {self.segType}")
        newSegment.setArgs(self.segType, **kwargs)
        return newSegment
