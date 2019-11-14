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
        self.startEdit = QtWidgets.QDoubleSpinBox(self)
        self.startEdit.setRange(0, 999)
        self.startEdit.setDecimals(2)
        self.startEdit.setSingleStep(1)
        self.startEdit.setPrefix('from ')
        self.endEdit = QtWidgets.QDoubleSpinBox(self)
        self.endEdit.setRange(0, 999)
        self.endEdit.setDecimals(2)
        self.endEdit.setSingleStep(1)
        self.endEdit.setPrefix('to ')
        self.rangeLayout.addWidget(QtWidgets.QLabel('Beat Interval:', self), 4)
        self.rangeLayout.addWidget(self.startEdit, 3)
        self.rangeLayout.addWidget(self.endEdit, 3)
        self.layout.addLayout(self.rangeLayout)

        self.typeLinearRadio = QtWidgets.QRadioButton("Linear", self)
        self.linearStartValueEdit = QtWidgets.QDoubleSpinBox(self)
        self.linearStartValueEdit.setDecimals(3)
        self.linearStartValueEdit.setSingleStep(.01)
        self.linearStartValueEdit.setPrefix('from ')
        self.linearEndValueEdit = QtWidgets.QDoubleSpinBox(self)
        self.linearEndValueEdit.setDecimals(3)
        self.linearEndValueEdit.setSingleStep(.01)
        self.linearEndValueEdit.setPrefix('to ')
        self.linearValueLayout = QtWidgets.QHBoxLayout()
        self.linearValueLayout.addWidget(self.typeLinearRadio, 4)
        self.linearValueLayout.addWidget(self.linearStartValueEdit, 3)
        self.linearValueLayout.addWidget(self.linearEndValueEdit, 3)
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
            self.linearStartValueEdit.setValue(self.param.default)
            self.linearStartValueEdit.setEnabled(False)
            self.linearEndValueEdit.setValue(self.param.default)
            self.linearEndValueEdit.setEnabled(False)
            self.constValueEdit.setValue(self.param.default)
            self.constValueEdit.setEnabled(False)
            self.literalValueEdit.setEnabled(False)
            self.nameEdit.setText(findFreeSerial(f"{self.param.id}_seg", self.param.getSegmentList()))
            self.startEdit.setValue(self.param.getLastSegmentEnd())
            self.endEdit.setValue(self.param.getLastSegmentEnd())
        else:
            self.setType(self.segment.type)
            self.nameEdit.setText(self.segment.id)
            self.startEdit.setValue(self.segment.start)
            self.endEdit.setValue(self.segment.end)
            if self.segment.type == ParamSegment.LINEAR:
                self.typeLinearRadio.setChecked(True)
                self.linearStartValueEdit.setValue(self.segment.args['startValue'])
                self.linearEndValueEdit.setValue(self.segment.args['endValue'])
            elif self.segment.type == ParamSegment.CONST:
                self.typeConstRadio.setChecked(True)
                self.constValueEdit.setValue(self.segment.args['value'])
            elif self.segment.type == ParamSegment.LITERAL:
                self.typeLiteralRadio.setChecked(True)
                self.literalValueEdit.setText(self.segment.args['value'])


    def setType(self, segType):
        self.segType = segType
        self.okButton.setEnabled(self.segType is not None)
        self.linearStartValueEdit.setEnabled(segType == ParamSegment.LINEAR)
        self.linearEndValueEdit.setEnabled(segType == ParamSegment.LINEAR)
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

        newSegment = ParamSegment(id = self.nameEdit.text(), start = self.startEdit.value(), end = self.endEdit.value())
        if self.segType == ParamSegment.LINEAR:
            kwargs = {'startValue': self.linearStartValueEdit.value(), 'endValue': self.linearEndValueEdit.value()}
        elif self.segType == ParamSegment.CONST:
            kwargs = {'value': self.constValueEdit.value()}
        elif self.segType == ParamSegment.LITERAL:
            kwargs = {'value': self.literalValueEdit.text()}
        else:
            raise ValueError(f"getSegment() called with invalid segment type {self.segType}")
        newSegment.setArgs(self.segType, **kwargs)
        return newSegment
