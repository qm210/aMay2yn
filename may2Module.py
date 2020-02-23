from may2Pattern import NONETYPE


class Module:

    patternHash = None
    patternName = None
    patternLength = None
    patternSynthType = NONETYPE

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
            self.patternSynthType = copyModule.patternSynthType

    def setPattern(self, pattern):
        self.patternHash = pattern._hash
        self.patternName = pattern.name
        self.patternLength = pattern.length
        self.patternSynthType = pattern.synthType

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
