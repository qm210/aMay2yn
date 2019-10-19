from PyQt5.QtGui import QColor, QPainter, QFont
from PyQt5.QtWidgets import QWidget
from math import sqrt, floor
from numpy import clip

from may2Objects import * # pylint: disable=unused-wildcard-import
from may2Models import * # pylint: disable=unused-wildcard-import
from may2Utils import * # pylint: disable=unused-wildcard-import
import may2Style

colorBG = QColor(*may2Style.group_bgcolor)

colorWhiteKeys = Qt.white
colorBlackKeys = QColor(25, 25, 25)
colorSelectedKey = QColor(180, 255, 75, 150)
colorWhiteKeyText = QColor(77, 77, 77)
colorBlackKeyText = Qt.white
colorWhiteBG = QColor(25, 77, 51)
colorBlackBG = QColor(25, 25, 25)

PAD_L = 10
PAD_R = 20
PAD_T = 10
PAD_B = 22

CLICK_PRECISION = 1.03


class May2PatternWidget(QWidget):

    noteSelected = pyqtSignal(int)
    patternChanged = pyqtSignal()
    activated = pyqtSignal()

    claviature = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

    def __init__(self, parent):
        super().__init__()
        self.parent = parent

        self.active = False

        self.offsetV = 12
        self.offsetH = 0
        self.scaleV = 1
        self.scaleH = 1

        self.barsPerBeat = 4
        self.beatQuantum = 1/16

        self.dragNote = None
        self.dragOrigin = (None, None)
        self.dragNoteOrigin = None

        self.stretchNote = None
        self.stretchOrigin = None
        self.stretchPos = None
        self.stretchNoteOrigin = None

        self.pattern = None

    def setPattern(self, pattern):
        self.pattern = pattern

    def paintEvent(self, event):
        self.setGeometry(event)
        qp = QPainter()
        qp.begin(self)
        qp.setFont(QFont(may2Style.default_fontname, self.fontSize))
        qp.fillRect(self.X - PAD_L, self.Y - PAD_T, self.W + PAD_L + PAD_R, self.H + PAD_T + PAD_B, colorBG)
        self.drawBackground(qp)
        self.drawGrid(qp)
        if self.pattern is not None:
            self.drawNotes(qp)
        qp.end()

    def setGeometry(self, event):
        self.X = event.rect().left() + PAD_L
        self.Y = event.rect().top() + PAD_T
        self.W = event.rect().width() - PAD_L - PAD_R
        self.H = event.rect().height() - PAD_T - PAD_B
        self.R = self.X + self.W
        self.B = self.Y + self.H
        self.keyH = 10 * self.scaleV
        self.keyW = 32 * self.scaleH
        self.pianoW = 34 * self.scaleH

        self.fontSize = 9 * min(self.scaleH, self.scaleV)
        self.fontSizeParameters = self.fontSize * sqrt(self.scaleH)
        self.barW = 48 * self.scaleH
        self.beatW = self.barsPerBeat * self.barW # would change for a 3/4 beat!

        self.rollX = self.X + self.pianoW
        self.rollW = self.R - self.rollX

        self.numberKeysVisible = int(self.H / self.keyH)
        self.T = self.B - self.keyH * (self.numberKeysVisible)

        self.maxNumberBars = (self.W - self.pianoW) / self.barW
        self.numberBarsVisible = 0 if not self.pattern else int(clip(self.barsPerBeat * (self.pattern.length - self.offsetH), 0, self.maxNumberBars))
        self.numberBeatsVisible = self.numberBarsVisible / self.barsPerBeat

    def drawBackground(self, qp):

        isKeyWhite = lambda key: '#' not in self.claviature[key % 12]

        for c in range(self.numberKeysVisible):
            key = self.offsetV + c
            y = self.B - (c + 1) * self.keyH

            qp.fillRect(self.X, y, self.keyW, (self.keyH - 1) + 0.7 * isKeyWhite(key), colorWhiteKeys if isKeyWhite(key) else colorBlackKeys)

            if self.pattern and self.pattern.notes and key == (self.pattern.getNote().note_pitch) % 100:
                qp.fillRect(self.X, y, self.keyW, (self.keyH - 1) + 0.7 * isKeyWhite(key), colorSelectedKey)

            qp.setPen(colorWhiteKeyText if isKeyWhite(key) else colorBlackKeyText)
            drawTextDoubleInY(qp, self.X + 2, y - 2.5, Qt.AlignLeft | Qt.AlignTop, self.claviature[key % 12] + str(key // 12), .5)

            qp.fillRect(self.rollX, y, self.rollW, self.keyH - 1, colorWhiteBG if isKeyWhite(key) else colorBlackBG)


    def drawGrid(self, qp):

        x = self.X + self.pianoW

        qp.setPen(QColor(150, 200, 200)) # first grid label # HARDCODE
        qp.font().setPointSize(12) # HARDCODE
        drawText(qp, x, self.B + 1, Qt.AlignHCenter | Qt.AlignTop, f'{self.offsetH : .2f}')
        pen = qp.pen()
        for b in range(self.numberBarsVisible):
            pen.setColor(QColor(13, 0, 13, 100)) # HARDCODE
            pen.setWidthF(1.5 if b % 4 == 0 else 1)
            qp.setPen(pen)
            qp.drawLine(x, self.B, x, self.T)
            pen.setWidthF(.3)
            qp.setPen(pen)
            x += 0.25 * self.barW
            qp.drawLine(x, self.B, x, self.T)
            x += 0.25 * self.barW
            qp.drawLine(x, self.B, x, self.T)
            x += 0.25 * self.barW
            qp.drawLine(x, self.B, x, self.T)
            x += 0.25 * self.barW
            pen.setColor(QColor(153, 204, 204)) # HARDCODE
            qp.setPen(pen)
            drawText(qp, x, self.B + 1, Qt.AlignHCenter | Qt.AlignTop, f'{(b+1)/4 + self.offsetH : .2f}')

        # END SEGMENT
        qp.fillRect(x, self.B, self.R - x, self.T - self.B, QColor(0, 0, 0, 75)) # HARDCODE
        qp.setPen(Qt.black)
        qp.pen().setWidthF(2) # doesntwork
        qp.drawLine(x, self.B, x, self.T)


    def drawNotes(self, qp):
        if self.pattern is None:
            return
        for note in self.pattern.notes:
            note_on = note.note_on - self.offsetH
            L, R, T, B = self.getRectOfNote(note)
            if note_on < 0 or L > self.R or T < self.T:
                continue
            qp.fillRect(L + 1, T, R - L, B - T, QColor(*self.parent.getPatternColor(self.pattern._hash), 140))
            if note == self.pattern.getNote():
                qp.fillRect(L + 1, T, R - L, B - T, QColor(255, 255, 255, 150))
                if self.pattern.currentGap:
                    qp.fillRect(R - 1, T + self.keyH / 2, self.beatW * self.pattern.currentGap, self.keyH / 4, QColor(255, 255, 255, 100))


    def getRectOfNote(self, note):
        coordL = self.X + self.pianoW + self.beatW * (note.note_on - self.offsetH)
        coordR = coordL + self.beatW * note.note_len
        coordB = self.B - self.keyH * (note.note_pitch - self.offsetV)
        coordT = coordB - self.keyH
        return coordL, coordR, coordT, coordB

    def findCorrespondingNote(self, coordX, coordY):
        nextNeighbor = None
        minDistance = None
        for note in self.pattern.notes:
            L, R, T, B = self.getRectOfNote(note)
            centerX = 0.5 * (L + R)
            centerY = 0.5 * (T + B)
            deltaX = abs(coordX - centerX)
            deltaY = abs(coordY - centerY)
            halfW = .5 * (R - L)
            halfH = .5 * (B - T)
            distance = max(deltaX / halfW, deltaY / halfH)
            if distance < CLICK_PRECISION:
                if nextNeighbor is None or distance < minDistance:
                    nextNeighbor = note
                    minDistance = distance
        return nextNeighbor

    def getDistanceInNoteUnits(self, deltaX, deltaY):
        return (deltaX / self.beatW, -deltaY / self.keyH)

    def initDragNote(self, note, origin):
        if self.dragNote is None:
            self.dragNote = note
            self.dragOrigin = origin
            self.dragNoteOrigin = (note.note_on, note.note_pitch)

    def dragNoteTo(self, pos):
        noteDistance = self.getDistanceInNoteUnits(pos.x() - self.dragOrigin.x(), pos.y() - self.dragOrigin.y())
        self.dragNote.note_on = self.dragNoteOrigin[0] + quantize(noteDistance[0], self.beatQuantum)
        self.dragNote.note_off = self.dragNote.note_on + self.dragNote.note_len
        self.dragNote.note_pitch = self.dragNoteOrigin[1] + quantize(noteDistance[1], 1)

    def initStretchNote(self, note, origin):
        if self.stretchNote is None:
            self.stretchNote = note
            self.stretchOrigin = origin
            self.stretchNoteOrigin = note.note_len

    def stretchNoteTo(self, pos):
        noteDistance = self.getDistanceInNoteUnits(pos.x() - self.stretchOrigin.x(), 0)
        self.stretchNote.note_len = self.stretchNoteOrigin + quantize(noteDistance[0], self.beatQuantum)

    def mousePressEvent(self, event):
        if not self.active:
            self.activate()

        corrNote = self.findCorrespondingNote(event.pos().x(), event.pos().y())
        if corrNote is None:
            return
        self.select(corrNote)
        if event.button() == Qt.LeftButton:
            self.initDragNote(corrNote, event.pos())
        if event.button() == Qt.RightButton:
            self.initStretchNote(corrNote, event.pos())

    def mouseMoveEvent(self, event):
        if self.dragNote is not None:
            self.dragNoteTo(event.pos())
            self.repaint()
        if self.stretchNote is not None:
            self.stretchNoteTo(event.pos())
            self.repaint()

    def mouseReleaseEvent(self, event):
        self.finalizeDragAndStretch()
        self.dragNote = None
        self.stretchNote = None
        self.update()
        # TODO: re-sort notes upon drop

    def wheelEvent(self, event):
        if self.pattern:
            self.offsetV += event.angleDelta().y() / 30
            self.offsetV = int(clip(self.offsetV, -24, self.pattern.max_note - self.numberKeysVisible))
            self.offsetH -= event.angleDelta().x() / 30
            self.offsetH = .25 * int(4 * clip(self.offsetH, 0, self.pattern.length - self.numberBeatsVisible))
            self.repaint()

    def activate(self):
        self.active = True
        self.activated.emit()

    def select(self, note):
        note.tag()
        self.pattern.selectFirstTaggedNoteAndUntag()
        self.noteSelected.emit(note)
        self.repaint()

    def finalizeDragAndStretch(self):
        if self.dragNote is not None:
            if self.dragNote.note_on < self.offsetH or self.dragNote.note_on > self.offsetH + self.numberBeatsVisible + 1 \
                or self.dragNote.note_off > self.pattern.length \
                or self.dragNote.note_pitch < self.offsetV or self.dragNote.note_pitch >= self.offsetV + self.numberKeysVisible:
                    self.dragNoteTo(self.dragOrigin)
            else:
                self.patternChanged.emit()
        if self.stretchNote is not None:
            print("TEST THIS")
            quit()


    def debugOutput(self):
        print("=== PATTERN ===")
        print(self.pattern)