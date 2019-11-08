from PyQt5.QtCore import QAbstractListModel, Qt, QModelIndex, pyqtSignal
from copy import deepcopy
import json
from may2Objects import SYNTHTYPE
from may2Synth import Synth


class SynthModel(QAbstractListModel):

    def __init__(self, *args, **kwargs):
        super(SynthModel, self).__init__(*args, **kwargs)
        self.synths = []

    def setSynths(self, synths):
        self.beginResetModel()
        self.synths = []
        for item in synths:
            if isinstance(item, str):
                self.synths.append(Synth(name = item))
            elif isinstance(item, Synth):
                self.synths.append(item)
            else:
                print(f"you are trying to pass object of type {type(item)} to SynthModel setSynth()...!?")
                print(item)
                raise TypeError
        self.endResetModel()
        self.layoutChanged.emit()

    def updateSynth(self, synth):
        print("OEHM", synth)
        for index, existingSynth in enumerate(self.synths):
            if synth.name == existingSynth.name:
                self.synths[index] = synth
                return index
        else:
            self.synths.append(synth)
            return -1

    def synthList(self):
        return [synth.name for synth in self.synths if synth.type == SYNTHTYPE]

    def data(self, index, role):
        i = index.row()
        if role == Qt.DisplayRole:
            displayName = self.synths[i].name
            if self.synths[i].usesAnyRandoms():
                displayName += ' [USES RANDOMS: ' + ','.join(self.synths[i].usedRandomIDs()) + ']'
            return displayName

    def rowCount(self, index = None):
        return len(self.synths)

    def removeRow(self, row, parent = QModelIndex()):
        self.beginRemoveRows(parent, row, row)
        self.synths.remove(self.synths[row])
        self.endRemoveRows()

    def cloneRow(self, row, parent = QModelIndex()):
        self.beginInsertRows(parent, row, row)
        self.synths.insert(row, deepcopy(self.synths[row]))
        self.endInsertRows()

#    def addRow(self, row, parent = QModelIndex()):
#        self.beginInsertRows(parent, row, row)
#        self.synths.insert(row, Synth())
#        self.endInsertRows()

