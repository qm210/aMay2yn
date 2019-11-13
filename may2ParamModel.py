from PyQt5.QtCore import QAbstractItemModel, Qt, QModelIndex

from May2ynatizer import newlineindent
from may2Utils import GLfloat, GLstr


class Param:

    def __init__(self, form, parent = None):
        self.parent = parent
        self.form = form
        self.segments = []
        self.id = form['id']
        self.default = form.get('default', None)

        self.initSegments()

    def __str__(self):
        return f"{self.id} (default: {self.default})"

    def initSegments(self):
        n_segments = self.form.get('n_segments', None)
        if n_segments is None:
            return
        for n in range(n_segments):
            segment = ParamSegment(self.form['segments'][3*n+1], self.form['segments'][3*n+2])
        return
        # TODO: think about the shit below
        shape = self.form.get('shape', None)

        segment = ParamSegment()
        if shape == 'linear':
            if self.form.get('from', None) is not None and self.form.get('to', None) is not None:
                from_x = float(self.form['from'].split(',')[0])
                from_y = float(self.form['from'].split(',')[1])
                to_x = float(self.form['to'].split(',')[0])
                to_y = float(self.form['to'].split(',')[1])
                segment = ParamSegment(beatFrom = from_x, valueFrom = from_y, beatTo = to_x, valueTo = to_y)
                #form['scale'] = GLfloat(round((to_y-from_y)/(to_x-from_x), 5))
                #form['offset'] = GLfloat(from_x)
                #form['shift'] = GLfloat(from_y)

        elif shape == 'const':
            pass
            # segment = ParamConstSegment()

        elif shape == 'literal':
            pass
            # segment = ParamLiteralSegment()


    def addSegment(self, item):
        self.segments.append(item)

    def getForm(self, row):
        try:
            return self.form[row]
        except IndexError:
            return None

    def getSegmentList(self):
        return [segment.id for segment in self.segments]

class ParamSegment:

    LINEAR, CONST, LITERAL = ['linear', 'const', 'literal']

    def __init__(self, id = None, beatFrom = None, beatTo = None, **kwargs):
        self.id = id
        self.beatFrom = beatFrom
        self.beatTo = beatTo
        self.type = None
        self.args = {**kwargs}

    def __str__(self):
        if self.type == ParamSegment.LINEAR:
            return f"[{self.beatFrom}..{self.beatTo}] linear: {self.args['valueFrom']} -> {self.args['valueTo']}"
        elif self.type == ParamSegment.CONST:
            return f"[{self.beatFrom}..{self.beatTo}] const: {self.args['value']}"
        elif self.type == ParamSegment.LITERAL:
            return f"[{self.beatFrom}..{self.beatTo}] \"{self.args['value']}\""
        else:
            return f"[{self.beatFrom or '?'}..{self.beatTo or '?'}] unknown segment"

    def setArgs(self, type, **kwargs):
        self.type = type
        self.args.update(kwargs)
