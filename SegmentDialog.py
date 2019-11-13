from PyQt5 import QtWidgets, QtCore
from random import randint
from functools import partial

from may2ParamModel import ParamSegment
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

        self.layout = QtWidgets.QVBoxLayout()

        self.nameEdit = QtWidgets.QLineEdit(self)
        self.nameEdit.setPlaceholderText('Segment Name (arbitrary)')
        self.layout.addWidget(self.nameEdit)

        self.rangeLayout = QtWidgets.QHBoxLayout()
        self.fromBeatEdit = QtWidgets.QDoubleSpinBox(self)
        self.fromBeatEdit.setRange(0, 999)
        self.fromBeatEdit.setDecimals(2)
        self.fromBeatEdit.setPrefix('from ')
        self.toBeatEdit = QtWidgets.QDoubleSpinBox(self)
        self.toBeatEdit.setRange(0, 999)
        self.toBeatEdit.setDecimals(2)
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

        self.buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Reset | QtWidgets.QDialogButtonBox.Cancel, self)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.clicked.connect(self.clickOther)
        self.buttonBox.rejected.connect(self.reject)
        self.layout.addWidget(self.buttonBox)

        self.okButton = self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok)
        self.resetButton = self.buttonBox.button(QtWidgets.QDialogButtonBox.Reset)

        self.setLayout(self.layout)

        self.typeLinearRadio.clicked.connect(partial(self.setType, segType = ParamSegment.LINEAR))
        self.typeConstRadio.clicked.connect(partial(self.setType, segType = ParamSegment.CONST))
        self.typeLiteralRadio.clicked.connect(partial(self.setType, segType = ParamSegment.LITERAL))

        self.init()

    def init(self):
        if self.segment is None:
            self.okButton.setEnabled(False)
            self.resetButton.setEnabled(False)
            self.linearValueFromEdit.setEnabled(False)
            self.linearValueToEdit.setEnabled(False)
            self.constValueEdit.setEnabled(False)
            self.literalValueEdit.setEnabled(False)
            self.nameEdit.setText(findFreeSerial(f"{self.param.id}_seg", self.param.getSegmentList()))
        else:
            self.setType(self.segment.type)

    def setType(self, segType):
        if segType == ParamSegment.LINEAR:
            pass
        elif segType == ParamSegment.CONST:
            pass
        elif segType == ParamSegment.LITERAL:
            pass
        else:
            print("warning: called segType with unknown Segment Type of", segType)
            segType = None

        self.okButton.setEnabled(segType is not None)
        self.linearValueFromEdit.setEnabled(segType == ParamSegment.LINEAR)
        self.linearValueToEdit.setEnabled(segType == ParamSegment.LINEAR)
        self.constValueEdit.setEnabled(segType == ParamSegment.CONST)
        self.literalValueEdit.setEnabled(segType == ParamSegment.LITERAL)

    def clickOther(self, button):
        if button == self.resetButton:
            self.init()