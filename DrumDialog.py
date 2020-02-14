from PyQt5 import QtWidgets, QtCore
from random import randint


class DrumDialog(QtWidgets.QDialog):

    WIDTH = 400
    HEIGHT = 600

    def __init__(self, parent, track = None, *args, **kwargs):
        super(DrumDialog, self).__init__(parent, *args, **kwargs)
        self.setWindowTitle('Drum Dialog')
        self.setGeometry(parent.x() + 0.5 * (parent.width() - self.WIDTH), parent.y() + 0.5 * (parent.height() - self.HEIGHT), self.WIDTH, self.HEIGHT)
        self.parent = parent
        self.track = track

        self.layout = QtWidgets.QVBoxLayout()

        self.nameLayout = QtWidgets.QHBoxLayout()
        self.nameEdit = QtWidgets.QLineEdit(self)
        self.nameEdit.setPlaceholderText('Drum Name')
        self.renameButton = QtWidgets.QPushButton('rename',self)
        self.nameLayout.addWidget(self.nameEdit, 4)
        self.nameLayout.addWidget(self.renameButton, 1)
        self.layout.addLayout(self.nameLayout)

        self.buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Reset | QtWidgets.QDialogButtonBox.Cancel, self)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.clicked.connect(self.clickOther)
        self.buttonBox.rejected.connect(self.reject)

        self.layout.addWidget(QtWidgets.QLabel('Drum Instruments:', self))

        self.drumList = QtWidgets.QListView(self)
        self.drumList.setModel(self.parent.drumModel)
        self.layout.addWidget(self.drumList)

        self.buttonGrid = QtWidgets.QGridLayout()

        self.randomDrumButton = QtWidgets.QPushButton('Random Drum', self)
        self.buttonGrid.addWidget(self.randomDrumButton, 0, 0)

        self.randomizeParametersButton = QtWidgets.QPushButton('Randomize Parameters!', self)
        self.buttonGrid.addWidget(self.randomizeParametersButton, 0, 1)

        self.previewModuleButton = QtWidgets.QPushButton('Preview Module', self)
        self.previewModuleButton.setEnabled(track is not None and not track.isEmpty())
        self.buttonGrid.addWidget(self.previewModuleButton, 1, 1)

        self.hardCopyDrumButton = QtWidgets.QPushButton('HardCopy Drum', self)
        self.buttonGrid.addWidget(self.hardCopyDrumButton, 1, 0)

        self.layout.addLayout(self.buttonGrid)

        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)

        self.randomDrumButton.clicked.connect(self.selectRandomDrum)
        self.randomizeParametersButton.clicked.connect(self.randomizeDrumParameters)
        self.previewModuleButton.clicked.connect(self.parent.renderModule)
        #self.hardCopyDrumButton.clicked.connect(self.parent.hardCopyDrum)

        # LAYOUT:
        # Button: Randomize Parameters
        # HARD COPY DRUM
        # HIDE DRUM (keep information separate)
        # PREVIEW DRUM:
        ### preview with volume ...
        ### preview with aux ...
        # --> preview-drum-mode (or include 'vel' and 'aux' in Drumatizer, somehow...)
        # TODO: drum list should tell us which drums contain random values...

        self.init()

    def init(self):
        self.nameEdit.setText(self.track.drumName)
        drumIndex = self.parent.drumModel.stringList().index(self.track.drumName)
        self.selectDrum(drumIndex)

    def drumName(self):
        index = self.drumList.selectedIndexes()[0].row()
        return self.parent.drumModel.stringList()[index]

    def selectDrum(self, index):
        self.drumList.setCurrentIndex(self.parent.drumModel.createIndex(index, 0))

    def selectRandomDrum(self):
        self.selectDrum(randint(1, self.parent.drumModel.rowCount() - 1))

    def clickOther(self, button):
        if button == self.buttonBox.button(QtWidgets.QDialogButtonBox.Reset):
            self.init()

    def randomizeDrumParameters(self):
        self.parent.randomizeSynatizer()