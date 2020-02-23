from copy import deepcopy

from may2Note import Note

SYNTHTYPE, DRUMTYPE, NONETYPE = ['I', 'D', '_']

class Pattern:

    def __init__(self, name = 'NJU', length = 1, synthType = '_', max_note = 0, _hash = None):
        self._hash = _hash or hash(self)
        self.name = name
        self.notes = []
        self.length = length if length and length > 0 else 1
        self.currentNoteIndex = 0
        self.currentGap = 0
        self.setTypeParam(synthType = synthType, max_note = max_note if max_note > 0 else 88)

    def __repr__(self):
        return ','.join(str(i) for i in [self.name, self.notes, self.length, self.currentNoteIndex, self.synthType])

    def isDuplicateOf(self, other, transposed = 0):
        return len(self.notes) == len(other.notes) and all(nS == (nO + transposed) for nS, nO in zip(self.notes, other.notes))

    def setTypeParam(self, synthType = None, max_note = None):
        if synthType:
            self.synthType = synthType
        if max_note:
            self.max_note = max_note
            for n in self.notes:
                n.note_pitch = n.note_pitch % max_note

    def rehash(self):
        self.notes = deepcopy(self.notes)
        self._hash = hash(self)

    # helpers...
    def getNote(self, offset=0):
        return self.notes[(self.currentNoteIndex + offset) % len(self.notes)] if self.notes else None
    def getNoteOn(self, offset=0):
        return self.getNote(offset).note_on if self.getNote(offset) else None
    def getNoteOff(self, offset=0):
        return self.getNote(offset).note_off if self.getNote(offset) else None
    def getFirstNote(self):
        return self.notes[0]  if self.notes else None
    def getLastNote(self):
        return self.notes[-1] if self.notes else None
    def getFirstTaggedNoteIndex(self):
        return next(i for i in range(len(self.notes)) if self.notes[i].tagged)
    def isEmpty(self):
        return False if self.notes else True
    def getDrumIndex(self):
        return self.getNote().note_pitch if self.getNote() and self.synthType == DRUMTYPE else None

    def selectFirstTaggedNoteAndUntag(self):
        self.currentNoteIndex = self.getFirstTaggedNoteIndex()
        self.notes[self.currentNoteIndex].tag(False)

    def findIndexOfNote(self, note):
        for i, n in enumerate(self.notes):
            if n == note:
                return i
        return None


    def addNote(self, note = None, select = True, append = False, clone = False):
        if note is None:
            note = Note()
            append = False
        if clone:
            select = False

        note = Note( \
            note_on = note.note_on + append * note.note_len + self.currentGap, \
            note_len = note.note_len, \
            note_pitch = note.note_pitch % self.max_note, \
            note_pan = note.note_pan, \
            note_vel = note.note_vel, \
            note_slide = note.note_slide, \
            note_aux = note.note_aux \
            )
        note.tag()

        if note.note_off > self.length:
            note.note_off = self.length
            note.note_len = note.note_off - note.note_on

        self.notes.append(note)
        self.notes.sort(key = lambda n: (n.note_on, n.note_pitch))
        self.currentNoteIndex = self.getFirstTaggedNoteIndex()
        self.untagAllNotes()
        # cloning: since we have polyphonic mode now, we can not just assign the right gap - have to do it via space/backspace - will be changed to polyphonic cloning
        if not clone:
            self.setGap(to = 0)
        return note


    def fillNote(self, note = None): #this is for instant pattern creation... copy the content during the current note (plus gap) and repeat it as long as the pattern allows to
        if note is None:
            return

        copy_span = note.note_len + self.currentGap
        copy_pos = note.note_off + self.currentGap
        note.tag()

        notes_to_copy = [n for n in self.notes if n.note_on <= copy_pos and n.note_off > note.note_on]
        print("yanked some notes, ", len(notes_to_copy), notes_to_copy)

        while copy_pos + copy_span <= self.length:
            for n in notes_to_copy:
                copy_on = copy_pos + n.note_on - note.note_on
                copy_len = n.note_len

                if n.note_on < note.note_on:
                    copy_on = copy_pos
                    copy_len = n.note_len - (note.note_on - n.note_on)
                if n.note_off > note.note_off:
                    copy_len = note.note_off - n.note_on

                self.notes.append(Note( \
                    note_on = copy_on, \
                    note_len = copy_len, \
                    note_pitch = n.note_pitch, \
                    note_pan = n.note_pan, \
                    note_vel = n.note_vel, \
                    note_slide = n.note_slide \
                    ))

            copy_pos += copy_span

        self.notes.sort(key = lambda n: (n.note_on, n.note_pitch))
        self.currentNoteIndex = self.getFirstTaggedNoteIndex()
        self.untagAllNotes()

    def delNote(self, specificNote = None):
        if self.notes:
            if specificNote is not None:
                self.currentNoteIndex = self.findIndexOfNote(specificNote)
            old_note = self.currentNoteIndex
            old_pitch = self.notes[old_note].note_pitch

            del self.notes[self.currentNoteIndex if self.currentNoteIndex is not None else -1]

            if self.currentNoteIndex > 0:
                self.currentNoteIndex = min(self.currentNoteIndex-1, len(self.notes)-1)

            if self.synthType == DRUMTYPE:
                for n in self.notes[old_note:] + self.notes[0:old_note-1]:
                    if n.note_pitch == old_pitch:
                        n.tag()
                        self.notes.sort(key = lambda n: (n.note_on, n.note_pitch))
                        self.currentNoteIndex = self.getFirstTaggedNoteIndex()
                        self.untagAllNotes()
                        break

    def setGap(self, to = 0, inc = False, dec = False):
        if self.notes:
            if inc:
                self.currentGap += self.getNote().note_len
            elif dec:
                self.currentGap = max(self.currentGap - self.getNote().note_len, 0)
            elif to is not None:
                self.currentGap = to
            else:
                pass

    def untagAllNotes(self):
        for n in self.notes:
            n.tagged = False

    def switchNote(self, inc, to = -1, same_pitch = False):
        if self.notes:
            if inc != 0:
                if same_pitch:
                    while self.getNote(offset = inc).note_pitch != self.getNote().note_pitch and abs(inc) < len(self.notes):
                        inc += 1 if inc > 0 else -1
                self.currentNoteIndex = (self.currentNoteIndex + inc) % len(self.notes)
            else:
                self.currentNoteIndex = (len(self.notes) + to) % len(self.notes)

    def shiftNote(self, inc):
        if self.notes:
            self.getNote().note_pitch = (self.getNote().note_pitch + inc) % self.max_note

    def shiftAllNotes(self, inc):
        notes = self.notes if not self.synthType == DRUMTYPE else [n for n in self.notes if n.note_pitch == self.getNote().note_pitch]
        if notes:
            for n in notes:
                n.note_pitch = (n.note_pitch + inc) % self.max_note
                #idea: for drum patterns - skip those drums ('notes') that already have something in there
                #TODO: different kind of drum editor! completely grid-based!!

    def stretchNote(self, inc):
        # here I had lots of possibilities .. is inc > or < 0? but these where on the monophonic synth. Let's rethink polyphonic!
        if self.notes:
            if inc < 0:
                if self.getNote().note_len <= 1/32:
                    self.getNote().note_len = 1/64
                elif self.getNote().note_len <= -inc:
                    self.getNote().note_len /= 2
                else:
                    self.getNote().note_len -= -inc
            else:
                if self.getNote().note_len <= inc:
                    self.getNote().note_len *= 2
                else:
                    self.getNote().note_len = max(0, min(self.length - self.getNote().note_on, self.getNote().note_len + inc))

            self.getNote().note_off = self.getNote().note_on + self.getNote().note_len

    def moveNote(self, inc):
        # same as with stretch: rethink for special Käses?
        if self.notes:
            if abs(self.getNote().note_len) < abs(inc):
                inc = abs(inc)/inc * self.getNote().note_len

        self.getNote().tag()

        if self.getNoteOff() == self.length and inc > 0:
            self.getNote().moveNoteOn(0)

        elif self.getNoteOn() == 0 and inc < 0:
            self.getNote().moveNoteOff(self.length)

        else:
            self.getNote().note_on = max(0, min(self.length - self.getNote().note_len, self.getNote().note_on + inc))
            self.getNote().note_off = self.getNote().note_on + self.getNote().note_len

        self.notes.sort(key = lambda n: (n.note_on, n.note_pitch))
        self.currentNoteIndex = self.getFirstTaggedNoteIndex()
        self.untagAllNotes()

    def moveAllNotes(self, inc):
        if not self.notes:
            return
        for n in self.notes:
            if n.note_on + inc < 0 or n.note_off + inc > self.length:
                return
        for n in self.notes:
            n.note_on += inc
            n.note_off += inc

    def stretchPattern(self, inc, scale = False):
        if self.length + inc <= 0:
            return

        old_length = self.length
        self.length = self.length + inc

        # fun gimmick: option to really stretch (scale all notes) the pattern ;)
        if scale:
            factor = self.length/old_length
            for n in self.notes:
                n.note_on *= factor
                n.note_off *= factor
                n.note_len *= factor

        # remove notes beyond pattern (TODO after release of shift / after timer?)
        for n in reversed(self.notes):
            if n.note_on > self.length:
                self.notes = self.notes[:-1]
            elif n.note_off > self.length:
                n.note_off = self.length
                n.note_len = n.note_off - n.note_on
            else:
                break

    def applyDrumMap(self, drumMap):
        if self.synthType != DRUMTYPE or not self.notes:
            return
        print(self.max_note, len(drumMap))
        self.max_note = len(drumMap) - 1
        for note in self.notes:
            note.note_pitch = drumMap[note.note_pitch] if note.note_pitch < len(drumMap) else self.max_note

    def ensureOrder(self):
        if self.notes:
            self.getNote().tag()
            self.notes.sort(key = lambda n: (n.note_on, n.note_pitch))
            self.currentNoteIndex = self.getFirstTaggedNoteIndex()
            self.untagAllNotes()

    def getCopy(self):
        newPattern = Pattern(name = self.name, length=self.length, synthType = self.synthType, max_note = self.max_note)
        newPattern.notes = deepcopy(self.notes)
        return newPattern

    ### DEBUG ###
    def printNoteList(self):
        for n in self.notes:
            print('on', n.note_on, 'off', n.note_off, 'len', n.note_len, 'pitch', n.note_pitch, 'pan', n.note_pan, 'vel', n.note_vel, 'slide', n.note_slide)
