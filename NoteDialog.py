from PyQt5 import QtWidgets
from may2Note import Note


class NoteDialog(QtWidgets.QDialog):

    WIDTH = 200
    HEIGHT = 200

    def __init__(self, parent, note, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.setWindowTitle('Note')
        self.setGeometry(parent.x() + 0.5 * (parent.width() - self.WIDTH), parent.y() + 0.5 * (parent.height() - self.HEIGHT), self.WIDTH, self.HEIGHT)
        self.parent = parent
        self.initNoteOn = note.note_on
        self.initNoteLen = note.note_len
        self.initNotePitch = note.note_pitch
        self.initNoteVel = note.note_vel
        self.initNotePan = note.note_pan
        self.initNoteSlide = note.note_slide
        self.initNoteAux = note.note_aux

        self.layout = QtWidgets.QVBoxLayout(self)

        self.mainFormLayout = QtWidgets.QFormLayout()

        self.noteOnSpinBox = QtWidgets.QDoubleSpinBox(self)
        self.noteOnSpinBox.setRange(0, 999)
        self.noteOnSpinBox.setSingleStep(0.01)
        self.mainFormLayout.addRow('NoteOn:', self.noteOnSpinBox)

        self.noteLenSpinBox = QtWidgets.QDoubleSpinBox(self)
        self.noteLenSpinBox.setRange(0.01, 999)
        self.noteLenSpinBox.setSingleStep(0.01)
        self.mainFormLayout.addRow('Length:', self.noteLenSpinBox)

        self.noteOffSpinBox = QtWidgets.QDoubleSpinBox(self)
        self.noteOffSpinBox.setRange(0, 999)
        self.noteOffSpinBox.setSingleStep(0.01)
        self.mainFormLayout.addRow('NoteOff:', self.noteOffSpinBox)

        self.notePitchSpinBox = QtWidgets.QSpinBox(self)
        self.notePitchSpinBox.setRange(-12, 88)
        self.mainFormLayout.addRow('Pitch (0 = C0):', self.notePitchSpinBox)

        self.noteVelSpinBox = QtWidgets.QSpinBox(self)
        self.noteVelSpinBox.setRange(0, 999)
        self.mainFormLayout.addRow('Velocity:', self.noteVelSpinBox)

        self.notePanSpinBox = QtWidgets.QSpinBox(self)
        self.notePanSpinBox.setRange(-100, 100)
        self.mainFormLayout.addRow('Pan:', self.notePanSpinBox)

        self.noteSlideSpinBox = QtWidgets.QDoubleSpinBox(self)
        self.noteSlideSpinBox.setRange(-96, 96)
        self.mainFormLayout.addRow('Slide From:', self.noteSlideSpinBox)

        self.noteAuxSpinBox = QtWidgets.QDoubleSpinBox(self)
        self.noteAuxSpinBox.setRange(-999, 999)
        self.mainFormLayout.addRow('Aux:', self.noteAuxSpinBox)

        self.layout.addLayout(self.mainFormLayout)

        self.buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel, self) # TODO: reset feature?
        self.layout.addWidget(self.buttonBox)

        self.setLayout(self.layout)

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.noteOnSpinBox.valueChanged.connect(self.adjustNoteOff)
        self.noteOffSpinBox.valueChanged.connect(self.adjustLength)
        self.noteLenSpinBox.valueChanged.connect(self.adjustNoteOff)

        self.init()

    def init(self):
        self.noteOnSpinBox.setValue(self.initNoteOn)
        self.noteOffSpinBox.setValue(self.initNoteOn + self.initNoteLen)
        self.noteLenSpinBox.setValue(self.initNoteLen)
        self.notePitchSpinBox.setValue(self.initNotePitch)
        self.noteVelSpinBox.setValue(self.initNoteVel)
        self.notePanSpinBox.setValue(self.initNotePan)
        self.noteSlideSpinBox.setValue(self.initNoteSlide)
        self.noteAuxSpinBox.setValue(self.initNoteAux)

    def adjustLength(self):
        self.noteLenSpinBox.setValue(self.noteOffSpinBox.value() - self.noteOnSpinBox.value())

    def adjustNoteOff(self):
        self.noteOffSpinBox.setValue(self.noteOnSpinBox.value() + self.noteLenSpinBox.value())

    def getNewNote(self):
        noteOn = self.noteOnSpinBox.value()
        noteOff = self.noteOffSpinBox.value()
        noteLen = self.noteLenSpinBox.value()
        if noteLen <= 0 or noteOff <= noteOn:
            return None
        newNote = Note(note_on = noteOn, note_len = noteLen, note_pitch = self.notePitchSpinBox.value())
        newNote.setVelocity(self.noteVelSpinBox.value())
        newNote.setPan(self.notePanSpinBox.value())
        newNote.setSlide(self.noteSlideSpinBox.value())
        newNote.setAuxParameter(self.noteAuxSpinBox.value())
        return newNote
