from PyQt5.QtGui import QColor, QPainter, QFont
from PyQt5.QtWidgets import QWidget, QInputDialog, QLineEdit
from PyQt5.QtCore import Qt, pyqtSignal
from math import sqrt, floor
from numpy import clip
from copy import deepcopy

from may2Objects import Track, Module, SYNTHTYPE, DRUMTYPE
from may2TrackModel import TrackModel
from may2Utils import drawText, drawTextDoubleInX, quantize, GLfloat
from SynthDialog import SynthDialog
from PatternDialogs import PatternDialog
from TrackDialogs import TrackSettingsDialog, TrackTypeDialog
import may2Style

colorBG = QColor(*may2Style.group_bgcolor)

colorTrackName = Qt.white
colorSynthName = QColor(210, 210, 210)
colorSynthMissing = QColor(210, 50, 50)

PAD_L = 10
PAD_R = 20
PAD_T = 9
PAD_B = -7


class May2TrackWidget(QWidget):

    moduleSelected = pyqtSignal(Module)
    trackSelected = pyqtSignal(Track)
    trackChanged = pyqtSignal()
    trackTypeChanged = pyqtSignal()
    activated = pyqtSignal()

    def __init__(self, parent):
        super().__init__()
        self.parent = parent

        self.active = False

        self.offsetV = 0
        self.offsetH = 0
        self.scaleV = 1
        self.scaleH = 1

        self.dragModule = None
        self.dragOrigin = None
        self.dragModuleOrigin = None
        self.dragModuleTrack = None

        self.model = None
        self.markerList = []
        self.trackSolo = None
        self.copyOfLastSelectedModule = None

    def setTrackModel(self, model):
        self.model = model

    def paintEvent(self, event):
        self.setGeometry(event)
        qp = QPainter()
        qp.begin(self)
        qp.setFont(QFont(may2Style.default_fontname, self.fontSize))
        qp.fillRect(self.X - PAD_L, self.Y - PAD_T, self.W + PAD_L + PAD_R, self.H + PAD_T + PAD_B, colorBG)
        if self.model is not None:
            self.drawTracks(qp)
            self.drawGrid(qp)
            self.drawModules(qp)
            self.drawTrackInfo(qp)
            self.drawMarkers(qp)
        qp.end()

    def setGeometry(self, event):
        self.X = event.rect().left() + PAD_L
        self.Y = event.rect().top() + PAD_T
        self.W = event.rect().width() - PAD_L - PAD_R
        self.H = event.rect().height() - PAD_T - PAD_B
        self.R = self.X + self.W
        self.B = self.Y + self.H
        self.trackH = 21 * self.scaleV
        self.gapH = 4 * self.scaleV
        self.rowH = self.trackH + self.gapH
        self.beatW = 20 * self.scaleH

        self.fontSize = max(13 * sqrt(self.scaleV), 5)
        self.fontSizeSmall = max(8 * min(self.scaleH, self.scaleV), 5)
        self.fontSizeSmallerScale = .9

        self.charW = 10
        self.nrCharName = 13
        self.nrCharSynth = 13

        self.synthX = self.X + self.charW * (self.nrCharName + 1) + 5
        self.gridX = self.X + self.charW * (self.nrCharName + self.nrCharSynth + 2) + 10 # HARDCODE (the 10. but what??)
        self.numberBeatsVisible = int((self.R - self.gridX) / self.beatW + 1)

        self.maxTracksVisible = int((self.H - 2 * self.fontSize) / self.rowH)
        self.numberTracksVisible = min(self.model.rowCount(), self.maxTracksVisible)
        self.endY = self.Y + self.numberTracksVisible * self.rowH

        self.offsetV = min(self.offsetV, abs(self.model.rowCount() - self.maxTracksVisible))

    def drawTracks(self, qp):
        for c in range(self.numberTracksVisible):
            track = self.model.tracks[self.offsetV + c]
            y = self.Y + c * self.rowH

            color = QColor(50, 50, 50) if track != self.model.currentTrack() else QColor(128, 50, 50)
            qp.fillRect(self.X, y, self.charW * self.nrCharName + 4, self.trackH, color)

            qp.setPen(colorTrackName)
            drawText(qp, self.X + 1, y, Qt.AlignTop, f'{track.name[:self.nrCharName]}')

            if track.synthName in self.parent.synthModel.synthList() or track.synthType != SYNTHTYPE:
                qp.setPen(colorSynthName)
                drawText(qp, self.synthX, y, Qt.AlignTop, f'{track.synthName[:self.nrCharSynth]}')
            else:
                qp.setPen(colorSynthMissing)
                drawText(qp, self.synthX, y, Qt.AlignTop, f'!{track.synthName[:self.nrCharSynth-1]}')

            color = QColor(50, 50, 50) if track != self.model.currentTrack() else QColor(128, 50, 50)
            color.setAlpha(255 - 128 * track.mute)
            qp.fillRect(self.gridX, y, self.R - self.gridX, self.trackH, color)


    def drawGrid(self, qp):
        font = qp.font()
        pen = qp.pen()

        x = self.gridX
        for b in range(self.numberBeatsVisible):
            pen.setColor(QColor(153, 204, 204)) # HARDCODE
            qp.setPen(pen)
            beatNr = f'{b + self.offsetH}'
            font.setPointSize(self.fontSizeSmall * (1 if len(beatNr) < 3 else self.fontSizeSmallerScale))
            qp.setFont(font)
            drawText(qp, x, self.endY + 1, Qt.AlignHCenter | Qt.AlignTop, beatNr)
            pen.setColor(QColor(13, 0, 13, 100)) # HARDCODE
            pen.setWidth(2)
            qp.setPen(pen)
            qp.drawLine(x, self.endY, x, self.Y)
            x += self.beatW

    def drawModules(self, qp):
        qp.font().setPointSize(self.fontSizeSmall)
        for c in range(self.numberTracksVisible):
            track = self.model.tracks[self.offsetV + c]
            y = self.Y + c * self.rowH
            for module in track.modules:
                L, R = self.getPosOfModule(module)
                if R < self.gridX or L > self.R:
                    continue
                L = max(L, self.gridX)
                R = min(R, self.R)
                patternColor = self.parent.getPatternColor(module.patternHash)
                qp.fillRect(L + 1, y, R - L, self.trackH, QColor(*patternColor, 100)) # HARDCODE
                qp.setPen(QColor(*(128 + .5*c for c in patternColor)))
                drawText(qp, L, y + self.trackH + 2, Qt.AlignLeft | Qt.AlignBottom, module.patternName[:3*int(module.patternLength)])
                if module.transpose != 0:
                    drawText(qp, L + 1, y - 2, Qt.AlignLeft | Qt.AlignTop, f'{module.transpose:+d}')
                if module == track.getModule() and track == self.model.currentTrack():
                    qp.drawRect(L - 1, y - 1, R - L + 1, self.trackH + 2)

    def drawTrackInfo(self, qp):
        qp.setPen(QColor(255, 255, 255, 180))
        font = qp.font()
        font.setPointSize(self.fontSize)
        qp.setFont(font)
        for c in range(self.numberTracksVisible):
            track = self.model.tracks[self.offsetV + c]
            y = self.Y + c * self.rowH
            label = f'{100 * track.volume:.0f}%'
            if track.mute or (self.trackSolo is not None and track != self.trackSolo):
                label = 'MUTE'
            elif track == self.trackSolo:
                label = f'SOLO {label}'
            drawText(qp, self.R, y, Qt.AlignRight | Qt.AlignTop, label)

    def drawMarkers(self, qp):
        font = qp.font()
        pen = qp.pen()
        for m in self.markerList:
            markerPos = m['pos'] - self.offsetH
            if markerPos < 0 or markerPos >= self.numberBeatsVisible: continue

            x = self.gridX + markerPos * self.beatW

            if m['style'] == 'BPM':
                lineBottom = self.endY + 25
                lineTop = self.endY + 17
                pen.setColor(QColor(77, 77, 180, 180)) # HARDCODE
                markerText = m['label'][3:]
                font.setPointSize(self.fontSizeSmall * self.fontSizeSmallerScale)
            else:
                lineBottom = self.endY + self.fontSizeSmall + 4
                lineTop = self.Y
                pen.setColor(QColor(210, 50, 50, 180))
                markerText = m['label']
                font.setPointSize(self.fontSizeSmall)
            pen.setWidthF(1.5)
            qp.setPen(pen)
            qp.drawLine(x, lineBottom, x, lineTop)
            qp.setFont(font)
            drawTextDoubleInX(qp, x, lineBottom + 2, Qt.AlignHCenter | Qt.AlignTop, markerText, 0.5)


    def getPosOfModule(self, module):
        coordL = self.gridX + self.beatW * (module.mod_on - self.offsetH)
        coordR = coordL + self.beatW * module.patternLength - 1
        return coordL, coordR

    def getTrackAtY(self, y):
        if y < self.Y or y > self.endY:
            return None
        visibleRow = int((y - self.Y) / (self.endY - self.Y) * self.numberTracksVisible)
        track = self.model.tracks[self.offsetV + visibleRow]
        return track

    def getBeatAtX(self, x):
        if x < self.gridX or x > self.R:
            return None
        visibleBeat = int((x - self.gridX) / (self.R - self.gridX) * self.numberBeatsVisible)
        beat = self.offsetH + visibleBeat
        return beat

    def findCorrespondingTrackAndModule(self, coordX, coordY):
        track = self.getTrackAtY(coordY)
        if track is None:
            return None, None
        for module in track.modules:
            L, R = self.getPosOfModule(module)
            if coordX >= L and coordX <= R:
                return track, module
        return track, None

    def mousePressEvent(self, event):
        if not self.active:
            self.activate()
            return

        eventX = event.pos().x()
        eventY = event.pos().y()
        corrTrack, corrModule = self.findCorrespondingTrackAndModule(eventX, eventY)
        if corrTrack is None:
            return

        self.select(corrTrack, corrModule)

        if eventX < self.synthX:
            if event.button() == Qt.RightButton:
                self.toggleMute(corrTrack)
            elif event.button() == Qt.MiddleButton:
                self.renameTrack(corrTrack)

        elif eventX < self.gridX:
            if event.button() == Qt.RightButton:
                self.openSynthDialog(corrTrack)

        else:
            if event.button() == Qt.MiddleButton and self.parent.ctrlPressed:
                self.setScale(H = 1, V = 1)
                return

            if corrModule is None:
                beat = self.getBeatAtX(eventX)
                if event.button() == Qt.RightButton:
                    self.queryTrackType(corrTrack)
                    self.openPatternDialog(corrTrack, beat = beat)
                elif event.button() == Qt.MiddleButton:
                    self.insertModule(corrTrack, self.copyOfLastSelectedModule, beat)
            else:
                if event.button() == Qt.LeftButton:
                        self.initDragModule(corrTrack, corrModule, event.pos())
                elif event.button == Qt.RightButton:
                        self.openPatternDialog(corrTrack, module = corrModule)
                elif event.button() == Qt.MiddleButton:
                    self.deleteModule(corrTrack, corrModule)

    def mouseMoveEvent(self, event):
        if self.dragModule is not None:
            self.dragModuleTo(event.pos())
            self.repaint()

    def mouseReleaseEvent(self, event):
        self.finalizeDrag()
        self.dragModule = None
        self.update()

    def wheelEvent(self, event):
        if self.parent.ctrlPressed:
            self.setScale(deltaH = event.angleDelta().y() / 1200)
        elif self.parent.altPressed:
            transpose = 12 if event.angleDelta().x() > 0 else -12
            self.model.currentTrack().transposeModule(transpose)
        else:
            if self.parent.shiftPressed:
                xScroll = -event.angleDelta().y() / 60
                yScroll = 0
            else:
                xScroll = event.angleDelta().x() / 15
                yScroll = event.angleDelta().y() / 30
            self.offsetV = int(clip(self.offsetV - yScroll, 0, self.model.rowCount() - self.numberTracksVisible))
            self.offsetH = int(clip(self.offsetH - xScroll, 0, max(0, self.model.totalLength() - .5 * self.numberBeatsVisible)))
        self.repaint()

    def activate(self):
        self.active = True
        self.activated.emit()

    def setScale(self, H = None, V = None, deltaH = None, deltaV = None):
        if H is not None:
            self.scaleH = H
        if deltaH is not None:
            self.scaleH += deltaH
        if V is not None:
            self.scaleV = V
        if deltaV is not None:
            self.scaleV += deltaV
        self.scaleH = max(self.scaleH, 0.1)
        self.scaleV = max(self.scaleV, 0.1)
        self.repaint()

    def initDragModule(self, track, module, origin):
        if self.dragModule is None:
            self.dragModule = module
            self.dragOrigin = origin
            self.dragModuleTrack = track
            self.dragModuleOrigin = module.mod_on

    def dragModuleTo(self, pos):
        distance = (pos.x() - self.dragOrigin.x()) / self.beatW
        self.dragModule.mod_on = self.dragModuleOrigin + quantize(distance, 1)

    def finalizeDrag(self):
        if self.dragModule:
            if self.dragModule.mod_on < self.offsetH or self.dragModule.mod_on > self.offsetH + self.numberBeatsVisible + 1:
                self.dragModuleTo(self.dragOrigin)
            #TODO: note to self; Editor should allow overlapping modules but export should be declined, then! (give error message)
            else:
                self.trackChanged.emit()

    def select(self, track, module = None):
        if track is not None:
            currentSynthType = self.model.currentTrackType()
            self.model.setCurrentTrack(track)
            self.trackSelected.emit(track)
            if track.synthType != currentSynthType:
                self.trackTypeChanged.emit()
        if module is None and track.modules:
            module = track.modules[0]
        if module is not None:
            module.tag()
            self.model.currentTrack().selectFirstTaggedModuleAndUntag()
            self.moduleSelected.emit(module)
            self.copyOfLastSelectedModule = deepcopy(module)
        self.repaint()

    def insertModule(self, track, modulePrototype, modOn, forceModOn = True):
        if track is None or modulePrototype is None:
            return # if modulePrototype is None, should open some window to choose pattern
        newModule = Module(mod_on = modOn, pattern = None, copyModule = modulePrototype, transpose = modulePrototype.transpose)
        track.addModule(newModule, forceModOn = forceModOn)
        self.trackChanged.emit()
        self.select(track, newModule)

    def deleteModule(self, track, module):
        track.currentModuleIndex = track.findIndexOfModule(module)
        track.delModule()
        self.trackChanged.emit()
        self.select(track, track.getModule())

    ################# HELPERS ##############

    def repaintAndEmitTrackChanged(self):
        self.repaint()
        self.trackChanged.emit()

    def debugOutput(self):
        print("=== TRACK MODEL ===")
        print("MODEL CONTENT:", self.model.rowCount(), "ENTRIES")
        for item in self.model:
            print(item.__dict__)

    ############ BASIC FUNCTIONALITY ###############

    def selectTrack(self, inc):
        index = self.model.currentTrackIndex + inc
        self.select(self.model.track(index))
        print(inc)

    def toggleMute(self, track = None):
        if track is None:
            track = self.model.currentTrack()
        track.mute = not track.mute
        self.trackChanged.emit()
        self.repaint()

    def toggleSolo(self, track = None):
        if track is None:
            track = self.model.currentTrack()
        self.trackSolo = track if self.trackSolo is None else None
        self.repaint()

    def renameTrack(self, track = None, name = None):
        if track is None:
            track = self.mode.currentTrack()
        if name is None:
            # TODO: enhance to 'Track Settings Dialog with Mute, Solo, Volume, etc.'
            trackDialog = TrackSettingsDialog(self.parent, track)
            if trackDialog.exec_():
                track.name = trackDialog.getName()
                track.volume = trackDialog.getVolume()
                track.mute = trackDialog.getMute()
                self.repaintAndEmitTrackChanged()

    def openSynthDialog(self, track = None):
        self.parent.setModifiers()
        if track is None:
            track = self.model.currentTrack()
        # TODO: separate DrumkitDialog for drum tracks...
        if track.synthType == SYNTHTYPE:
            synthDialog = SynthDialog(self.parent, track)
            if synthDialog.exec_():
                track.setSynth(name = synthDialog.synthName())
                self.repaintAndEmitTrackChanged()
        else:
            self.queryTrackType(track)

    def queryTrackType(self, track):
        if track.isEmpty():
            trackTypeDialog = TrackTypeDialog(self.parent)
            if trackTypeDialog.exec_():
                track.setSynth(type = trackTypeDialog.chosenType, name = self.parent.getRandomSynthName(trackTypeDialog.chosenType))
                self.repaintAndEmitTrackChanged()

    def openPatternDialog(self, track, beat = None, module = None):
        self.parent.setModifiers()
        if module is None:
            patternDialog = PatternDialog(self.parent, track = track, pattern = self.parent.getModulePattern(), beat = beat)
            if patternDialog.exec_():
                track.addModule(patternDialog.module)
                self.syncPatternNames(patternDialog.namesChanged)
                self.select(track, patternDialog.module)
                self.trackChanged.emit()
        else:
            oldPatternHash = module.patternHash
            patternDialog = PatternDialog(self.parent, track = track, module = module)
            status = patternDialog.exec_()
            if status:
                pattern = patternDialog.getPattern()
                self.syncPatternNames(patternDialog.namesChanged)
                if pattern._hash != oldPatternHash:
                    self.select(track, module)
                    self.trackChanged.emit()

    def syncPatternNames(self, namesChanged):
        if namesChanged:
            for module in self.model.getAllModules():
                if module.patternHash in namesChanged:
                    module.patternName = namesChanged[module.patternHash]


    def addPattern(self, pattern, clone = False):
        self.parent.addPattern(pattern, clone)


    def addMarker(self, label, position, style = '', unique = False):
        if unique:
            self.removeMarkersContaining(label)
        self.markerList.append({'label': label, 'pos': position, 'style': style})
        markersToRemove = [m for m in self.markerList if m['pos']<0]
        for m in markersToRemove:
            self.markerList.remove(m)

    def removeMarkersContaining(self, label):
        markersToRemove = [m for m in self.markerList if label in m['label']]
        for m in markersToRemove:
            self.markerList.remove(m)

    def updateBpmList(self, bpmListString):
        bpmList = bpmListString.split()
        bpmDict = {float(pair[0]):float(pair[1]) for pair in [pair.split(':') for pair in bpmList]}
        self.removeMarkersContaining('BPM')
        for beat in bpmDict:
            markerLabel = 'BPM' + GLfloat(bpmDict[beat])
            if markerLabel[-1] == '.':
                markerLabel = markerLabel[:-1]
            self.addMarker(markerLabel, beat, style = 'BPM')
