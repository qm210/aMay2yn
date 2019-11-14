from PyQt5.QtCore import Qt, QRectF
from math import floor
from re import match

quantize = lambda x, q: floor(x/q)*q

GLfloat = lambda f: str(int(f)) + '.' if f==int(f) else str(f)[0 if f>=1 or f<0 or abs(f)<1e-4 else 1:].replace('-0.','-.')
strfloat = lambda f: str(int(f)) if f==int(f) else str(f)
newlineindent = '\n' + 4*' '
newlineplus = '\n' + 6*' ' + '+'
inQuotes = lambda f: len(f) > 2 and f[0] == '"' and f[-1] == '"'

split_if_not_quoted = lambda string, delimiter: string.split(delimiter) if not inQuotes(string) else [string]

mixcolor = lambda t1,t2: tuple((v1+v2)/2 for v1,v2 in zip(t1,t2))

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

def isNumber(string):
    regex = match(r'[+-]?[\d]*[\.]?[\d]*([eE][+-]?[\d]+)?', string).group()
    return (regex == string)

def findFreeSerial(serialPrefix, takenSerials = []):
    count = 0
    while True:
        newSubID = f'{serialPrefix}{count}'
        if newSubID not in takenSerials:
            return newSubID
        count += 1
        if count > 999:
            print(f"findFreeSerial() tries {newSubID}...")
