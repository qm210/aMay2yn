from PyQt5.QtCore import QAbstractListModel, Qt, QModelIndex, pyqtSignal
from copy import deepcopy


class TrackModel(QAbstractListModel):

    def __init__ (self, *args, **kwargs):
        super(TrackModel, self).__init__(*args, **kwargs)
        self.tracks = []

    def setTracks(self, tracks):
        self.beginRemoveRows(QModelIndex(), self.createIndex(0,0).row(), self.createIndex(self.rowCount(),0).row())
        self.tracks = tracks
        self.layoutChanged.emit()
        self.endRemoveRows()

    def data(self, index, role):
        i = index.row()
        if role == Qt.DisplayRole:
            track = self.tracks[i]
            return f"{track.name} ({track.synths[track.current_synth][2:]}, {round(track.par_norm * 100) if not track.mute else 'MUTE'}%)"

    def rowCount(self, index = None):
        return len(self.tracks)

    def removeRow(self, row, parent = QModelIndex()):
        self.beginRemoveRows(parent, row, row)
        self.tracks.remove(self.tracks[row])
        self.endRemoveRows()

    def cloneRow(self, row, parent = QModelIndex()):
        self.beginInsertRows(parent, row, row)
        self.tracks.insert(row, deepcopy(self.tracks[row]))
        self.endInsertRows()

    def setSynthList(self, synths):
        for track in self.tracks:
            track.synths = synths

    def updateModulesWithChangedPattern(self, pattern):
        for track in self.tracks:
            for module in track.modules:
                if module.pattern.name == pattern.name:
                    module.pattern = pattern # deepcopy(pattern)

    def totalLength(self):
        return max(t.getLastModuleOff() for t in self.tracks)


class PatternModel(QAbstractListModel):

    def __init__ (self, *args, **kwargs):
        super(PatternModel, self).__init__(*args, **kwargs)
        self.patterns = []

    def setPatterns(self, patterns):
        self.beginRemoveRows(QModelIndex(), self.createIndex(0,0).row(), self.createIndex(self.rowCount(),0).row())
        self.patterns = patterns
        self.layoutChanged.emit()
        self.endRemoveRows()

    def data(self, index, role):
        i = index.row()
        if role == Qt.DisplayRole:
            pattern = self.patterns[i]
            return f"{pattern.name} [{pattern.length}] ({len(pattern.notes)} Notes)"

    def rowCount(self, index = None):
        return len(self.patterns)
