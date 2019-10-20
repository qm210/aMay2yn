from PyQt5.QtGui import QColor, QPainter, QFont
from PyQt5.QtWidgets import QWidget
from math import sqrt, floor
from numpy import clip
from copy import deepcopy

from may2Objects import * # pylint: disable=unused-wildcard-import
from may2Models import * # pylint: disable=unused-wildcard-import
from may2Utils import * # pylint: disable=unused-wildcard-import
from SynthDialog import SynthDialog
import may2Style

colorBG = QColor(*may2Style.group_bgcolor)

PAD_L = 10
PAD_R = 20
PAD_T = 9
PAD_B = -12


class May2TrackWidget(QWidget):

    moduleSelected = pyqtSignal(Module)
    trackChanged = pyqtSignal()
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
        self.currentTrack = None
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

        self.fontSize = 13 * sqrt(self.scaleV)
        self.fontSizeSmall = 8 * min(self.scaleH, self.scaleV)
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

            color = QColor(50, 50, 50) if track != self.currentTrack else QColor(128, 50, 50)
            qp.fillRect(self.X, y, self.charW * self.nrCharName + 4, self.trackH, color)

            qp.setPen(Qt.white)
            drawText(qp, self.X + 1, y, Qt.AlignTop, f'{track.name[:self.nrCharName]}')

            qp.setPen(QColor(210, 210, 210))
            drawText(qp, self.synthX, y, Qt.AlignTop, f'{track.getSynthName()[:self.nrCharSynth]}')

            color = QColor(50, 50, 50) if track != self.currentTrack else QColor(128, 50, 50)
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
                if module == track.getModule() and track == self.currentTrack:
                    qp.drawRect(L - 1, y - 1, R - L + 1, self.trackH + 2)


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
        eventX = event.pos().x()
        eventY = event.pos().y()
        corrTrack, corrModule = self.findCorrespondingTrackAndModule(eventX, eventY)
        if corrModule is None:
            if eventX < self.synthX:
                corrTrack.mute = not corrTrack.mute
            elif eventX < self.gridX:
                self.openSynthDialog(corrTrack)
            else:
                if event.button() == Qt.LeftButton:
                    self.insertModule(corrTrack, self.copyOfLastSelectedModule, eventX, forceModOn = True)
                return

        self.select(corrTrack, corrModule)
        if event.button() == Qt.LeftButton:
            self.initDragModule(corrTrack, corrModule, event.pos())
        elif event.button() == Qt.RightButton:
            pass
            #self.openModuleSelector(module) # window to choose Pattern and Transpose, and exact Position
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
        self.offsetV -= event.angleDelta().y() / 30
        self.offsetV = int(clip(self.offsetV, 0, self.model.rowCount() - self.numberTracksVisible))
        self.offsetH -= event.angleDelta().x() / 15
        self.offsetH = int(clip(self.offsetH, 0, self.model.totalLength() - .5 * self.numberBeatsVisible))
        self.repaint()

    def activate(self):
        self.active = True
        self.activated.emit()

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
        self.currentTrack = track
        if module is not None:
            module.tag()
            self.currentTrack.selectFirstTaggedModuleAndUntag()
            self.moduleSelected.emit(module)
            self.copyOfLastSelectedModule = deepcopy(module)

    def insertModule(self, track, modulePrototype, eventX, forceModOn = False):
        if track is None or modulePrototype is None:
            return # if modulePrototype is None, should open some window to choose pattern
        newModule = Module(mod_on = self.getBeatAtX(eventX), pattern = None, copyModule = modulePrototype, transpose = modulePrototype.transpose)
        track.addModule(newModule, forceModOn = forceModOn)

    def deleteModule(self, track, module):
        track.currentModuleIndex = track.findIndexOfModule(module)
        track.delModule()

    def debugOutput(self):
        print("=== TRACK MODEL ===")
        print("MODEL CONTENT:", self.model.rowCount(), "ENTRIES")
        for item in self.model:
            print(item.__dict__)

    def openSynthDialog(self, track):
        synthDialog = SynthDialog(self, track)
        if synthDialog.exec_():
            print(synthDialog.nameEdit.text())