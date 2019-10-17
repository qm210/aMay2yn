from PyQt5.QtGui import QColor, QPainter, QFont
from PyQt5.QtWidgets import QWidget
from math import sqrt, floor
from numpy import clip

from may2Objects import *
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

quantize = lambda x, q: floor(x/q)*q

class May2PatternWidget(QWidget):

    claviature = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

    def __init__(self, parent):
        super().__init__()
        self.parent = parent

        self.pattern = Pattern(name = 'NJU', length = 6, synth_type = '_', max_note = 0)
        self.pattern.notes = [Note(note_on = 0.25, note_len = 0.5, note_pitch = 22)]
        self.active = False # Hope I don't need this too soon

        self.offsetV = 0
        self.offsetH = 0
        self.scaleV = 1
        self.scaleH = 1

        self.barsPerBeat = 4
        self.beatQuantum = 1/16

        self.dragNote = None
        self.dragOrigin = (None, None)
        self.dragPos = (None, None)
        self.dragNoteOrigin = None

        self.stretchNote = None
        self.stretchOrigin = None
        self.stretchPos = None
        self.stretchNoteOrigin = None


    def paintEvent(self, event):
        self.setGeometry(event)
        qp = QPainter()
        qp.begin(self)

        qp.setFont(QFont(may2Style.default_fontname, self.fontSize))

        qp.fillRect(self.X - PAD_L, self.Y - PAD_T, self.W + PAD_L + PAD_R, self.H + PAD_T + PAD_B, colorBG)

        self.drawBackground(qp)
        self.drawGrid(qp)
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
        self.T = self.Y

    def drawBackground(self, qp):

        isKeyWhite = lambda key: '#' not in self.claviature[key % 12]

        numberKeysVisible = int(self.H / self.keyH)
        self.T = self.B - self.keyH * (numberKeysVisible)

#        if self.active:
#            Color(1.,0.,1,.5)
#            Line(angle = [self.x + 3, self.y + 4, self.width - 7, self.height - 4], width = 1.5)

        for c in range(numberKeysVisible):
            key = self.offsetV + c
            y = self.B - (c + 1) * self.keyH

            qp.fillRect(self.X, y, self.keyW, (self.keyH - 1) + 0.7 * isKeyWhite(key), colorWhiteKeys if isKeyWhite(key) else colorBlackKeys)

            if self.pattern and self.pattern.notes and key == (self.pattern.getNote().note_pitch) % 100:
                qp.fillRect(self.X, y, self.keyW, (self.keyH - 1) + 0.7 * isKeyWhite(key), colorSelectedKey)

            qp.setPen(colorWhiteKeyText if isKeyWhite(key) else colorBlackKeyText)
            drawTextDoubleInY(qp, self.X + 2, y - 2.5, Qt.AlignLeft | Qt.AlignTop, self.claviature[key % 12] + str(key // 12), .5)

            qp.fillRect(self.rollX, y, self.rollW, self.keyH - 1, colorWhiteBG if isKeyWhite(key) else colorBlackBG)


    def drawGrid(self, qp):

        maxNumberBars = self.W - self.pianoW
        numberBarsVisible = 0 if not self.pattern else clip(4 * (self.pattern.length - self.offsetH), 0, maxNumberBars)

        x = self.X + self.pianoW

        qp.setPen(QColor(150, 200, 200)) # first grid label # HARDCODE
        qp.font().setPointSize(12) # HARDCODE
        drawText(qp, x, self.B + 1, Qt.AlignHCenter | Qt.AlignTop, f'{self.offsetH : .2f}')
        for b in range(numberBarsVisible):
            qp.setPen(QColor(13, 0, 13, 100)) # HARDCODE
            qp.pen().setWidthF(1.5 if b % 4 == 0 else 1) # WORKS NOT. WHY. SHIT.
            qp.drawLine(x, self.B, x, self.T)
            qp.pen().setWidthF(.3) # WORKS NOT. WHY. SHIT.
            x += 0.25 * self.barW
            qp.drawLine(x, self.B, x, self.T)
            x += 0.25 * self.barW
            qp.drawLine(x, self.B, x, self.T)
            x += 0.25 * self.barW
            qp.drawLine(x, self.B, x, self.T)
            x += 0.25 * self.barW
            qp.setPen(QColor(153, 204, 204)) # HARDCODE
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
            L, T, R, B = self.getRectOfNote(note)

            if note_on < 0 or L > self.R or T < self.T:
                continue

            #color = self.pattern.color
            #color.setAlpha
            color = QColor(255, 0, 0, 140)
            qp.fillRect(L + 1, T, R - L, B - T, color)
            if self.pattern.current_gap:
                qp.fillRect(R - 1, T + self.keyH / 2, self.beatW * self.pattern.current_gap, self.keyH / 4, QColor(255, 255, 255, 100))


    def getRectOfNote(self, note):
        coordL = self.X + self.pianoW + self.beatW * note.note_on
        coordR = coordL + self.beatW * note.note_len
        coordB = self.B - self.keyH * (note.note_pitch - self.offsetV)
        coordT = coordB - self.keyH
        return coordL, coordT, coordR, coordB

    def findNextNeighbor(self, coordX, coordY):
        nextNeighbor = None
        minDistance = None
        for note in self.pattern.notes:
            L, T, R, B = self.getRectOfNote(note)
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

    def dragNoteRelativeToNoteOrigin(self, pos):
        noteDistance = self.getDistanceInNoteUnits(pos.x() - self.dragOrigin.x(), pos.y() - self.dragOrigin.y())
        self.dragNote.note_on = self.dragNoteOrigin[0] + quantize(noteDistance[0], self.beatQuantum)
        self.dragNote.note_pitch = self.dragNoteOrigin[1] + quantize(noteDistance[1], 1)

    def initStretchNote(self, note, origin):
        if self.stretchNote is None:
            self.stretchNote = note
            self.stretchOrigin = origin
            self.stretchNoteOrigin = note.note_len

    def stretchNoteRelativeToNoteOrigin(self, pos):
        noteDistance = self.getDistanceInNoteUnits(pos.x() - self.stretchOrigin.x(), 0)
        self.stretchNote.note_len = self.stretchNoteOrigin + quantize(noteDistance[0], self.beatQuantum)

    def mousePressEvent(self, event):
        nextNote = self.findNextNeighbor(event.pos().x(), event.pos().y())
        if nextNote is None:
            return
        if event.button() == Qt.LeftButton:
            self.initDragNote(nextNote, event.pos())
        if event.button() == Qt.RightButton:
            self.initStretchNote(nextNote, event.pos())

    def mouseMoveEvent(self, event):
        if self.dragNote is not None:
            self.dragNoteRelativeToNoteOrigin(event.pos())
            self.repaint()
        if self.stretchNote is not None:
            self.stretchNoteRelativeToNoteOrigin(event.pos())
            self.repaint()

    def mouseReleaseEvent(self, event):
        self.dragNote = None
        self.stretchNote = None
        self.update()