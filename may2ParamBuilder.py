from may2Param import Param, ParamSegment
from may2Utils import GLfloat, GLstr, newlineindent


def buildParamFunction(param):

    if not isinstance(param, Param):
        raise TypeError(f"Called buildParamFunction() with some argument of type {type(param)}; needs to be Param")

    paramCode = f"float {param.id}(float B)\n{{{newlineindent}return B<0 ? 0. : "

    for segment in param.segments:

        if segment.type == ParamSegment.CONST:
            segmentCode = GLfloat(segment.args['value'])

        elif segment.type == ParamSegment.LITERAL:
            segmentCode = GLstr(segment.args['value'])

        elif segment.type == ParamSegment.LINEAR:
            linCoeffA = GLfloat(round(1/segment.beatLen(), 4))
            linCoeffB = GLfloat(round(-segment.beatTo/segment.beatLen(), 4))
            segmentCode = f"linmix(B, {linCoeffA}, {linCoeffB}, {segment.args['valueFrom']}, {segment.args['valueTo']})"

        paramCode += f"(B>={GLfloat(segment.beatFrom)} && B<{GLfloat(segment.beatTo)}) ? {segmentCode} : "

    paramCode += f"{GLfloat(param.default)};\n}}\n"

    return paramCode
