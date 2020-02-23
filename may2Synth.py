from copy import deepcopy

from may2Utils import inQuotes, isNumber, collectValuesRecursively
from may2Pattern import SYNTHTYPE


class Synth:

    def __init__(self, name):
        self.name = name
        self.type = SYNTHTYPE
        self.amaysynL = ''
        self.amaysynR = ''
        self.args = {}
        self.overwrites = {}
        self.mainSrc = None
        # TODO: allow for mainSrcR (e.g. allow for a list of two, then also two nodeTrees, or one with two sources? don't know yet.)
        self.nodeTree = SynthRoot(ID = name)
        self.usedParams = self.nodeTree.usedParams
        self.usedRandoms = self.nodeTree.usedRandoms

    def __repr__(self):
        return f"{self.__dict__}"

    def usesAnyRandoms(self):
        return len(self.usedRandoms) > 0

    def usedRandomIDs(self):
        return [rnd for rnd in self.usedRandoms]

    def usesAnyParams(self):
        return len(self.usedParams) > 0

    def usedParamIDs(self):
        return [param for param in self.usedParams]

    def parseNodeTreeFromSrc(self, mainSrc, formList, verbose = False):
        if mainSrc is not None:
            self.mainSrc = mainSrc
        self.nodeTree.verbose = verbose
        self.nodeTree.parse(formList, self.mainSrc)
        self.nodeTree.parseExtra(self.args, 'shape')

    def resetNodeTree(self):
        self.nodeTree = SynthRoot(ID = self.name)
        self.usedParams = self.nodeTree.usedParams
        self.usedRandoms = self.nodeTree.usedRandoms

    def printNodeTree(self):
        self.nodeTree.printWhole()
        for error in self.nodeTree.errorStack:
            print(error)

    def isEmpty(self):
        return not self.mainSrc

    def isUnparsed(self):
        return self.nodeTree.src is None


class SynthRoot:

    def __init__(self, ID):
        self.id = ID
        self.usedParams = {}
        self.usedRandoms = {}
        self.formList = []
        self.formIDs = {}
        self.countSubID = 0
        self.src = None
        self.extraNodes = set()
        self.verbose = False
        self.errorStack = []

    def __repr__(self):
        return f"{self.src}"

    def setFormList(self, formList):
        self.formList = formList
        self.formIDs = {form['id'] for form in formList}

    def parse(self, formList, mainSrc):
        self.countSubID = 0
        if formList is not None:
            self.setFormList(formList)
        if self.formList is None:
            print("ERROR! tried to parse nodeTree without given formList!")
            raise ValueError
        self.src = SynthNode(root = self, ID = self.id)
        self.src.parse('src', mainSrc)

    def parseExtra(self, extraDict, extraKey):
        if not isinstance(extraDict, dict) or extraDict.get(extraKey) is None:
            return
        for extraID in collectValuesRecursively(extraDict.get(extraKey)):
            extraNode = SynthNode(root = self, ID = extraID)
            extraNode.parse(extraID, extraID)

    def newSubID(self):
        newSubID = f'{self.id}__{self.countSubID}'
        if newSubID in self.formIDs:
            print("ERROR! DO NOT USE __ IN ANY FORM ID; THIS ONE NOW COLLIDES:", newSubID)
            raise ValueError
        self.countSubID += 1
        return newSubID

    def printWhole(self):
        print(f"\nNODE TREE {self.id}:")
        for node in self.src.subNodes:
            self.src.subNodes[node].printNested()


class SynthNode:

    SUM, PRODUCT, CONST, LITERAL, UNIFORM = ('sum', 'product', 'const', 'literal', 'uniform')

    def __init__(self, root, ID = None):
        self.root = root
        self.id = ID or self.root.newSubID()
        self.type = None
        self.subNodes = {}
        self.value = None

    def __repr__(self):
        if self.isLeaf():
            return f"{self.value}"
        else:
            subNodeList = '(' + ','.join([f"{key}:{self.subNodes[key]}" for key in self.subNodes]) + ')' if self.subNodes else ''
            return f"{self.id}{subNodeList}"

    def printNested(self, oldPrefix = ''):
        if self.isLeaf():
            print(self.id, '=', self.value)
        else:
            print('\n' + oldPrefix, 'id:', self.id, 'type:', self.type, 'value:', self.value)
        subNodeCount = 0
        for node in self.subNodes:
            prefix = oldPrefix + ('  └─ ' if subNodeCount == len(self.subNodes) - 1 else '  ├─ ')
            print(prefix, end = '')
            self.subNodes[node].printNested(oldPrefix + '    ' if subNodeCount == len(self.subNodes) - 1 else '  │ ')
            subNodeCount += 1

    #pylint: disable=redefined-builtin
    def setType(self, type):
        if self.type is not None:
            print(f"ERROR! TYPE ALREADY SET! in{self.root.id}: {self.id} is {self.type}, not {type}")
            raise TypeError
        self.type = type

    def parse(self, argKey, argSource):
        if self.root.verbose:
            print("PARSE NOW: ID", self.id, "KEY", argKey, '=', argSource)

        if not isinstance(argSource, str):
            self.setType(SynthNode.CONST)
            return

        if inQuotes(argSource):
            self.setType(self.LITERAL)
            return

        if '+' in argSource and argKey == 'src': # TODO: do not do this argKey == 'src' shit
            self.setType(SynthNode.SUM)
            for term in argSource.split('+'): #TODO: is it hard to switch the ',' to '+' now?
                subID = f"{self.id}__{term}" if term in self.root.formIDs else None
                subNode = SynthNode(root = self.root, ID = subID)
                subNode.parse('src', term)
                self.subNodes.update({subNode.id: subNode})
            return

        if '*' in argSource:
            self.setType(SynthNode.PRODUCT)
            for term in argSource.split('*'):
                subID = f"{self.id}__{term}" if term in self.root.formIDs else None
                subNode = SynthNode(root = self.root, ID = subID)
                subNode.parse('src', term)
                self.subNodes.update({subNode.id: subNode})
            return

        form = next((form for form in self.root.formList if form['id'] == argSource), None)

        if form is None:
            if not isNumber(argSource):
                self.root.errorStack.append(f"ERROR! in {self.root.id} / {self.id}: undefined term? {argKey} = {argSource}")
            self.setType(SynthNode.CONST)
            return

        subID = form.get('id', None)
        if self.root.verbose:
            print("VERBOSE: ", subID, form)
        subNode = SynthNode(root = self.root, ID = subID)
        subNode.parseForm(form)
        self.subNodes.update({argKey: subNode})


    def parseForm(self, form):
        for key in form:
            if key == 'id':
                pass
            elif key == 'type':
                self.setType(form[key])
            elif key in ['op', 'shape']:
                self.value = form[key]
            else:
                subNode = SynthNode(root = self.root, ID = f"{self.id}__{key}")
                if self.root.verbose:
                    print(f"PARSE NOW {self.id} -- FORM[{key}] = {form[key]} in {form}")
                subNode.parse(key, form[key])
                self.subNodes[key] = subNode

        self.assignValue(form)


    def isLeaf(self):
        return self.type in [SynthNode.CONST, SynthNode.LITERAL, SynthNode.UNIFORM]

    def assignValue(self, form):
        if self.type == 'uniform':
            self.value = form['id'] # todo: redundant
        elif self.type == 'const':
            self.value = form['value']
        elif self.type == 'random':
            self.value = deepcopy(form)
            self.root.usedRandoms.update({self.id: self.value})
        elif self.type in ['param']:
            self.value = deepcopy(form) # wtf what to do with this!?? and how to treat includes? BIGTODO
            self.root.usedParams.update({self.id: self.value})
        elif self.value is not None and 'src' in form:
            self.value = form['src']
