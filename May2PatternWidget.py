from PyQt5.QtGui import QColor, QPainter, QFont
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import pyqtSignal
from math import sqrt, floor
from numpy import clip
from copy import deepcopy

from may2Objects import Pattern, Note
from may2PatternModel import PatternModel
from may2Utils import * # pylint: disable=unused-wildcard-import
from NoteDialog import NoteDialog
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
PAD_B = 16

CLICK_PRECISION = 1.03


class May2PatternWidget(QWidget):

    noteSelected = pyqtSignal(int)
    patternChanged = pyqtSignal()
    activated = pyqtSignal()

    claviature = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

    def __init__(self, parent, drumMode = False):
        super().__init__()
        self.parent = parent
        self.active = False
        self.numberInput = ''
        self.drumMode = drumMode

        self.offsetV = 12 if not drumMode else 0
        self.offsetH = 0
        self.scaleV = 1
        self.scaleH = 1

        self.dragNote = None
        self.dragOrigin = (None, None)
        self.dragNoteOrigin = None

        self.stretchNote = None
        self.stretchOrigin = None
        self.stretchPos = None
        self.stretchNoteOrigin = None

        self.pattern = None
        self.copyOfLastSelectedNote = None

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
        self.drawNumberInput(qp)
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
        self.keyBaseH = 10 if not self.drumMode else 30
        self.keyH = self.keyBaseH * self.scaleV
        self.keyW = 32 * self.scaleH
        self.pianoW = 34 * self.scaleH

        self.fontSize = max(9 * min(self.scaleH, self.scaleV), 5)
        self.fontSizeParameters = max(self.fontSize * sqrt(self.scaleH), 5)
        self.fontSizeNumberInput = 13
        self.barW = 48 * self.scaleH
        self.beatW = self.barsPerBeat() * self.barW

        self.rollX = self.X + self.pianoW
        self.rollW = self.R - self.rollX

        self.numberKeysVisible = int(self.H / self.keyH)
        self.T = self.B - self.keyH * (self.numberKeysVisible)

        self.maxNumberBars = (self.W - self.pianoW) / self.barW
        self.numberBarsVisible = 0 if not self.pattern else int(clip(self.barsPerBeat() * (self.pattern.length - self.offsetH), 0, self.maxNumberBars))
        self.numberBeatsVisible = self.numberBarsVisible / self.barsPerBeat()

        if self.drumMode:
            self.numberDrums = self.parent.drumModel.rowCount()
            self.numberDrumsVisible = min(self.numberKeysVisible, self.numberDrums)
            self.minOffsetV = 0
            self.maxOffsetV = self.numberDrums - self.numberDrumsVisible
        else:
            self.minOffsetV = -24
            self.maxOffsetV = 0 if not self.pattern else (self.pattern.max_note - self.numberKeysVisible)


    def drawBackground(self, qp):
        if self.drumMode:
            self.drawDrumBackground(qp)
        else:
            self.drawSynthBackground(qp)

    def drawSynthBackground(self, qp):

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

    def drawDrumBackground(self, qp):

        isRowWhite = lambda row: row % 2 == 0

        font = qp.font()

        for c in range(self.numberDrumsVisible):
            key = self.offsetV + c
            y = self.B - (c + 1) * self.keyH

            qp.fillRect(self.X, y, self.keyW, (self.keyH - 1) + 0.7 * isRowWhite(key), colorWhiteKeys if isRowWhite(key) else colorBlackKeys)

            if self.pattern and self.pattern.notes and key == (self.pattern.getNote().note_pitch) % self.numberDrums:
                qp.fillRect(self.X, y, self.keyW, (self.keyH - 1) + 0.7 * isRowWhite(key), colorSelectedKey)

            qp.setPen(colorWhiteKeyText if isRowWhite(key) else colorBlackKeyText)
            drumName = self.parent.drumModel.stringList()[key]
            if len(drumName) < 5:
                font.setPointSize(self.fontSize)
                qp.setFont(font)
                drawTextDoubleInY(qp, self.X + 2, y - 2.5, Qt.AlignLeft | Qt.AlignTop, drumName[0:4], .5)
            elif len(drumName) < 9:
                font.setPointSize(self.fontSize)
                qp.setFont(font)
                drawTextDoubleInY(qp, self.X + 2, y - 2.5, Qt.AlignLeft | Qt.AlignTop, drumName[0:4], .5)
                drawTextDoubleInY(qp, self.X + 2, y - 2.5 + self.fontSize, Qt.AlignLeft | Qt.AlignTop, drumName[4:8], .5)
            elif len(drumName) < 11:
                font.setPointSize(self.fontSize - 1)
                qp.setFont(font)
                drawTextDoubleInY(qp, self.X + 2, y - 2.5, Qt.AlignLeft | Qt.AlignTop, drumName[0:5], .5)
                drawTextDoubleInY(qp, self.X + 2, y - 2.5 + self.fontSize, Qt.AlignLeft | Qt.AlignTop, drumName[5:10], .5)
            else:
                font.setPointSize(self.fontSize - 1)
                qp.setFont(font)
                drawTextDoubleInY(qp, self.X + 2, y - 2.5, Qt.AlignLeft | Qt.AlignTop, drumName[0:5], .5)
                drawTextDoubleInY(qp, self.X + 2, y - 2.5 + self.fontSize, Qt.AlignLeft | Qt.AlignTop, drumName[5:10], .5)
                drawTextDoubleInY(qp, self.X + 2, y - 2.5 + self.fontSize * 2, Qt.AlignLeft | Qt.AlignTop, drumName[10:15], .5)

            qp.fillRect(self.rollX, y, self.rollW, self.keyH - 1, colorWhiteBG if isRowWhite(key) else colorBlackBG)


    def drawGrid(self, qp):

        x = self.X + self.pianoW

        qp.setPen(QColor(150, 200, 200)) # first grid label # HARDCODE
        qp.font().setPointSize(12) # HARDCODE
        drawText(qp, x, self.B + 1, Qt.AlignHCenter | Qt.AlignTop, f'{self.offsetH : .2f}')
        pen = qp.pen()
        for b in range(self.numberBarsVisible):
            pen.setColor(QColor(13, 0, 13, 100)) # HARDCODE
            pen.setWidthF(1.5 if b % self.barsPerBeat() == 0 else 1)
            qp.setPen(pen)
            qp.drawLine(x, self.B, x, self.T)
            pen.setWidthF(.3)
            qp.setPen(pen)
            for _ in range(3):
                x += 0.25 * self.barW
                qp.drawLine(x, self.B, x, self.T)
            x += 0.25 * self.barW
            pen.setColor(QColor(153, 204, 204)) # HARDCODE
            qp.setPen(pen)
            drawText(qp, x, self.B + 1, Qt.AlignHCenter | Qt.AlignTop, f'{(b+1)/self.barsPerBeat() + self.offsetH : .2f}')

        # END SEGMENT
        if self.pattern is None:
            endX = self.X + self.pianoW
        else:
            endX = self.X + self.pianoW + self.beatW * (self.pattern.length - self.offsetH)
        if endX > 0 and endX < self.R:
            qp.fillRect(endX, self.B, self.R - endX, self.T - self.B, QColor(0, 0, 0, 75)) # HARDCODE
            pen = qp.pen()
            pen.setColor(Qt.black)
            pen.setWidthF(2)
            qp.setPen(pen)
            qp.drawLine(endX, self.B, endX, self.T)

    def drawNumberInput(self, qp):
        font = qp.font()
        font.setPointSize(self.fontSizeNumberInput)
        qp.setFont(font)
        qp.setPen(QColor(255, 0, 255, 230))
        if not self.numberInput:
            return
        boxW = len(self.numberInput) * .763 * self.fontSizeNumberInput + 2
        boxH = 1.6 * self.fontSizeNumberInput
        qp.fillRect(self.R, self.B, -boxW, -boxH, colorBG)
        drawText(qp, self.R, self.B, Qt.AlignRight, self.numberInput)


    def drawNotes(self, qp):
        if self.pattern is None:
            return
        font = qp.font()
        color = self.parent.getPatternColor(self.pattern._hash)

        for note in self.pattern.notes:
            note_on = note.note_on - self.offsetH
            L, R, T, B = self.getRectOfNote(note)
            if note_on < 0 or L > self.R or T < self.T:
                continue
            qp.fillRect(L + 1, T, R - L - 1, B - T - 1, QColor(*color, 140))
            if note == self.pattern.getNote():
                qp.fillRect(L + 1, T, R - L - 1, B - T - 1, QColor(255, 255, 255, 150))
                if self.pattern.currentGap:
                    qp.fillRect(R - 1, T + self.keyH / 2, self.beatW * self.pattern.currentGap, self.keyH / 4, QColor(255, 255, 255, 100))

            font.setPointSize(self.fontSizeParameters - (1 if note.note_len >= .125 else 2))
            qp.setFont(font)

            if note.note_pan != 0:
                qp.setPen(QColor(*(mixcolor((255, 255, 255), color))))
                drawText(qp, R, B - 2, Qt.AlignTop | Qt.AlignRight, strfloat(note.note_pan))

            vel_and_aux_info = ''
            if note.note_aux != 0:
                vel_and_aux_info = f"({strfloat(note.note_aux)})"
            if any(n.note_vel != 100 for n in self.pattern.notes):
                vel_and_aux_info += strfloat(note.note_vel)
            if vel_and_aux_info != '':
                qp.setPen(QColor(*(mixcolor((0, 0, 0), color) if note == self.pattern.getNote() else mixcolor((255, 255, 255), color))))
                drawText(qp, R, B + 1, Qt.AlignBottom | Qt.AlignRight, vel_and_aux_info)

            if note.note_slide != 0:
                qp.setPen(QColor(*(mixcolor((1,1,1), color))))
                drawText(qp, R, T, Qt.AlignBottom | Qt.AlignRight, strfloat(note.note_slide))


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

    def getPositionInNoteUnits(self, coordX, coordY):
        distanceToCorner = self.getDistanceInNoteUnits(coordX - self.rollX, coordY - self.B)
        distanceX = quantize(distanceToCorner[0], self.beatQuantum())
        distanceY = quantize(distanceToCorner[1], 1)
        return (distanceX + self.offsetH, distanceY + self.offsetV)

    def getDistanceInNoteUnits(self, deltaX, deltaY):
        return (deltaX / self.beatW, -deltaY / self.keyH)

    def initDragNote(self, note, origin):
        if self.dragNote is None:
            self.dragNote = note
            self.dragOrigin = origin
            self.dragNoteOrigin = (note.note_on, note.note_pitch)

    def dragNoteTo(self, pos):
        noteDistance = self.getDistanceInNoteUnits(pos.x() - self.dragOrigin.x(), pos.y() - self.dragOrigin.y())
        if not self.parent.shiftPressed:
            self.dragNote.moveNoteOn(quantize(self.dragNoteOrigin[0] + noteDistance[0], self.beatQuantum()))
        self.dragNote.note_pitch = quantize(self.dragNoteOrigin[1] + noteDistance[1], 1)

    def initStretchNote(self, note, origin):
        if self.stretchNote is None:
            self.stretchNote = note
            self.stretchOrigin = origin
            self.stretchNoteOrigin = note.note_len

    def stretchNoteTo(self, pos):
        noteDistance = self.getDistanceInNoteUnits(pos.x() - self.stretchOrigin.x(), 0)
        self.stretchNote.note_len = quantize(max(self.stretchNoteOrigin + noteDistance[0], self.beatQuantum()), self.beatQuantum())

    def mousePressEvent(self, event):
        if not self.active:
            self.activate()

        if self.parent.ctrlPressed and event.button() == Qt.MiddleButton:
            self.setScale(H = 1, V = 1)
            return

        corrNote = self.findCorrespondingNote(event.pos().x(), event.pos().y())
        if corrNote is None:
            if event.button() == Qt.LeftButton:
                self.insertNote(self.copyOfLastSelectedNote, event.pos(), copyParameters = False, initDrag = True)
            elif event.button() == Qt.MiddleButton:
                self.openInsertNoteDialog(self.copyOfLastSelectedNote, event.pos())
            return

        noteAlreadySelected = (corrNote == self.pattern.getNote()) # TOOD: use this, or ctrlPressed, to somehow change the parameters
        self.select(corrNote)
        if event.button() == Qt.LeftButton:
            if self.parent.ctrlPressed:
                self.openNoteDialog(corrNote)
            else:
                self.initDragNote(corrNote, event.pos())
        if event.button() == Qt.RightButton:
            self.initStretchNote(corrNote, event.pos())
        if event.button() == Qt.MiddleButton:
            self.deleteNote(corrNote)

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
        if self.parent.ctrlPressed:
            self.setScale(deltaH = event.angleDelta().y() / 1200)
        else:
            if self.pattern:
                if self.parent.shiftPressed:
                    xScroll = -event.angleDelta().y() / 120
                    yScroll = 0
                else:
                    xScroll = event.angleDelta().x() / 120
                    yScroll = event.angleDelta().y() / 30
                self.offsetV = int(clip(self.offsetV + yScroll, self.minOffsetV, self.maxOffsetV))
                self.offsetH = .25 * int(4 * clip(self.offsetH - xScroll, 0, self.pattern.length - self.numberBeatsVisible))
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

    def select(self, note):
        note.tag()
        self.pattern.selectFirstTaggedNoteAndUntag()
        self.noteSelected.emit(note)
        self.repaint()
        self.copyOfLastSelectedNote = deepcopy(note)

    def finalizeDragAndStretch(self):
        # do I want to bring the notes in sorted order now?
        if self.dragNote is not None:
            if self.dragNote.note_on < self.offsetH or self.dragNote.note_on > self.offsetH + self.numberBeatsVisible + 1 \
                or self.dragNote.note_off > self.pattern.length \
                or self.dragNote.note_pitch < self.offsetV or self.dragNote.note_pitch >= self.offsetV + self.numberKeysVisible:
                    self.dragNoteTo(self.dragOrigin)
            else:
                self.finalizePatternChangeAndEmit()
        if self.stretchNote is not None:
            if self.stretchNote.note_off > self.pattern.length:
                self.moveNoteOff(self.pattern.length)
            if self.stretchNote.note_len < 0:
                self.stretchNoteTo(self.stretchOrigin)
            else:
                self.finalizePatternChangeAndEmit()

    def finalizePatternChangeAndEmit(self):
        self.pattern.ensureOrder()
        self.patternChanged.emit()

    def openNoteDialog(self, note):
        noteDialog = NoteDialog(self.parent, note = note)
        if noteDialog.exec_():
            self.pattern.delNote(specificNote = note)
            newNote = noteDialog.getNewNote()
            self.pattern.addNote(newNote)
            self.select(self.pattern.findSuchANote(newNote))
            self.finalizePatternChangeAndEmit()

    def insertNote(self, notePrototype, pos, copyParameters = False, initDrag = False):
        if notePrototype is None:
            notePrototype = Note(note_len = 1)
        notePos = self.getPositionInNoteUnits(pos.x(), pos.y())
        if copyParameters:
            newNote = notePrototype
        else:
            newNote = Note(note_len = notePrototype.note_len)
        newNote.moveNoteOn(notePos[0])
        newNote.note_pitch = notePos[1]
        self.pattern.addNote(newNote)
        if initDrag:
            self.initDragNote(self.pattern.getNote(), pos)
        self.finalizePatternChangeAndEmit()

    def openInsertNoteDialog(self, notePrototype, pos):
        notePos = self.getPositionInNoteUnits(pos.x(), pos.y())
        if notePrototype is None:
            notePrototype = Note()
        notePrototype.note_on = notePos[0]
        notePrototype.note_pitch = notePos[1]
        noteDialog = NoteDialog(self.parent, note = notePrototype)
        if noteDialog.exec_():
            newNote = noteDialog.getNewNote()
            if newNote is None:
                return
            self.pattern.addNote(newNote)
            self.select(self.pattern.findSuchANote(newNote))
            self.finalizePatternChangeAndEmit()

    def deleteNote(self, note):
        self.pattern.delNote(note)
        self.finalizePatternChangeAndEmit()


    def setNumberInput(self, numberInput):
        self.numberInput = numberInput
        self.update()

    def barsPerBeat(self):
        return self.parent.info['barsPerBeat']

    def beatQuantum(self):
        return self.parent.info['beatQuantum'] * 4/self.barsPerBeat() # the last factor is some hack, but it's only three days to Vortex

    def debugOutput(self):
        print("=== PATTERN ===")
        print(self.pattern)