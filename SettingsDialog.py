from PyQt5 import QtWidgets, QtCore


class SettingsDialog(QtWidgets.QDialog):

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)