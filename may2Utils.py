from PyQt5.QtCore import Qt, QRectF
from math import floor

quantize = lambda x, q: floor(x/q)*q

GLfloat = lambda f: str(int(f)) + '.' if f==int(f) else str(f)[0 if f>=1 or f<0 or abs(f)<1e-4 else 1:].replace('-0.','-.')

inquotes = lambda f: len(f) > 2 and f[0] == '"' and f[-1] == '"'
split_if_not_quoted = lambda string, delimiter: string.split(delimiter) if not inquotes(string) else [string]

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

def GLstr(s):
    try:
        f = float(s)
    except ValueError:
        return s
    else:
        return GLfloat(f)
