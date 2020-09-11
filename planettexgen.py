from itertools import product
from math import radians, pi, sin, cos, sqrt
from random import randint
import os
import sys
import inspect
from PIL import Image, ImageDraw, ImageFilter
import noise
import PySimpleGUI as sg

def folder(follow_symlinks=True): # Automatic main folder path detection (by jfs)
    if getattr(sys, 'frozen', False): # py2exe, PyInstaller, cx_Freeze
        path = os.path.abspath(sys.executable)
    else:
        path = inspect.getabsfile(folder)
    if follow_symlinks:
        path = os.path.realpath(path)
    return os.path.dirname(path) + "/"
path = folder()

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
    radius = height / pi
    lng_std = 0
    lat_std = 0
    if seed == '':
        rand = randint(-20000, 20000)
    else:
        rand = eval(seed)
    for x, y in product(range(width), range(height)):
        uvx = x / width
        uvy = y / height
        my = sin(uvy * pi - pi / 2)
        mx = cos(uvx * 2 * pi) * cos(uvy * pi - pi / 2)
        mz = sin(uvx * 2 * pi) * cos(uvy * pi - pi / 2)
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

def add_ice(img, lat, iceColor):
    rand = 20    # maximum random brightness addition
    blur = 2     # noise blur radius
    side = 12    # half side of ice square near land
    snow = 40    # extra brightness on land
    lon = 6      # luminance addition from longitude
    w0 = img.size[0]
    w = int(w0 * 1.5)
    h = img.size[1]
    # Create maps one and a half times longer than the original
    base = Image.new('RGB', (w, h))
    spec = Image.new('L', (w, h), 255) # water map
    mask = Image.new('L', (w, h)) # conditionally temperature map
    draw_spec = ImageDraw.Draw(spec)
    draw_mask = ImageDraw.Draw(mask)
    base.paste(img, (0, 0))
    base.paste(img, (w0, 0))
    draw_base = ImageDraw.Draw(base)
    # Add polar ice caps to the mask and fill in the water map
    for x in range(w):
        for y in range(h):
            br = 255 * (1 + sin(pi * (1 + y/h))) # formula of caps from illumination
            br += lon * sin(pi*(1 + 3*x / w))  # roughness by longitude
            color = base.getpixel((x, y))
            if not (color[0] == eval(values['OceanR']) and color[1] == eval(values['OceanG']) and color[2] == eval(values['OceanB'])):
                br += snow
                draw_spec.point((x, y), 0)
            br += randint(-rand, rand)
            draw_mask.point((x, y), int(br))
    # "Pulling" ice to the continents using the Pluto-Charon heights method
    p = spec.load()
    for x, y in product(range(w), range(h)):
            b0 = p[x, y]
            if b0 != 0:
                n = 0
                while True:
                    n += 1
                    if x+n >= w or y+n >= h or x-n <= 0 or y-n <= 0:
                        break
                    if n > side:
                        break
                    for i in range(1, n+1):
                        if 0 in [p[x+i, y+n], p[x+i, y-n], p[x-i, y+n], p[x-i, y-n], p[x+n, y+i], p[x+n, y-i], p[x-n, y+i], p[x-n, y-i]]:
                            a = 1 - sqrt(n**2 + i**2) / side
                            b1 = mask.getpixel((x, y)) + int(a * snow/4)
                            draw_mask.point((x, y), b1)
                            break
    # Transferring ice from mask to base map
    mask = mask.filter(ImageFilter.GaussianBlur(blur))
    mask.save(path + 'mask.png')
    base = base.convert('RGBA')
    draw_base = ImageDraw.Draw(base)
    limit = (1 - abs(cos(radians(lat)))) * 255
    for x, y in product(range(w), range(h)):
        if mask.getpixel((x, y)) > limit:
            color = iceColor
            draw_spec.point((x, y), 64)
        else:
            color = base.getpixel((x, y))
        draw_base.point((x, y), color)
    # Move the piece, cut off the excess and save
    crop = (w0, 0, int(1.25 * w0), h)
    base.paste(base.crop(crop))
    spec.paste(spec.crop(crop))
    cut = (0, 0, w0, h) # original size
    os.remove(path + 'mask.png')
    return [base.crop(cut), spec.crop(cut)]

left = [
    [sg.Text('Settings', font=("arial", 12))], 
    [sg.Text('Texture size'), sg.Input(size=(10, 1), key='TexSize', default_text='2048')], 
    [sg.Text('File name:'), sg.Input(size=(10, 1), key='Filename', default_text='planet')],
    [sg.Text('Seed'), sg.Input(size=(6, 1), key='Seed', default_text=randint(-20000, 20000))],
    [sg.Text("_" * 32, size=(22, 1))],
    [sg.Text('Lands', font=("arial", 12))], 
    [sg.Text('Color'), 
    sg.Input(size=(4, 1), key='LandR', default_text='250'), 
    sg.Input(size=(4, 1), key='LandG', default_text='200'), 
    sg.Input(size=(4, 1), key='LandB', default_text='150')],
    [sg.Text("_" * 32, size=(22, 1))],
    [sg.Text('Oceans', font=("arial", 12))], 
    [sg.Text('Color'), 
    sg.Input(size=(4, 1), key='OceanR', default_text='29'),
    sg.Input(size=(4, 1), key='OceanG', default_text='33'),
    sg.Input(size=(4, 1), key='OceanB', default_text='48')],
    [sg.Text('Level (0.25-0.75)'), sg.Input(size=(4, 1), key='OceanLevel', default_text='0.5')],
    [sg.Text("_" * 32, size=(22, 1))],
    [sg.Checkbox('Ice', font=("arial", 12), key='Ice', default=False, enable_events=True)],
    [sg.Text('Color'), 
    sg.Input(size=(4, 1), key='IceR', default_text='240', disabled=True, disabled_readonly_text_color='#444444', disabled_readonly_background_color='#bbbbbb'),
    sg.Input(size=(4, 1), key='IceG', default_text='245', disabled=True, disabled_readonly_text_color='#444444', disabled_readonly_background_color='#bbbbbb'),
    sg.Input(size=(4, 1), key='IceB', default_text='250', disabled=True, disabled_readonly_text_color='#444444', disabled_readonly_background_color='#bbbbbb')],
    [sg.Text('Latitude'), sg.Input(size=(4, 1), key='IceLevel', default_text='60', disabled=True, disabled_readonly_text_color='#444444', disabled_readonly_background_color='#bbbbbb')],
]
right = [
    [sg.Text('Generate:'), sg.Checkbox('Surface', key='Surface', default=True), sg.Checkbox('Bump', key='Bump', default=False), sg.Checkbox('Specular', key='Spec', default=True)],
    [sg.Button('Preview Surface'), sg.Button('Preview Bump'), sg.Button('Preview Spec'), sg.Button('Generate'), sg.Button('Reset'), sg.Button('Exit')],
    [sg.Text(size=(25, 1), key='Output')],
    [sg.Image(path+'blank.png', key='Preview')],
]
layout = [
    [sg.Column(left), sg.VSeperator(), sg.Column(right)]
]
window = sg.Window('Planet Texture Generator', layout, icon='icon.ico')

while True:
    event, values = window.read()
    temp = Image.new('RGB', (512, 256), (255, 255, 255))
    temp.save(path + 'temp.png')

    if event == sg.WIN_CLOSED or event == 'Exit':
        os.remove(path + 'temp.png')
        break

    if event == 'Reset':
        window['TexSize'].update('2048')
        window['Filename'].update('planet')
        window['Seed'].update(randint(-20000, 20000))
        window['LandR'].update('250')
        window['LandG'].update('200')
        window['LandB'].update('150')
        window['OceanR'].update('29')
        window['OceanG'].update('33')
        window['OceanB'].update('48')
        window['OceanLevel'].update('0.5')
        window['Ice'].update(False)
        window['IceR'].update('240')
        window['IceG'].update('245')
        window['IceB'].update('250')
        window['IceLevel'].update('60', disabled=True, text_color='#444444')
        window['Surface'].update(True)
        window['Spec'].update(True)
        window['Bump'].update(False)
        window['Output'].update('All fields reset!')

    if event.startswith('Ice'):
        if values['Ice'] == True:
            window['IceR'].update(disabled=False, text_color='#000000')
            window['IceG'].update(disabled=False, text_color='#000000')
            window['IceB'].update(disabled=False, text_color='#000000')
            window['IceLevel'].update(disabled=False, text_color='#000000')
        if values['Ice'] == False:
            window['IceR'].update(disabled=True, text_color='#444444')
            window['IceG'].update(disabled=True, text_color='#444444')
            window['IceB'].update(disabled=True, text_color='#444444')
            window['IceLevel'].update(disabled=True, text_color='#444444')

    if event == 'Preview Surface':
        tex = generate(512, values['Seed'], 'Surface')
        if values['Ice']:
            tex = add_ice(tex, eval(values['IceLevel']), (eval(values['IceR']), eval(values['IceG']), eval(values['IceB'])))[0]
        tex.save(path + 'temp.png')
        window['Preview'].update(path + 'temp.png')
    if event == 'Preview Bump':
        tex = generate(512, values['Seed'], 'Bump')
        tex.save(path + 'temp.png')
        window['Preview'].update(path + 'temp.png')
    if event == 'Preview Spec':
        tex = generate(512, values['Seed'], 'Specular')
        if values['Ice']:
            tex = add_ice(tex, eval(values['IceLevel']), (eval(values['IceR']), eval(values['IceG']), eval(values['IceB'])))[1]
        tex.save(path + 'temp.png')
        window['Preview'].update(path + 'temp.png')

    if event == 'Generate':
        window['Output'].update('Generating texture...')
        if values['LandR'] == '' or values['LandG'] == '' or values['LandB'] == '':
            window['Output'].update('Error: missing land color!')
        elif values['OceanR'] == '' or values['OceanG'] == '' or values['OceanB'] == '':
            window['Output'].update('Error: missing ocean color!')
        elif values['OceanLevel'] == '':
            window['Output'].update('Error: missing ocean level!')
        elif values['Ice'] == True and values['IceLevel'] == '':
            window['Output'].update('Error: missing ice level!')
        elif values['TexSize'] == '':
            window['Output'].update('Error: missing texture size!')
        elif values['Filename'] == '':
            window['Output'].update('Error: missing filename!')
        else:
            size = eval(values['TexSize'])
            if values['Surface']:
                tex = generate(size, values['Seed'], 'Surface')
                if values['Ice']:
                    tex = add_ice(tex, eval(values['IceLevel']), (eval(values['IceR']), eval(values['IceG']), eval(values['IceB'])))[0]
                    spec = add_ice(tex, eval(values['IceLevel']), (eval(values['IceR']), eval(values['IceG']), eval(values['IceB'])))[1]
                tex.save(path + '%s.png' % values['Filename'])
            if values['Bump']:
                bump = generate(size, values['Seed'], 'Bump')
                bump.save(path + '%s-bump.png' % values['Filename'])
            if values['Spec']:
                if values['Ice'] == False or values['Surface'] == False:
                    spec = generate(size, values['Seed'], 'Specular')
                spec.save(path + '%s-spec.png' % values['Filename'])
            window['Output'].update('Texture(s) generated!')

window.close()