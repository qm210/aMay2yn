from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QTreeView, QTableView, QPushButton, QTreeView, QTreeWidget, QTreeWidgetItem, QInputDialog
from PyQt5.QtGui import QStandardItemModel
from PyQt5.QtCore import pyqtSignal

from may2Synth import Synth
from may2Param import Param
from SegmentDialog import SegmentDialog


class May2SynthWidget(QWidget):

    paramChanged = pyqtSignal(Param)
    randomsChanged = pyqtSignal()

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.synth = None
        self.params = []
        self.selectedParam = None
        self.selectedSegment = None
        self.randoms = []
        self.selectedRandom = None
        self.initLayout()
        self.initSignals()

    def getSynthName(self):
        return self.synth.name if self.synth is not None else None

    def updateParamWidget(self):
        self.paramWidget.clear()
        for param in self.params:
            paramItem = QTreeWidgetItem([param.__str__()])
            for seg in param.segments:
                paramItem.addChild(QTreeWidgetItem([seg.__str__()]))
            self.paramWidget.addTopLevelItem(paramItem)
        self.paramWidget.expandAll()
        self.paramWidget.setStyleSheet("background-color: red;" if self.findParamSegmentCollisions() else "")
        self.updateParamButtons()

    def updateParamButtons(self):
        self.paramEditButton.setEnabled(self.selectedParam is not None)
        self.newSegmentButton.setEnabled(self.selectedParam is not None)

    def setSynth(self, synth):
        self.synth = synth
        self.params = []
        if self.synth is not None:
            for paramID in self.synth.usedParams:
                param = self.getParamOverride(paramID)
                if param is None:
                    param = Param(self.synth.usedParams[paramID])
                self.params.append(param)
        self.selectedParam = None
        self.selectedSegment = None
        self.updateParamWidget()

        self.randoms = []
        # self.randomWidget.clear()

    def initLayout(self):
        self.mainLayout = QHBoxLayout(self)

        self.paramEditLayout = QVBoxLayout(self)
        self.reloadFromSynButton = QPushButton("Reload from .syn", self)
        self.paramEditButton = QPushButton("Edit Selected", self)
        self.paramEditButton.setEnabled(False)
        self.newSegmentButton = QPushButton("New Segment", self)
        self.newSegmentButton.setEnabled(False)
        self.paramEditLayout.addWidget(self.reloadFromSynButton)
        self.paramEditLayout.addWidget(self.paramEditButton)
        self.paramEditLayout.addWidget(self.newSegmentButton)

        self.mainLayout.addLayout(self.paramEditLayout)

        self.paramWidget = QTreeWidget(self)
        self.paramWidget.setHeaderHidden(True)
        self.paramWidget.setItemsExpandable(False)
        self.mainLayout.addWidget(self.paramWidget)

        self.randomEditLayout = QVBoxLayout(self)
        self.reshuffleButton = QPushButton("reshuffle", self)
        self.hardcopyButton = QPushButton("hardcopy", self)
        self.setFixedButton = QPushButton("set fixed", self)
        self.randomEditLayout.addWidget(self.reshuffleButton)
        self.randomEditLayout.addWidget(self.hardcopyButton)
        self.randomEditLayout.addWidget(self.setFixedButton)
        self.mainLayout.addLayout(self.randomEditLayout)

        self.randomWidget = QTableView(self)
        self.mainLayout.addWidget(self.randomWidget)

        self.setLayout(self.mainLayout)

    def initSignals(self):
        self.paramWidget.itemClicked.connect(self.selectParam)
        self.paramWidget.itemDoubleClicked.connect(self.editSelected)
        self.reloadFromSynButton.clicked.connect(self.reloadFromSyn)
        self.paramEditButton.clicked.connect(self.editSelected)
        self.newSegmentButton.clicked.connect(self.newSegment)

    def selectParam(self, item, column = None):
        self.selectedParam = self.params[self.paramWidget.indexOfTopLevelItem(item)]
        if item.parent() is None:
            self.selectedSegment = None
        else:
            segmentIndex = self.paramWidget.indexFromItem(item).row()
            self.selectedSegment = self.selectedParam.getSegmentAtIndex(segmentIndex)
        self.updateParamButtons()

    def editSelected(self, item = None, column = 0):
        if self.selectedSegment is None:
            paramDefault, ok = QInputDialog.getDouble(self, 'Edit Parameter Default', f'Default Value for Parameter:\n{self.selectedParam.id}', self.selectedParam.default, decimals = 3)
            if not ok:
                return
            self.selectedParam.default = paramDefault
        else:
            print(self.selectedSegment)
            segmentDialog = SegmentDialog(self.parent, self.selectedParam, segment = self.selectedSegment)
            if not segmentDialog.exec_():
                return
            self.selectedParam.updateSegment(self.selectedSegment, segmentDialog.getSegment())

        self.paramChanged.emit(self.selectedParam)
        self.updateParamWidget()

    def newSegment(self):
        segmentDialog = SegmentDialog(self.parent, self.selectedParam)
        if segmentDialog.exec_():
            self.selectedParam.addSegment(segmentDialog.getSegment())
            self.paramChanged.emit(self.selectedParam)
            self.updateParamWidget()

    def findParamSegmentCollisions(self):
        for param in self.params:
            if param.hasCollidingSegments():
                return True
        return False

    def getParamOverride(self, paramID):
        return self.parent.synthModel.paramOverrides.get(paramID, None)

    def reloadFromSyn(self):
        if self.selectedParam is None:
            return
        print("Reload From .Syn is not properly implemented yet. For now, just erase the paramOverride in the synthModel...")
        self.parent.synthModel.deleteParamOverride(self.selectedParam.id) # TODO: actually, do it via signal as well
        self.setSynth(self.synth)
