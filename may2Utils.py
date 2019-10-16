from PyQt5.QtCore import Qt, QRectF

def drawText(self, qp, x, y, flags, text):
    size = 32767
    y -= size
    if flags & Qt.AlignHCenter:
        x -= 0.5*size
    elif flags & Qt.AlignRight:
        x -= size
    if flags & Qt.AlignVCenter:
        y += 0.5*size
    elif flags & Qt.AlignTop:
        y += size
    else:
        flags |= Qt.AlignBottom
    rect = QtCore.QRectF(x, y, size, size)
    qp.drawText(rect, flags, text)

