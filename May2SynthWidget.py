from PyQt5.QtWidgets import QWidget

from may2Synth import Synth


class May2SynthWidget(QWidget):

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.synth = None

    def getSynthName(self):
        return self.synth.name if self.synth is not None else None

    def setSynth(self, synth):
        self.synth = synth
        print(f"WOAH! LOADED: {self.synth.name} {self.synth.usedRandomIDs()} {self.synth.usedParamIDs()}")