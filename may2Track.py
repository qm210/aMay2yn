from copy import deepcopy

from may2Module import Module
from may2Pattern import SYNTHTYPE, DRUMTYPE, NONETYPE


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
        return f"{self.name}, {self.synthName}, {self.synthType}, {self.modules}, {self.currentModuleIndex}"

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
    def isDrumTrack(self):
        return self.synthType == DRUMTYPE
    def isEmpty(self):
        return self.modules == []

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
        self.modules = [deepcopy(m) for m in track.modules]
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
        else:
            self.ensureOrder()

    def delModule(self):
        if self.modules:
            del self.modules[self.currentModuleIndex if self.currentModuleIndex is not None else -1]
            self.currentModuleIndex = min(self.currentModuleIndex, len(self.modules)-1)
            self.ensureOrder()

    def transposeModule(self, inc):
        if self.modules:
            self.getModule().transpose += inc

    def moveModule(self, inc, move_home = None, move_end = None, total_length = None):
        if self.modules:
            move_to = self.getModuleOn() + inc
            if move_to < 0:
                return
            try_leap = 0

            if inc < 0:
                if self.getModule() != self.getFirstModule():
                    while move_to < self.getModuleOff(try_leap-1):
                        try_leap -=1
                        move_to = self.getModuleOn(try_leap) - self.getModuleLen()
                        if move_to < 0:
                            return
                        if move_to + self.getModuleLen() <= self.getFirstModuleOn():
                            break

            else:
                if self.getModule() != self.getLastModule():
                    while move_to + self.getModuleLen() > self.getModuleOn(try_leap+1):
                        try_leap += 1
                        move_to = self.getModuleOff(try_leap)
                        if move_to >= self.getLastModuleOff():
                            break

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
            if self.getFirstModuleOn() + inc < 0:
                return
        for m in self.modules:
            m.mod_on += inc

    def clearModules(self):
        self.modules=[]

    def setSynth(self, name = None, synthType = None, fullName = None):
        if fullName is not None:
            self.synthType = fullName[0]
            self.synthName = fullName[2:]
        else:
            if synthType is not None:
                self.synthType = synthType
            if name is not None:
                if self.synthType == SYNTHTYPE:
                    self.synthName = name
                elif self.synthType == DRUMTYPE:
                    self.synthName = 'Drums'
                else:
                    self.synthName = 'None'

    def setParameters(self, volume = None, mute = None):
        if volume is not None:
            self.volume = float(volume)
        if mute is not None:
            self.mute = mute

    def untagAllModules(self):
        for m in self.modules:
            m.tagged = False

    def ensureOrder(self):
        if self.modules:
            self.getModule().tag()
            self.modules.sort(key = lambda m: m.mod_on)
            self.currentModuleIndex = self.getFirstTaggedModuleIndex()
            self.untagAllModules()
