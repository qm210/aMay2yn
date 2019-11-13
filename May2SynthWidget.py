from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QTreeView, QTableView, QPushButton, QTreeView, QTreeWidget, QTreeWidgetItem
from PyQt5.QtGui import QStandardItemModel

from may2Synth import Synth
from may2ParamModel import Param
from SegmentDialog import SegmentDialog


class May2SynthWidget(QWidget):

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

    def setSynth(self, synth):
        self.synth = synth

        self.params = []
        self.paramWidget.clear()
        self.randoms = []
        # self.randomWidget.clear()

        if synth is None:
            return

        for paramKey in self.synth.usedParams:
            paramForm = self.synth.usedParams[paramKey]
            print(paramForm)
            param = Param(paramForm)
            item = QTreeWidgetItem([param.__str__()])
            for seg in param.segments:
                item.addChild(seg.__str__())
            self.paramWidget.addTopLevelItem(item)
        self.paramWidget.expandAll()

    def initLayout(self):
        self.mainLayout = QHBoxLayout(self)

        self.paramEditLayout = QVBoxLayout(self)
        self.reloadSynButton = QPushButton("Reload .syn", self)
        self.paramEditButton = QPushButton("Edit Selected", self)
        self.paramEditButton.setEnabled(False)
        self.newSegmentButton = QPushButton("New Segment", self)
        self.newSegmentButton.setEnabled(False)
        self.paramEditLayout.addWidget(self.reloadSynButton)
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

        self.paramEditButton.clicked.connect(self.editSelected)
        self.newSegmentButton.clicked.connect(self.newSegment)

    def selectParam(self, item, column = None):
        if item.parent() is None:
            self.selectedParam = item.text(0).split()[0]
            self.selectedSegment = None
        else:
            self.selectedParam = item.parent().text(0).split()[0]
            self.selectedSegment = self.paramWidget.indexOfTopLevelItem(item)

        self.paramEditButton.setEnabled(self.selectedParam is not None)
        self.newSegmentButton.setEnabled(self.selectedParam is not None)


    def editSelected(self):
        pass

    def newSegment(self):
        segmentDialog = SegmentDialog(self.parent)
        if segmentDialog.exec_():
            print("yay!")

            self.checkParamSegmentCollisions()

    def checkParamSegmentCollisions(self):
        foundCollision = False
        for param in self.params:
            for seg, nextSeg in zip(param.segments, param.segments[1:]):
                if seg.beatTo > nextSeg.beatFrom:
                    foundCollision = True
                    break
        self.paramWidget.setStyleSheet("background-color: red;" if foundCollision else "")
