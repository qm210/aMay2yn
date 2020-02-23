from copy import deepcopy
from PyQt5.QtCore import QAbstractListModel, Qt, QModelIndex


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

    def getPatternOfHash(self, patternHash):
        return next(p for p in self.patterns if p._hash == patternHash)

    def getPatternIndexOfHash(self, patternHash):
        for i, p in enumerate(self.patterns):
            if p._hash == patternHash:
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

    def extendPattern(self, pattern, beatsInc):
        if pattern not in self.patterns:
            print("wtf, pattern not in patternModel,", pattern.name)
            quit()
        if pattern.length + beatsInc < 1:
            return
        if beatsInc < 0:
            for note in pattern.notes[:]:
                if note.note_on >= pattern.length + beatsInc:
                    pattern.delNote(specificNote = note)
                elif note.note_off > pattern.length + beatsInc:
                    note.cropNoteOff(pattern.length + beatsInc)
        pattern.length += beatsInc

    def updateDrumPatterns(self, drumMap):
        print('lel', [(p.name, p.synthType) for p in self.patterns])
        if drumMap is not None:
            for pattern in self.patterns:
                pattern.applyDrumMap(drumMap)
