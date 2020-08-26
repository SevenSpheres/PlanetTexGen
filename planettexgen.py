from itertools import product
import math
import random
import os
from PIL import Image
import noise
import PySimpleGUI as sg

def generate(size, seed, type):
    width = size
    height = round(size/2)
    freq = 1
    octaves = 10
    persistence = 0.5
    lacunarity = 2.0
    tex = Image.new('RGB', (width, height))
    spec = Image.new('RGB', (width, height))
    scale = 5
    latitudes = [lat / scale for lat in range(int(-90 * scale), int(90 * scale) + 1)]
    longitudes = [lng / scale for lng in range(int(-180 * scale), int(180 * scale) + 1)]
    radius = height / math.pi
    lng_std = 0
    lat_std = 0
    if seed == '':
        rand = random.randint(-20000, 20000)
    else:
        rand = eval(seed)
    for x, y in product(range(width), range(height)):
        uvx = x / width
        uvy = y / height
        my = math.sin(uvy * math.pi - math.pi / 2)
        mx = math.cos(uvx * 2 * math.pi) * math.cos(uvy * math.pi - math.pi / 2)
        mz = math.sin(uvx * 2 * math.pi) * math.cos(uvy * math.pi - math.pi / 2)
        z = noise.snoise3(
            (mx + rand) / freq,
            (my + rand) / freq,
            mz / freq,
            octaves=octaves,
            persistence=persistence,
            lacunarity=lacunarity
        )
        z_normalized = (z + 1) / 2
        if type == 'Surface':
            color_a = (int(z_normalized*eval(values['LandR'])), int(z_normalized*eval(values['LandG'])), int(z_normalized*eval(values['LandB'])))
            color_b = (eval(values['OceanR']), eval(values['OceanG']), eval(values['OceanB']))
        if type == 'Bump':
            color_a = (int(z_normalized*200), int(z_normalized*200), int(z_normalized*200))
            color_b = (0, 0, 0)
        if type == 'Specular':
            color_a = (0, 0, 0)
            color_b = (255, 255, 255)
        if z_normalized > eval(values['OceanLevel']):
            color = color_a
        else:
            color = color_b
        tex.putpixel((x, y), color)
    return tex

layout = [
    [sg.Text('Land color:'), sg.Input(size=(10,1), key='LandR', default_text='250'),
    sg.Input(size=(10,1), key='LandG', default_text='200'),
    sg.Input(size=(10,1), key='LandB', default_text='150')],
    [sg.Text('Ocean color:'), sg.Input(size=(10,1), key='OceanR', default_text='29'),
    sg.Input(size=(10,1), key='OceanG', default_text='33'),
    sg.Input(size=(10,1), key='OceanB', default_text='48')],
    [sg.Text('Ocean level (0.25-0.75):'), sg.Input(size=(30,1), key='OceanLevel', default_text='0.5')],
    [sg.Text('Texture size:'), sg.Input(size=(15,1), key='TexSize', default_text='2048'),
    sg.Text('Seed:'), sg.Input(size=(15,1), key='Seed', default_text=random.randint(-20000, 20000))],
    [sg.Text('File name:'), sg.Input(size=(30,1), key='Filename', default_text='planet')],
    [sg.Text('Generate:'), sg.Checkbox('Surface', key='Surface', default=True), sg.Checkbox('Bump', key='Bump', default=False), sg.Checkbox('Specular', key='Spec', default=True)],
    [sg.Button('Generate'), sg.Button('Reset'), sg.Button('Exit'), sg.Text(size=(25,1), key='Output')],
    [sg.Button('Preview Surface'), sg.Button('Preview Bump'), sg.Button('Preview Spec')],
    [sg.Image(r'blank.png', key='Preview')],
]
window = sg.Window('Planet Texture Generator', layout, icon='icon.ico')

while True:
    event, values = window.read()
    temp = Image.new('RGB', (512, 256), (255, 255, 255))
    temp.save('temp.png')

    if event == sg.WIN_CLOSED or event == 'Exit':
        os.remove('temp.png')
        break

    if event == 'Reset':
        window['LandR'].update('250')
        window['LandG'].update('200')
        window['LandB'].update('150')
        window['OceanR'].update('29')
        window['OceanG'].update('33')
        window['OceanB'].update('48')
        window['OceanLevel'].update('0.5')
        window['TexSize'].update('2048')
        window['Seed'].update(random.randint(-20000, 20000))
        window['Filename'].update('planet')
        window['Surface'].update(True)
        window['Spec'].update(True)
        window['Bump'].update(False)
        window['Output'].update('All fields reset!')

    if event == 'Preview Surface':
        tex = generate(512, values['Seed'], 'Surface')
        tex.save('temp.png')
        window['Preview'].update('temp.png')
    if event == 'Preview Bump':
        tex = generate(512, values['Seed'], 'Bump')
        tex.save('temp.png')
        window['Preview'].update('temp.png')
    if event == 'Preview Spec':
        tex = generate(512, values['Seed'], 'Specular')
        tex.save('temp.png')
        window['Preview'].update('temp.png')

    if event == 'Generate':
        window['Output'].update('Generating texture...')
        if values['TexSize'] == '':
            window['Output'].update('Error: missing texture size!')
        elif values['LandR'] == '' or values['LandG'] == '' or values['LandB'] == '':
            window['Output'].update('Error: missing land color!')
        elif values['OceanR'] == '' or values['OceanG'] == '' or values['OceanB'] == '':
            window['Output'].update('Error: missing ocean color!')
        elif values['OceanLevel'] == '':
            window['Output'].update('Error: missing ocean level!')
        elif values['Filename'] == '':
            window['Output'].update('Error: missing filename!')
        else:
            size = eval(values['TexSize'])
            if values['Surface'] == True:
                tex = generate(size, values['Seed'], 'Surface')
                tex.save('%s.png' % values['Filename'])
            if values['Bump'] == True:
                bump = generate(size, values['Seed'], 'Bump')
                bump.save('%s-bump.png' % values['Filename'])
            if values['Spec'] == True:
                spec = generate(size, values['Seed'], 'Specular')
                spec.save('%s-spec.png' % values['Filename'])
            window['Output'].update('Texture(s) generated!')

window.close()