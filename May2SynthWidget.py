from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QTreeWidget, QTreeWidgetItem, QInputDialog, QTableWidget, QTableWidgetItem, QHeaderView
from PyQt5.QtGui import QStandardItemModel
from PyQt5.QtCore import pyqtSignal, Qt

from may2Synth import Synth
from may2Param import Param
from may2RandomValue import RandomValue
from SegmentDialog import SegmentDialog
import may2Style


class May2SynthWidget(QWidget):

    paramChanged = pyqtSignal(Param)
    randomsChanged = pyqtSignal(list)
    activated = pyqtSignal()

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.synth = None
        self.params = []
        self.selectedParam = None
        self.selectedSegment = None
        self.randoms = []
        self.selectedRandom = None

        self.active = False
        self.justUpdatingRandomWidget = False
        self.initLayout()
        self.initSignals()

    def initLayout(self):
        self.mainLayout = QHBoxLayout(self)

        self.paramEditLayout = QVBoxLayout()
        self.reloadFromSynButton = QPushButton("Reload from .syn", self)
        self.reloadFromSynButton.setEnabled(False)
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

        self.randomEditLayout = QVBoxLayout()
        self.reshuffleButton = QPushButton("reshuffle", self)
        self.reshuffleButton.setEnabled(False)
        self.hardcopyButton = QPushButton("hardcopy", self)
        self.hardcopyButton.setEnabled(False)
        self.setFixedButton = QPushButton("fix/free all", self)
        self.setFixedButton.setEnabled(False)
        self.randomEditLayout.addWidget(self.reshuffleButton)
        self.randomEditLayout.addWidget(self.hardcopyButton)
        self.randomEditLayout.addWidget(self.setFixedButton)
        self.mainLayout.addLayout(self.randomEditLayout)

        self.randomWidget = QTableWidget(self)
        self.randomWidget.setColumnCount(6)
        self.randomWidget.verticalHeader().hide()
        self.mainLayout.addWidget(self.randomWidget)

        self.setLayout(self.mainLayout)

    def initSignals(self):
        self.paramWidget.itemClicked.connect(self.selectParam)
        self.paramWidget.itemDoubleClicked.connect(self.editSelectedParam)
        self.reloadFromSynButton.clicked.connect(self.reloadFromSyn)
        self.paramEditButton.clicked.connect(self.editSelectedParam)
        self.newSegmentButton.clicked.connect(self.newSegment)
        self.randomWidget.currentItemChanged.connect(self.selectRandom)
        self.randomWidget.itemChanged.connect(self.editRandom)
        self.reshuffleButton.clicked.connect(self.reshuffleRandoms)
        self.hardcopyButton.clicked.connect(self.hardcopySynth)
        self.setFixedButton.clicked.connect(self.setAllFixedOrFree)


    def getSynthName(self):
        return self.synth.name if self.synth is not None else None

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
        if self.synth is not None:
            for randomID in self.synth.usedRandoms:
                random = self.getRandom(randomID)
                if random is None:
                    random = RandomValue(self.synth.usedRandoms[randomID])
                self.randoms.append(random)
        self.selectedRandom = None
        self.updateRandomWidget()

############################## PARAMS ###############################

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
        self.reloadFromSynButton.setEnabled(self.selectedParam is not None)
        self.paramEditButton.setEnabled(self.selectedParam is not None)
        self.newSegmentButton.setEnabled(self.selectedParam is not None)

    def selectParam(self, item, column = None):
        self.selectedParam = self.params[self.paramWidget.indexOfTopLevelItem(item)]
        if item.parent() is None:
            self.selectedSegment = None
        else:
            segmentIndex = self.paramWidget.indexFromItem(item).row()
            self.selectedSegment = self.selectedParam.getSegmentAtIndex(segmentIndex)
        self.updateParamButtons()

    def editSelectedParam(self, item = None, column = 0):
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

############################## RANDOM VALUES ###############################

    def updateRandomWidget(self):
        self.randomWidget.clear()
        self.justUpdatingRandomWidget = True
        self.randomWidget.setRowCount(0)
        for row, random in enumerate(self.randoms):
            self.randomWidget.insertRow(row)
            for col, content in enumerate(random.getRow()):
                item = QTableWidgetItem(str(content))
                if col == random.idColumn:
                    item.setFlags(Qt.ItemIsEnabled)
                elif col == random.fixedColumn:
                    item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                    item.setText('fixed')
                    item.setCheckState(Qt.Checked if content == True else Qt.Unchecked)
                else:
                    item.setFlags(Qt.ItemIsEditable | Qt.ItemIsEnabled)
                self.randomWidget.setItem(row, col, item)
        self.randomWidget.resizeColumnsToContents()
        self.randomWidget.setHorizontalHeaderLabels(['ID', 'value', 'min', 'max', 'digits', 'fixed?'])
        self.justUpdatingRandomWidget = False
        self.updateRandomButtons()

    def updateRandomWidgetColumn(self, col):
        self.justUpdatingRandomWidget = True
        for row in range(self.randomWidget.rowCount()):
            item = self.randomWidget.item(row, col)
            newContent = self.randoms[row].getRow()[col]
            if col == RandomValue.fixedColumn:
                item.setCheckState(Qt.Checked if newContent == True else Qt.Unchecked)
            else:
                item.setText(str(newContent))
        self.randomWidget.resizeColumnsToContents()
        self.justUpdatingRandomWidget = False


    def updateRandomButtons(self):
        self.reshuffleButton.setEnabled(len(self.randoms) > 0)
        self.hardcopyButton.setEnabled(len(self.randoms) > 0)
        self.setFixedButton.setEnabled(len(self.randoms) > 0)


    def getRandom(self, randomID):
        return self.parent.synthModel.randomValues.get(randomID, None)

    def selectRandom(self, item, prevItem = None):
        validItem = item is not None and len(self.randoms) > item.row()
        self.selectedRandom = self.randoms[item.row()] if validItem else None

    def editRandom(self, item):
        if self.justUpdatingRandomWidget:
            return

        self.selectRandom(item)

        if self.selectedRandom is not None:
            if item.column() == RandomValue.idColumn:
                pass
            elif item.column() == RandomValue.valueColumn:
                self.selectedRandom.value = float(item.text())
            elif item.column() == RandomValue.minColumn:
                self.selectedRandom.min = float(item.text())
            elif item.column() == RandomValue.maxColumn:
                self.selectedRandom.max = float(item.text())
            elif item.column() == RandomValue.digitsColumn:
                self.selectedRandom.digits = int(item.text())
            elif item.column() == RandomValue.fixedColumn:
                self.selectedRandom.fixed = (item.checkState() == Qt.Checked)

            self.randomsChanged.emit([self.selectedRandom])

    def reshuffleRandoms(self):
        for random in self.randoms:
            random.reshuffle()
        self.randomsChanged.emit(self.randoms)
        self.updateRandomWidgetColumn(RandomValue.valueColumn)

    def hardcopySynth(self):
        print("should implement this, but for now, just write the values to this terminal:")
        for random in self.randoms:
            print(random.getRow())
        self.parent.hardcopySynth(self.synth, self.randoms)
        #TODO: "softcopy": connect this with storeValue

    def setAllFixedOrFree(self):
        anyFixed = any([random.fixed for random in self.randoms])
        for random in self.randoms:
            random.fixed = not anyFixed
        self.updateRandomWidgetColumn(RandomValue.fixedColumn)


################################################################################

    def debugOutput(self):
        print("RANDOM VALUES STORED IN SYNTH MODEL:")
        for r in self.parent.synthModel.randomValues:
            print(r)
