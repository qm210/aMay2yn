from PyQt5.QtCore import Qt, QRectF
from math import floor

quantize = lambda x, q: floor(x/q)*q

def drawText(qp, x, y, flags, text):
    size = 2**15 - 1
    y -= size
    if flags & Qt.AlignHCenter:
        x -= 0.5 * size
    elif flags & Qt.AlignRight:
        x -= size
    if flags & Qt.AlignVCenter:
        y += 0.5 * size
    elif flags & Qt.AlignTop:
        y += size
    else:
        flags |= Qt.AlignBottom
    rect = QRectF(x, y, size, size)
    qp.drawText(rect, flags, text)

def drawTextDoubleInX(qp, x, y, flags, text, offset):
    drawText(qp, x + offset, y, flags, text)
    drawText(qp, x, y, flags, text)

def drawTextDoubleInY(qp, x, y, flags, text, offset):
    drawText(qp, x, y, flags, text)
    drawText(qp, x, y - offset, flags, text)
