from PyQt5.QtCore import QAbstractListModel, Qt, QModelIndex, pyqtSignal
from copy import deepcopy
import json
from may2Objects import Pattern


class PatternModel(QAbstractListModel):

    def __init__ (self, *args, **kwargs):
        super(PatternModel, self).__init__(*args, **kwargs)
        self.patterns = []

    def setPatterns(self, patterns):
        self.beginRemoveRows(QModelIndex(), self.createIndex(0,0).row(), self.createIndex(self.rowCount(),0).row())
        self.patterns = patterns
        self.layoutChanged.emit()
        self.endRemoveRows()

    def setPatternsFromModel(self, otherModel):
        self.beginResetModel()
        self.patterns = otherModel.patterns
        self.endResetModel()

    def data(self, index, role):
        i = index.row()
        if role == Qt.DisplayRole:
            pattern = self.patterns[i]
            return f"{pattern.name} [{pattern.length}] ({len(pattern.notes)} Notes)"

    def rowCount(self, index = None):
        return len(self.patterns)

    def removePattern(self, pattern):
        if pattern not in self.patterns:
            return
        self.removeRow(self.patterns.index(pattern))

    def removeRow(self, row, parent = QModelIndex()):
        self.beginRemoveRows(parent, row, row)
        self.patterns.remove(self.patterns[row])
        self.endRemoveRows()

    def cloneRow(self, row, parent = QModelIndex()):
        self.beginInsertRows(parent, row, row)
        self.patterns.insert(row, deepcopy(self.patterns[row]))
        self.endInsertRows()

    def addRow(self, row, pattern, parent = QModelIndex()):
        self.beginInsertRows(parent, row, row)
        self.patterns.insert(row, pattern)
        self.endInsertRows()

    def getPatternOfHash(self, hash):
        return next(p for p in self.patterns if p._hash == hash)

    def getPatternIndexOfHash(self, hash):
        for i, p in enumerate(self.patterns):
            if p._hash == hash:
                return i
        return None

    def getPatternOfName(self, name):
        index = self.getPatternIndexOfName(name)
        if not self.patterns or index is None:
            return None
        return self.patterns[index]

    def getPatternIndexOfName(self, name):
        for i, p in enumerate(self.patterns):
            if p.name == name:
                return i
        return None

    def getIndexOfPattern(self, pattern):
        return self.patterns.index(pattern) if pattern in self.patterns else None

    def createFilteredModel(self, typeFilter):
        filteredModel = PatternModel()
        filteredModel.patterns = [pattern for pattern in self.patterns if pattern.synthType == typeFilter]
        return filteredModel

    def purgeEmptyPatterns(self):
        nonemptyPatterns = [pattern for pattern in self.patterns if not pattern.isEmpty()]
        self.setPatterns(nonemptyPatterns)

    def purgeUnusedPatterns(self, usedHashs):
        usedPatterns = [pattern for pattern in self.patterns if pattern._hash in usedHashs]
        self.setPatterns(usedPatterns)
