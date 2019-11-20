from PyQt5.QtCore import QAbstractListModel, Qt, QModelIndex, pyqtSignal
from copy import deepcopy
import json
from may2Objects import Track


class TrackModel(QAbstractListModel):

    def __init__ (self, *args, **kwargs):
        super(TrackModel, self).__init__(*args, **kwargs)
        self.tracks = []
        self.currentTrackIndex = None

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

    def addRow(self, row, parent = QModelIndex()):
        self.beginInsertRows(parent, row, row)
        self.tracks.insert(row, Track())
        self.endInsertRows()

    def updateModulesWithChangedPattern(self, pattern):
        for track in self.tracks:
            for module in track.modules:
                if module.pattern.name == pattern.name:
                    module.pattern = pattern # deepcopy(pattern)

    def totalLength(self):
        return max(t.getLastModuleOff() for t in self.tracks)

    def getAllModules(self):
        return [m for t in self.tracks for m in t.modules]

    def getAllModulesOfHash(self, hash):
        return [m for t in self.tracks for m in t.modules if m.patternHash == hash]

########################## TRACK FUNCTIONALITY ############################

    def track(self, index):
        if not self.tracks or index is None:
            return None
        return self.tracks[index % self.rowCount()]

    def currentTrack(self):
        return self.track(self.currentTrackIndex)

    def currentTrackType(self):
        return self.currentTrack().synthType if self.currentTrack() is not None else None

    def setCurrentTrack(self, track):
        self.currentTrackIndex = self.tracks.index(track) if track in self.tracks else None

    def addTrack(self, row = None):
        if row is None:
            row = self.currentTrackIndex
        self.addRow(row)

    def cloneTrack(self, row = None):
        if row is None:
            row = self.currentTrackIndex
        self.cloneRow(row)

    def deleteTrack(self, row = None):
        if row is None:
            row = self.currentTrackIndex
        self.removeRow(row)

    def transposeModule(self, inc):
        track = self.currentTrack()
        module = track.getModule() if track is not None else None
        if module is None:
            return
        module.transpose += inc