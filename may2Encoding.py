from copy import copy, deepcopy
from numpy import clip
import random
import json

from may2Objects import * #pylint: disable=unused-wildcard-import
from may2Synth import * #pylint: disable=unused-wildcard-import


################### EN/DECODING FUNCTIONALITY #####################
# have to include some processing for migration between parameters

def encodeTrack(obj):
    if isinstance(obj, Track):
        objDict = {
            'name': obj.name,
            'modules': json.dumps(obj.modules, default = (lambda mod: mod.__dict__)),
            'synthName': obj.synthName,
            'synthType': obj.synthType,
            'volume': obj.volume,
            'mute': obj.mute,
        }
        return objDict
    return TypeError(f"encodeTrack can't encode {obj.__class__.__name__}")

def decodeTrack(tDict):
    synthName = None
    synthType = None
    if 'synths' in tDict and 'current_synth' in tDict:
        synth = tDict['synths'][tDict['current_synth']]
        synthType = synth[0]
        synthName = synth[2:]
    track = Track(
        name = tDict.get('name', ''),
        synthName = tDict.get('synthName', synthName),
        synthType = tDict.get('synthType', synthType)
    )
    for m in tDict['modules']:
        module = Module(
            mod_on = m.get('mod_on', 0),
            transpose = m.get('transpose', 0)
        )
        if 'pattern' in m:
            module.setPattern(decodePattern(m.get('pattern', None)))
        else:
            module.patternHash = m.get('patternHash', None)
            module.patternName = m.get('patternName', None)
            module.patternLength = m.get('patternLength', None)
        track.modules.append(module)
    track.volume = tDict.get('volume', tDict.get('par_norm', track.volume))
    track.mute = tDict.get('mute', track.mute)
    track.currentModuleIndex = tDict.get('currentModuleIndex', track.currentModuleIndex)
    return track

#########################################################

def encodePattern(obj):
    if isinstance(obj, Pattern):
        objDict = {
            'name': obj.name,
            'length': obj.length,
            'synthType': obj.synthType,
            'max_note': obj.max_note,
            '_hash': obj._hash,
            'notes': json.dumps(obj.notes, default = (lambda note: note.__dict__)),
            'currentNoteIndex': obj.currentNoteIndex,
            'currentGap': obj.currentGap,
        }
        return objDict
    return TypeError(f"encodePattern can't encode {obj.__class__.__name__}")

def decodePattern(pDict):
    pattern = Pattern(
        name = pDict.get('name', Pattern().name),
        length = pDict.get('length', Pattern().length),
        synthType = pDict.get('synthType', pDict.get('synth_type', Pattern().synthType)),
        max_note = pDict.get('max_note', Pattern().max_note),
        _hash = pDict.get('_hash', None)
    )
    pattern.notes = [Note(
        note_on = n.get('note_on', Note().note_on),
        note_len = n.get('note_len', Note().note_len),
        note_pitch = n.get('note_pitch', Note().note_pitch),
        note_pan = n.get('note_pan', Note().note_pan),
        note_vel = n.get('note_vel', Note().note_vel),
        note_slide = n.get('note_slide', Note().note_slide),
        note_aux = n.get('note_aux', Note().note_aux)
        ) for n in pDict['notes']]
    pattern.currentNoteIndex = pDict.get('currentNoteIndex', pattern.currentNoteIndex)
    pattern.currentGap = pDict.get('currentGap', pattern.currentGap)
    return pattern

#########################################################

def encodeSynth(obj):
    if isinstance(obj, Synth):
        nodeTreeDict = {
            'usedParams': obj.nodeTree.usedParams,
            'usedRandoms': obj.nodeTree.usedRandoms,
            'formList': obj.nodeTree.formList,
            'src': json.dumps(obj.nodeTree.src, cls = SynthNodeEncoder)
        }
        objDict = {
            'name': obj.name,
            'type': obj.type,
            'amaysynL': obj.amaysynL,
            'amaysynR': obj.amaysynR,
            'args': obj.args,
            'nodeTree': nodeTreeDict,
            'overwrites': obj.overwrites,
            'mainSrc': obj.mainSrc
        }
        return objDict
    raise TypeError(f"encodeSynth can't encode {obj.__class__.__name__}")

def decodeSynth(sDict):
    if isinstance(sDict, str):
        if sDict[0:2] == f"{SYNTHTYPE}_":
            return Synth(name = sDict[2:])
        else:
            return Synth(name = sDict)
    else:
        synth = Synth(name = sDict['name'])
        synth.type = sDict.get('type', synth.type)
        synth.amaysynL = sDict.get('amaysynL', '')
        synth.amaysynR = sDict.get('amaysynR', '')
        synth.args = sDict.get('args', {})
        synth.overwrites = sDict.get('overwrites', {})
        synth.mainSrc = sDict.get('mainSrc', None)
        nDict = sDict['nodeTree']
        synth.nodeTree.usedParams = nDict.get('usedParams', {})
        synth.nodeTree.usedRandoms = nDict.get('usedRandoms', {})
        synth.nodeTree.setFormList(nDict.get('formList', []))
        synth.nodeTree.src = json.loads(nDict['src'], cls = SynthNodeDecoder(root = synth.nodeTree))
        return synth

class SynthNodeEncoder(json.JSONEncoder):

    #pylint: disable=method-hidden
    def default(self, obj):
        if isinstance(obj, SynthNode):
            return {
                'id': obj.id,
                'type': obj.type,
                'value': obj.value,
                'subNodes': json.dumps(obj.subNodes, cls = SynthNodeEncoder)
            }
        else:
            raise TypeError(f"SynthNodeEncoder can't encode {obj.__class__.__name__}")

class SynthNodeDecoder(json.JSONDecoder):

    def __init__(self, root, *args, **kwargs):
        super().__init__(self, object_hook = self.object_hook, *args, **kwargs)
        self.root = root

    #pylint: disable=method-hidden
    def object_hook(self, objDict):
        node = SynthNode(root = self.root, id = objDict['id'])
        node.type = objDict['type']
        node.value = objDict['value']
        node.subNodes = json.loads(objDict['subNodes'], cls = SynthNodeDecoder(root = self.root))
        return node

#########################################################

def encodeUndoObject(obj):
    if isinstance(obj, Track):
        return encodeTrack(obj)
    elif isinstance(obj, Pattern):
        return encodePattern(obj)
    elif isinstance(obj, Synth):
        return encodeSynth(obj)
    else:
        return json.dumps(obj)

def decodeUndoObject(oDict):
    obj = {
        'state': json.loads(oDict['state']),
        'info': json.loads(oDict['info']),
        'drumkit': json.loads(oDict['drumkit'])
    }
    obj['tracks'] = json.loads(oDict['tracks'], object_hook = decodeTrack)
    obj['patterns'] = json.loads(oDict['patterns'], object_hook = decodePattern)
    obj['synths'] = json.loads(oDict['synths'], object_hook = decodeSynth)
    return obj