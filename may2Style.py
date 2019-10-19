from PyQt5.QtGui import QFont

default_textcolor = (200, 230, 130)
group_bgcolor = (10, 0, 30)
button_bgcolor = (120, 60, 180)
button_textcolor = (230, 200, 255)
field_bgcolor = (60, 10, 80)
rendergroup_bordercolor = (160, 0, 190)

default_fontname = 'RobotoMono' # TODO: HOW CAN I USE THIS FONT, GOD DAMMIT FUCKING SHIT
default_fontsize = 17

notACrime = """

MainWindow {
    /* background-color: white; */
}

QGroupBox {
    background-color: GROUP_BGCOLOR;
    border-radius: 10px;
    border-width: 0px;
    border-style: solid;
    border-color: white;
    padding: 5px;
}

QGroupBox::title {
    color: DEFAULT_TEXTCOLOR
}

QGroupBox#activated {
    border-width: 5px;
    border-color: rgb(128, 0, 128);
}

"""\
    .replace('DEFAULT_TEXTCOLOR', 'rgb' + str(default_textcolor))\
    .replace('GROUP_BGCOLOR', 'rgb' + str(group_bgcolor))\
    .replace('BUTTON_BGCOLOR', 'rgb' + str(button_bgcolor))\
    .replace('BUTTON_TEXTCOLOR', 'rgb' + str(button_textcolor))\
    .replace('FIELD_BGCOLOR', 'rgb' + str(field_bgcolor))\
    .replace('RENDERGROUP_BORDERCOLOR', 'rgb' + str(rendergroup_bordercolor))
