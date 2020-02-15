#!/usr/bin/python3
#
# this script, for now, is standalone
# but might get integrated for "soft cloning" in some time (read: probably never)
# - qm210


import re


class RandomTemplateFixer:

    separators = r' =()*+-'

    def __init__(self, template):
        self.template = template.replace('\t', '') + ' '
        self.fixedDrumName = None
        self.fixedMainName = None

    def fix(self, rndString, newMainName):
        rndDict = self.parseRndString(rndString)
        if rndDict is None:
            return None
        return self.fixedString(rndDict, newMainName)

    @staticmethod
    def parseRndString(rndString):
        rndArray = rndString.replace('\t', ' ').split()
        rndDict = {s.split('=')[0]:s.split('=')[1] for s in rndArray[3:]}
        rndDict.update({'id': rndArray[2]})
        return rndDict

    def fixedString(self, rndDict, newMainName):
        fixedTemplate = self.template
        for key in rndDict:
            regExPtrn = fr'(?<=[{self.separators}]){key}(?=[{self.separators}])'
            regExSubst = f'{rndDict[key]}'
            fixedTemplate = re.sub(regExPtrn, regExSubst, fixedTemplate)

        oldSrcName = template.split()[1]
        self.fixedDrumName = newMainName + 'src'
        fixedTemplate = re.sub(f'(?<= ){oldSrcName}(?= )',f' {self.fixedDrumName} ', fixedTemplate)
#        fixedTemplate += f'\nmaindrum {newMainName} src={self.fixedDrumName} release=.01\n'

        return fixedTemplate


if __name__ == '__main__':
    template = """
env fqmbace200_env shape=ahdsrexp attack=qmattack decay=0.01 sustain=1 release=qmrelease
osc    QFManiaA shape=fm freq=f lv1=qlev1 lv2=qlev2 lv3=qlev3 lv4=qlev4 fr1=.5 fr3=1.001 fb1=qfbk1 fb2=qfbk2 fb3=qfbk3 fb4=qfbk4 algo=qalg0 parscale=127
lfo    QFManiaLFO shape=sin freq=.4 scale=.5 shift=.5 mode=global
form   QFManiaB waveshape src=QFManiaA amount=QFManiaLFO a=.05 b=.46 c=.3 d=.7 e=.8
osc    QFManiaC shape=fm freq=f lv1=qlev1 lv2=qlev2 lv3=qlev3 lv4=qlev4 fr1=.5 fr3=1.001 fb1=qfbk1 fb2=qfbk2 fb3=qfbk3 fb4=qfbk4 algo=qalg0 parscale=127
form   QFManiaD quantize src=QFManiaC bits=8000
form   QFManiaE op=chorus src=QFManiaD number=2 step=.002 intensity=5. rate=5.5
main   FQMbace  src=vel*QFManiaC*macebace_env release=.2 slidetime=.6
"""    
    rndString = """
    20/02/15 00:13	001	shp1=0.09	shp2=1.71	maddcut=79.31	maddcutq=3.66	maddres=3.36	maddresq=8.82	maddpw=0.1	maddmix=0.63	madddet=0.01	chpattack=0.045	chpdecay=0.182	chpsustain=0.954	chprelease=0.024	chplfoscale=501.0	chplfoshift=1955.0	chpndecay=25.0	chpres=0.0	chpresq=14.54	chpdetune=0.013	chpshape=0.78	strchlfofreq=0.883	strchlfoscale=879.0	strchlfoshift=5156.0	strchlfood=0.251	strchndecay=7.727	strchres=1.027	strchresq=8.63	strchpm=-0.68	strchdetune=0.026	strchattack=0.458	strchrelease=0.49	strchshape=-0.136	afreq0=243.0	afreq1=58.0	afreqdecay=0.02	aattack=0.004	adecay=0.18	adrive=1.07	arev1_amt=0.41	arev1_tone=4041.0	arev1_exp=20.51	arev1_drive=0.28	arev2_amt=0.42	arev2_tone=2334.0	arev2_exp=17.64	arev3_amt=0.51	arev3_tone=3759.0	arev3_exp=25.86	anoise_amt=0.09	anoise_hold=0.34	anoise_decay=0.46	anoise_tone=17099.0	shkamp=13.58	shktimbre=4.89	shkdecay=0.015	shkrelease=0.013	qmattack=0.024	qmrelease=0.006	qmlfoscale=446.0	qmlfoshift=1355.0	qmndecay=9.0	qmres=2.28	qmresq=1.1	qmdetune=0.011	qlev1=126.0	qlev2=19.0	qlev3=107.0	qlev4=80.0	qalg0=3.0	qfbk1=69.0	qfbk2=9.0	qfbk3=37.0	qfbk4=118.0	qatt0=0.022	qhld0=0.073	qdec0=0.09	qsus0=0.821	qrel0=0.178	qlfo1frq=0.113	qlfo2frq=0.817	qlfo3frq=0.355	qlfo4frq=0.17	qlfo5frq=0.166	qlfo1amt=0.492	qlfo2amt=0.192	qlfo3amt=0.055	qlfo4amt=0.336
"""
    newMainName = "fqmbace200"
    templateFixer = RandomTemplateFixer(template)
    output = templateFixer.fix(rndString, newMainName)
    print(template, '\n', output, '\nYou need to fix all the IDs yourself!!\n')
