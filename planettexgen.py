from itertools import product
import math
import random
from PIL import Image
import noise
import PySimpleGUI as sg

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
    [sg.Button('Generate'), sg.Button('Reset'), sg.Button('Exit'), sg.Text(size=(25,1), key='Output')],
]
window = sg.Window('Planet Texture Generator', layout, icon='icon.ico')

while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED or event == 'Exit':
        break

    if event == 'Reset':
        window['LandR'].update('250')
        window['LandG'].update('180')
        window['LandB'].update('130')
        window['OceanR'].update('29')
        window['OceanG'].update('33')
        window['OceanB'].update('48')
        window['OceanLevel'].update('0.5')
        window['TexSize'].update('2048')
        window['Seed'].update(random.randint(-20000, 20000))
        window['Filename'].update('planet')
        window['Output'].update('All fields reset!')

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

            if values['Seed'] == '':
                rand = random.randint(-20000, 20000)
            else:
                rand = eval(values['Seed'])

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
                color_a = (int(z_normalized*eval(values['LandR'])), int(z_normalized*eval(values['LandG'])), int(z_normalized*eval(values['LandB'])))
                color_b = (eval(values['OceanR']), eval(values['OceanG']), eval(values['OceanB']))

                if z_normalized < (1-eval(values['OceanLevel'])):
                    color = color_a
                else:
                    color = color_b

                tex.putpixel((x, y), color)

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
                color_a = (0, 0, 0)
                color_b = (255, 255, 255)

                if z_normalized < (1-eval(values['OceanLevel'])):
                    color = color_a
                else:
                    color = color_b

                spec.putpixel((x, y), color)

            tex.save('%s.png' % values['Filename'])
            spec.save('%s-spec.png' % values['Filename'])
            window['Output'].update('Texture generated!')

window.close()