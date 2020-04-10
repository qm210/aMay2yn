from copy import deepcopy


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

    def __repr__(self):
        repr_str = ','.join(str(i) for i in [self.note_on, self.note_off, self.note_pitch])
        if self.tagged:
            repr_str += ',TAG'
        return repr_str

    def __eq__(self, other):
        return (self.note_on == other.note_on
                and self.note_off == other.note_off
                and self.note_pitch == other.note_pitch
                and self.note_pan == other.note_pan
                and self.note_vel == other.note_vel
                and self.note_slide == other.note_slide
                and self.note_aux == other.note_aux)

    def __add__(self, other):
        newNote = deepcopy(self)
        if isinstance(other, int):
            newNote.note_pitch += other
        elif isinstance(other, Note):
            newNote.note_pitch += other.note_pitch
        else:
            raise TypeError(f"Tried to add Note + {other.__class__.__name__}, not defined.")
        return newNote

    def moveNoteOn(self, to):
        to = max(to, 0)
        self.note_on = to
        self.note_off = to + self.note_len

    def moveNoteOff(self, to):
        self.note_off = to
        self.note_on = to - self.note_len

    def cropNoteOff(self, to):
        self.note_off = to
        self.note_len = self.note_off - self.note_on

    def stretchNoteLen(self, length):
        self.note_len = length
        self.note_off = self.note_on + self.note_len

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
            if min_value is not None and value < min_value:
                value = min_value
            if max_value is not None and value > max_value:
                value = max_value
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

    def setPan(self, value = 0):
        self.note_pan = min(100, max(-100, int(value)))

    def setVelocity(self, value = 100):
        self.note_vel = min(999, max(0, int(value)))

    def setSlide(self, value = 0):
        self.note_slide = min(96, max(-96, float(value)))

    def setAuxParameter(self, value = 0):
        self.note_aux = min(999, max(-999, float(value)))
