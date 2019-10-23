from copy import copy
from numpy import clip
import random
import json


SYNTHTYPE, DRUMTYPE, NONETYPE = ['I', 'D', '_']

class Track:

    def __init__(self, name = '', synthName = None, synthType = None):
        self.name = name
        self.synthName = synthName or 'None'
        self.synthType = synthType or NONETYPE
        self.modules = []
        self.currentModuleIndex = 0
        self.volume = 1
        self.mute = False

    def __repr__(self):
        return ','.join(str(i) for i in [self.name, self.synthName, self.synthType, self.modules, self.currentModuleIndex])

    # helpers...
    def getModule(self, offset = 0):
        return self.modules[(self.currentModuleIndex + offset) % len(self.modules)] if self.modules else None
    def getModuleOn(self, offset = 0):
        return self.getModule(offset).mod_on
    def getModuleLen(self, offset = 0):
        return self.getModule(offset).patternLength
    def getModuleOff(self, offset = 0):
        return self.getModule(offset).getModuleOff()
    def getFirstModule(self):
        return self.modules[0]  if len(self.modules) > 0 else None
    def getFirstModuleOn(self):
        return self.getFirstModule().mod_on if self.getFirstModule() else None
    def getLastModule(self):
        return self.modules[-1] if len(self.modules) > 0 else None
    def getLastModuleOff(self):
        return self.getLastModule().getModuleOff() if self.getLastModule() else 0
    def getFirstTaggedModuleIndex(self):
        return next(i for i in range(len(self.modules)) if self.modules[i].tagged)
    def getSynthFullName(self):
        return f'{self.synthType}_{self.synthName}'
    def isDrumTrack(self):
        return self.synthType == DRUMTYPE
    def isEmpty(self):
        return (self.modules == [])

    def selectFirstTaggedModule(self):
        self.currentModuleIndex = self.getFirstTaggedModuleIndex()

    def selectFirstTaggedModuleAndUntag(self):
        self.currentModuleIndex = self.getFirstTaggedModuleIndex()
        self.modules[self.currentModuleIndex].tag(False)

    def findIndexOfModule(self, module):
        for i, m in enumerate(self.modules):
            if m == module:
                return i
        return None

    def cloneTrack(self, track):
        self.modules = [copy(m) for m in track.modules]
        self.currentModuleIndex = track.current_module
        self.current_synth = track.current_synth

    def addModuleFromPattern(self, pattern, transpose = 0):
        modOn = self.getModuleOff() if self.modules else 0
        newModule = Module(modOn, pattern, transpose)
        self.addModule(newModule)

    def addModule(self, newModule, forceModOn = True):
        if not self.modules:
            self.modules.append(newModule)
            return
        newModule.tag()
        self.modules.append(newModule)
        self.modules.sort(key = lambda m: m.mod_on)
        if not forceModOn:
            self.selectFirstTaggedModule()
            while newModule.collidesWithAnyOf(self.modules):
                self.moveModule(+1)
                self.modules.sort(key = lambda m: m.mod_on)
                self.selectFirstTaggedModule()
            self.untagAllModules()

    def delModule(self):
        if self.modules:
            del self.modules[self.currentModuleIndex if self.currentModuleIndex is not None else -1]
            self.currentModuleIndex = min(self.currentModuleIndex, len(self.modules)-1)

    def switchModule(self, inc, to = None):
        if self.modules:
            if to is None:
                self.currentModuleIndex = (self.currentModuleIndex + inc) % len(self.modules)
            else:
                self.currentModuleIndex = (to + len(self.modules)) % len(self.modules)

    def transposeModule(self, inc):
        if self.modules:
            self.getModule().transpose += inc

    def moveModule(self, inc, move_home = None, move_end = None, total_length = None):
        if self.modules:
            move_to = self.getModuleOn() + inc
            if move_to < 0: return
            try_leap = 0

            if inc < 0:
                if self.getModule() != self.getFirstModule():
                    while move_to < self.getModuleOff(try_leap-1):
                        try_leap -=1
                        move_to = self.getModuleOn(try_leap) - self.getModuleLen()
                        if move_to < 0: return
                        if move_to + self.getModuleLen() <= self.getFirstModuleOn(): break

            else:
                if self.getModule() != self.getLastModule():
                    while move_to + self.getModuleLen() > self.getModuleOn(try_leap+1):
                        try_leap += 1
                        move_to = self.getModuleOff(try_leap)
                        if move_to >= self.getLastModuleOff(): break

            self.getModule().move(move_to)
            self.currentModuleIndex += try_leap
            self.modules.sort(key = lambda m: m.mod_on)

        if move_home:
            self.getModule().move(-1)
            self.modules.sort(key = lambda m: m.mod_on)
            self.currentModuleIndex = 0
            self.moveModule(+1)
        if move_end:
            if self.getModule() != self.getLastModule():
                self.getModule().move(self.getLastModuleOff())
                self.modules.sort(key = lambda m: m.mod_on)
                self.currentModuleIndex = len(self.modules) - 1
            elif total_length is not None:
                self.getModule().move(total_length - self.getModuleLen())

    def moveModuleAnywhere(self, move_to):
        self.getModule().tag()
        self.getModule().move(move_to)
        self.modules.sort(key = lambda m: m.mod_on)
        self.currentModuleIndex = self.getFirstTaggedModuleIndex()
        self.untagAllModules()

    def moveAllModules(self, inc):
        if self.modules:
            if (self.getFirstModuleOn() + inc < 0):
                return
        for m in self.modules:
            m.mod_on += inc

    def clearModules(self):
        self.modules=[]

    def setSynth(self, name = None, type = None, fullName = None):
        if fullName is not None:
            self.synthType = fullName[0]
            self.synthName = fullName[2:]
        if name is not None:
            self.synthName = name
        if type is not None:
            self.synthType = type

    def setParameters(self, volume = None, mute = None):
        if volume is not None:
            self.volume = float(volume)
        if mute is not None:
            self.mute = mute

    def untagAllModules(self):
        for m in self.modules:
            m.tagged = False


class Module:

    patternHash = None
    patternName = None
    patternLength = None

    def __init__(self, mod_on, pattern = None, transpose = 0, copyModule = None):
        self.mod_on = mod_on
        self.transpose = transpose
        self.tagged = False
        if pattern is not None:
            self.setPattern(pattern)
        elif copyModule is not None:
            self.patternHash = copyModule.patternHash
            self.patternName = copyModule.patternName
            self.patternLength = copyModule.patternLength

    def setPattern(self, pattern):
        self.patternHash = pattern._hash
        self.patternName = pattern.name
        self.patternLength = pattern.length

    def __repr__(self):
        return 'Module[' + ','.join(str(i) for i in [self.mod_on, self.getModuleOff(), self.patternName, self.transpose]) + ']'

    def getModuleOn(self):
        return self.mod_on

    def getModuleOff(self):
        return self.mod_on + self.patternLength

    def move(self, move_to):
        self.mod_on = move_to

    def tag(self, tagged = True):
        self.tagged = tagged

    def collidesWithAnyOf(self, modules):
        for m in modules:
            if m == self:
                continue
            if self.getModuleOn() <= m.getModuleOn() and self.getModuleOff() > m.getModuleOn():
                return True
            if self.getModuleOn() < m.getModuleOff() and self.getModuleOff() > m.getModuleOff():
                return True
        return False



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

    def isDuplicateOf(self, other):
        return len(self.notes) == len(other.notes) and all(nS == nO for nS, nO in zip(self.notes, other.notes))

    def setTypeParam(self, synthType = None, max_note = None):
        if synthType:
            self.synthType = synthType
        if max_note:
            self.max_note = max_note
            for n in self.notes:
                n.note_pitch = n.note_pitch % max_note

    def replaceWith(self, other):
        if not other: return
        self.name = other.name
        self.notes = other.notes
        self.length = other.length
        self.currentNoteIndex = other.currentNote
        self.currentGap = other.currentGap
        self.synthType = other.synthType
        self.max_note = other.max_note
        print("[DEBUG] WHEN IS THIS CALLED? NEED TO FIGURE OUT WHAT TO DO WITH HASH")
        quit()

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
        if clone: select = False

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
        if not clone: self.setGap(to = 0)


    def fillNote(self, note = None): #this is for instant pattern creation... copy the content during the current note (plus gap) and repeat it as long as the pattern allows to
        if note is None: return

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
                if abs(self.getNote().note_len) < abs(inc): inc = abs(inc)/inc * self.getNote().note_len

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
        if self.length + inc <= 0: return

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

    def updateDrumkit(self, old_drumkit, new_drumkit):
        if not self.synthType == DRUMTYPE or not self.notes:
            return
        for n in self.notes:
            try:
                n.note_pitch = new_drumkit.index(old_drumkit[n.note_pitch])
            except:
                pass
        self.max_note = len(new_drumkit)

    ### DEBUG ###
    def printNoteList(self):
        for n in self.notes:
            print('on', n.note_on, 'off', n.note_off, 'len', n.note_len, 'pitch', n.note_pitch, 'pan', n.note_pan, 'vel', n.note_vel, 'slide', n.note_slide)

class Note:

    def __init__(self, note_on=0, note_len=1, note_pitch=24, note_pan=0, note_vel=100, note_slide=0, note_aux=0):
        self.note_on = float(note_on)
        self.note_off = float(note_on) + float(note_len)
        self.note_len = float(note_len)
        self.note_pitch = int(note_pitch)
        self.note_pan = int(note_pan)
        self.note_vel = int(note_vel)
        self.note_slide = float(note_slide)
        self.note_aux = float(note_aux)
        self.tagged = False
        # some safety checks TODO

    def __repr__(self):
        return ','.join(str(i) for i in [self.note_on, self.note_off, self.note_pitch])

    def __eq__(self, other):
        return (self.note_on == other.note_on
            and self.note_off == other.note_off
            and self.note_pitch == other.note_pitch
            and self.note_pan == other.note_pan
            and self.note_vel == other.note_vel
            and self.note_slide == other.note_slide
            and self.note_aux == other.note_aux)

    def moveNoteOn(self, to):
        to = max(to, 0)
        self.note_on = to
        self.note_off = to + self.note_len

    def moveNoteOff(self, to):
        self.note_off = to
        self.note_on = to - self.note_len

    def tag(self, tagged = True):
        self.tagged = tagged

    ### PARAMETER GETTERS ###

    def getParameter(self, parameter):
        if parameter == 'pan':
            return self.note_pan
        elif parameter == 'vel':
            return self.note_vel
        elif parameter == 'slide':
            return self.note_slide
        elif parameter == 'aux':
            return self.note_aux
        elif parameter == 'pos':
            return self.note_on
        elif parameter == 'len':
            return self.note_len
        elif parameter == 'pitch':
            return self.note_pitch
        else:
            print("WARNING. TRIED TO GET NONEXISTENT PARAMETER:", parameter)
            return None

    ### PARAMETER SETTERS ###
    def setParameter(self, parameter, value = None, min_value = None, max_value = None):
        if value is not None:
            value = float(value)
            if min_value and value < min_value: value = min_value
            if max_value and value > max_value: value = max_value
        if parameter == 'pan':
            self.setPan(value)
        elif parameter == 'vel':
            self.setVelocity(value)
        elif parameter == 'slide':
            self.setSlide(value)
        elif parameter == 'aux':
            self.setAuxParameter(value)
        elif parameter == 'pos':
            if min_value is None or max_value is None:
                print("WARNING. TRIED TO SET PARAMETER WITHOUT BOUNDARIES:", parameter)
                return
            self.note_on = value
            self.note_off = value + self.note_len
            if self.note_off > max_value:
                self.note_off = max_value
                self.note_len = max_value - value
        elif parameter == 'len':
            if min_value is None or max_value is None:
                print("WARNING. TRIED TO SET PARAMETER WITHOUT BOUNDARIES:", parameter)
                return
            self.note_len = value
            self.note_off = self.note_on + value
            if self.note_off > max_value:
                self.note_off = max_value
                self.note_len = max_value - self.note_on
        elif parameter == 'pitch':
            self.note_pitch = value
        else:
            print("WARNING. TRIED TO SET NONEXISTENT PARAMETER:", parameter)
            return

    def setPan(self, value = None):
        try:
            self.note_pan = min(100, max(-100, int(value)))
        except:
            self.note_pan = 0

    def setVelocity(self, value = None):
        try:
            self.note_vel = min(999, max(0, int(value)))
        except:
            self.note_vel = 100

    def setSlide(self, value = None):
        try:
            self.note_slide = min(96, max(-96, float(value)))
        except:
            self.note_slide = 0

    def setAuxParameter(self, value = None):
        try:
            self.note_aux = min(999, max(-999, float(value)))
        except:
            self.note_aux = 0

################### EN/DECODING FUNCTIONALITY #####################
# have to include some processing for migration between parameters

def encodeTrack(obj):
    if isinstance(obj, Track):
        objDict = {
            'name': obj.name,
            'modules': json.dumps(obj.modules, default = (lambda mod: mod.__dict__)),
            'synthName': obj.synthName,
            'synthType': obj.synthType,
            'volume': obj.volume,
            'mute': obj.mute,
        }
        return objDict
    return super().default(obj)

def decodeTrack(tDict):
    synthName = None
    synthType = None
    if 'synths' in tDict and 'current_synth' in tDict:
        synth = tDict['synths'][tDict['current_synth']]
        synthType = synth[0]
        synthName = synth[2:]
    track = Track(
        name = tDict.get('name', ''),
        synthName = tDict.get('synthName', synthName),
        synthType = tDict.get('synthType', synthType)
    )
    for m in tDict['modules']:
        module = Module(
            mod_on = m.get('mod_on', 0),
            transpose = m.get('transpose', 0)
        )
        if 'pattern' in m:
            module.setPattern(decodePattern(m.get('pattern', None)))
        else:
            module.patternHash = m.get('patternHash', None)
            module.patternName = m.get('patternName', None)
            module.patternLength = m.get('patternLength', None)
        track.modules.append(module)
    track.volume = tDict.get('volume', tDict.get('par_norm', track.volume))
    track.mute = tDict.get('mute', track.mute)
    track.currentModuleIndex = tDict.get('currentModuleIndex', track.currentModuleIndex)
    return track

def encodePattern(obj):
    if isinstance(obj, Pattern):
        objDict = {
            'name': obj.name,
            'length': obj.length,
            'synthType': obj.synthType,
            'max_note': obj.max_note,
            '_hash': obj._hash,
            'notes': json.dumps(obj.notes, default = (lambda note: note.__dict__)),
            'currentNoteIndex': obj.currentNoteIndex,
            'currentGap': obj.currentGap,
        }
        return objDict
    return super().default(obj)

def decodePattern(pDict):
    pattern = Pattern(
        name = pDict.get('name', Pattern().name),
        length = pDict.get('length', Pattern().length),
        synthType = pDict.get('synthType', pDict.get('synth_type', Pattern().synthType)),
        max_note = pDict.get('max_note', Pattern().max_note),
        _hash = pDict.get('_hash', None)
    )
    pattern.notes = [Note(
        note_on = n.get('note_on', Note().note_on),
        note_len = n.get('note_len', Note().note_len),
        note_pitch = n.get('note_pitch', Note().note_pitch),
        note_pan = n.get('note_pan', Note().note_pan),
        note_vel = n.get('note_vel', Note().note_vel),
        note_slide = n.get('note_slide', Note().note_slide),
        note_aux = n.get('note_aux', Note().note_aux)
        ) for n in pDict['notes']]
    pattern.currentNoteIndex = pDict.get('currentNoteIndex', pattern.currentNoteIndex)
    pattern.currentGap = pDict.get('currentGap', pattern.currentGap)
    return pattern
