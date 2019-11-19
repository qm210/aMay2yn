from random import uniform
from copy import deepcopy


class RandomValue:

    idColumn, valueColumn, minColumn, maxColumn, digitsColumn, fixedColumn = range(6)

    def __init__(self, form, id = None, value = None, fixed = False):
        self.form = form
        self.id = id or form['id']
        self.min = float(form['min'])
        self.max = float(form['max'])
        self.value = value or form['value']
        self.digits = int(form['digits'])
        self.mode = form['mode']
        self.fixed = fixed
        self.storedValues = {}

    def __str__(self):
        label = f"{self.id} = {self.value:.{self.digits}f} [{self.min}..{self.max}]"
        if self.fixed:
            label += ' [FIXED]'
        return label

    def reshuffle(self):
        if not self.fixed:
            self.value = round(uniform(self.min, self.max), self.digits)

    def setFromStore(self, key):
        self.value = self.storedValues[key]

    def store(self, key):
        self.storedValues[key] = self.value

    def getRow(self):
        return [self.id, self.value, self.min, self.max, self.digits, self.fixed]

    def getUpdatedForm(self):
        newForm = deepcopy(self.form)
        newForm.update({
            'value': self.value,
            'min': self.min,
            'max': self.max,
            'digits': self.digits,
        })
        return newForm