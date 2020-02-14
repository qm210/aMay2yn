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
            print('fix', key, rndDict[key], f"|{regExPtrn}|{regExSubst}|")
            fixedTemplate = re.sub(regExPtrn, regExSubst, fixedTemplate)
        print(template, '\n', fixedTemplate)

        oldSrcName = template.split()[1]
        self.fixedDrumName = newMainName + 'src'
        fixedTemplate = re.sub(f'(?<= ){oldSrcName}(?= )',f' {self.fixedDrumName} ', fixedTemplate)
        fixedTemplate += f'\nmaindrum {newMainName} src={self.fixedDrumName} release=.01\n'

        return fixedTemplate


if __name__ == '__main__':
    template = "drum protkickass shape=protokickass freq0=afreq0 freq1=afreq1 freqdecay=afreqdecay attack=aattack decay=adecay drive=adrive rev1_amt=arev1_amt rev2_amt=arev2_amt rev3_amt=arev3_amt rev1_tone=arev1_tone rev2_tone=arev2_tone rev3_tone=arev3_tone rev1_exp=arev1_exp rev2_exp=arev2_exp rev3_exp=arev3_exp rev1_drive=arev1_drive noise_amt=anoise_amt noise_hold=anoise_hold noise_decay=anoise_decay noise_tone=anoise_tone"
    rndString = "20/02/14 19:02	001	shp1=0.03	shp2=1.59	maddcut=293.85	maddcutq=4.12	maddres=1.18	maddresq=3.71	maddpw=0.42	maddmix=0.36	madddet=0.0	chpattack=0.02	chpdecay=0.192	chpsustain=0.065	chprelease=0.005	chplfoscale=690.0	chplfoshift=1212.0	chpndecay=14.0	chpres=0.0	chpresq=16.15	chpdetune=0.017	chpshape=-0.45	strchlfofreq=0.064	strchlfoscale=1313.0	strchlfoshift=7811.0	strchlfood=0.83	strchndecay=5.651	strchres=0.011	strchresq=8.75	strchpm=0.82	strchdetune=0.012	strchattack=0.164	strchrelease=0.236	strchshape=-0.843	afreq0=279.0	afreq1=63.0	afreqdecay=0.07	aattack=0.002	adecay=0.14	adrive=2.7	arev1_amt=0.23	arev1_tone=3537.0	arev1_exp=6.74	arev1_drive=0.29	arev2_amt=0.14	arev2_tone=8614.0	arev2_exp=3.08	arev3_amt=0.84	arev3_tone=3743.0	arev3_exp=8.19	anoise_amt=0.09	anoise_hold=0.7	anoise_decay=0.71	anoise_tone=19391.0	shkamp=11.91	shktimbre=1.12	shkdecay=0.019	shkrelease=0.025"
    newMainName = "drykik"
    templateFixer = RandomTemplateFixer(template)
    output = templateFixer.fix(rndString, newMainName)
    print('\n', output)
