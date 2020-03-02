
class Param:

    def __init__(self, form, ID = None, default = None):
        self.form = form
        self.segments = []
        self.id = ID or form['id']
        self.default = default or float(form.get('default', 0))
        self.syncWithModule = ('module' in form['mode']) # think about how to implement this in a flexible way. for now: just add mode=module in the .syn file

        self.initSegments()

    def __str__(self):
        label = f"{self.id} (default: {self.default})"
        if self.syncWithModule:
            label += ' (mod sync)'
        return label

    def initSegments(self): # TODO: implement this # Ok, I forgot what I planned to do with this
        pass


    def addSegment(self, item):
        if item is not None:
            self.segments.append(item)
            self.segments.sort(key = lambda segment: segment.start)

    def updateSegment(self, oldSegment, newSegment):
        try:
            oldSegmentIndex = self.segments.index(oldSegment)
        except ValueError:
            print("Tried to updateSegment(), but did not find", oldSegment, "in this parameter. Add instead.")
            self.addSegment(newSegment)
            return
        if newSegment is not None:
            self.segments[oldSegmentIndex] = newSegment
            self.segments.sort(key = lambda segment: segment.start)
        else:
            self.segments.remove(oldSegment)

    def getForm(self, row):
        try:
            return self.form[row]
        except IndexError:
            return None

    def getSegmentList(self):
        return [segment.id for segment in self.segments]

    def getSegmentAtIndex(self, index):
        return self.segments[index] if index is not None else None

    def hasCollidingSegments(self):
        for seg, nextSeg in zip(self.segments, self.segments[1:]):
            if seg.end > nextSeg.start:
                return True
        return False

    def getLastSegmentEnd(self):
        return self.segments[-1].end if self.segments else 0

    def shiftBy(self, offset):
        for segment in self.segments:
            segment.start += offset
            segment.end += offset

class ParamSegment:

    LINEAR, CONST, LITERAL = ['linear', 'const', 'literal']

    def __init__(self, ID = None, start = None, end = None, segmentType = None, **kwargs):
        self.id = ID
        self.start = start
        self.end = end
        self.segmentType = segmentType
        self.args = {**kwargs}

    def __str__(self):
        if self.segmentType == ParamSegment.LINEAR:
            return f"[{self.start}..{self.end}] linear: {self.args['startValue']} -> {self.args['endValue']}"
        elif self.segmentType == ParamSegment.CONST:
            return f"[{self.start}..{self.end}] const: {self.args['value']}"
        elif self.segmentType == ParamSegment.LITERAL:
            return f"[{self.start}..{self.end}] \"{self.args['value']}\""
        else:
            return f"[{self.start or '?'}..{self.end or '?'}] unknown segment"

    def setArgs(self, segmentType, **kwargs):
        self.segmentType = segmentType
        self.args.update(kwargs)
        if self.segmentType != ParamSegment.LITERAL:
            for arg in self.args:
                print(self.segmentType, self.args, self.args[arg])
                self.args[arg] = round(self.args[arg], 3)

    def length(self):
        return self.end - self.start
