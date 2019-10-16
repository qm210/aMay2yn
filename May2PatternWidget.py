from PyQt5 import QtGui
from PyQt5.QtWidgets import QWidget

from may2Models import * # pylint: disable=unused-import
from may2Utils import drawText
import may2Style


class May2PatternWidget(QWidget):

    def __init__(self, parent):
        super().__init__()
        self.parent = parent

    def paintEvent(self, event):
        self.qrect = event.rect()
        rectX = self.qrect.left()
        rectY = self.qrect.top()
        rectW = self.qrect.width()
        rectH = self.qrect.height()

        BGCOLOR = QtGui.QColor(*may2Style.group_bgcolor)

        qp = QtGui.QPainter()
        qp.begin(self)

        qp.fillRect(rectX, rectY, rectW, rectH, BGCOLOR)

        qp.end()


    def mousePressEvent(self, event):
        pass

    def mouseMoveEvent(self, event):
        pass

    def mouseReleaseEvent(self, event):
        pass