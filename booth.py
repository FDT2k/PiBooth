import time
import picamera
import picamera.array
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
from time import sleep
import RPi.GPIO as gpio
import io
import string
from subprocess import Popen, PIPE

from subprocess import call
import numpy as np

def white_balance():
    # custom white balance
    camera.awb_mode = 'off'
    # Start off with ridiculously low gains
    rg, bg = (0.5, 0.5)
    camera.awb_gains = (rg, bg)
    with picamera.array.PiRGBArray(camera, size=(128, 72)) as output:
        # Allow 30 attempts to fix AWB
        for i in range(30):
            # Capture a tiny resized image in RGB format, and extract the
            # average R, G, and B values
            camera.capture(output, format='rgb', resize=(128, 72), use_video_port=True)
            r, g, b = (np.mean(output.array[..., i]) for i in range(3))
            print('R:%5.2f, B:%5.2f = (%5.2f, %5.2f, %5.2f)' % (
                rg, bg, r, g, b))
            # Adjust R and B relative to G, but only if they're significantly
            # different (delta +/- 2)
            if abs(r - g) > 2:
                if r > g:
                    rg -= 0.1
                else:
                    rg += 0.1
            if abs(b - g) > 1:
                if b > g:
                    bg -= 0.1
                else:
                    bg += 0.1
            camera.awb_gains = (rg, bg)
            output.seek(0)
            output.truncate()

def display_overlay_timeout(file, delay):
    img = Image.open(file)
    o = display_overlay_image(img)
    sleep(delay)
    camera.remove_overlay(o)


def display_overlay_image(img):
    pad = Image.new('RGB', (
        ((img.size[0] + 31) // 32) * 32,
        ((img.size[1] + 15) // 16) * 16,
        ))
    pad.paste(img, (0, 0))
    o = camera.add_overlay(pad.tostring(), size=img.size)
    o.alpha = 128
    o.layer = 3
    return o




def start_capture():
    print " capture "

    display_overlay_timeout('overlay_3.png',1)

    display_overlay_timeout('overlay_2.png',1)

    display_overlay_timeout('overlay_1.png',1)

    # capture to stream
    stream = io.BytesIO()
    camera.capture(stream, format='jpeg')
    stream.seek(0)
    img = Image.open(stream)


    o = display_overlay_image(img)

    top =  (height /2) - (crop_size() /2)
    left =  (width /2) -(crop_size() /2)

    # debug info
    print "height "+str(height)
    print "width "+ str(width)
    print crop_size(),top, left

    img = img.crop((left, top, left+crop_size(),top+crop_size()))
    img.save('out.jpg')
    camera.remove_overlay(o)
    img.close();
    stream = None

    #camera.capture('foo.jpg')
    #-o media=4X6FULL -o position=top -o orientation-requested=1 -o mediatype=PMPHOTO_HIGH
    # print quality parameters config in cups.



    img = Image.open("out.jpg")

    display_overlay_timeout("develop.png",5)

    output = Image.new('RGBA',(img.size[0],img.size[1]+50),"white")
    draw = ImageDraw.Draw(output)
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
    h = int(img.size[1])+15
    draw.text((0,h),"Moi je ...",(0,0,0),font=font)
    output.paste(img,(0,0))
    output.save('sample-out.jpg')
    #write out some text
    call(["lp","sample-out.jpg","-o","position=top"])
    output.close()
    img.close();
    #write out some text





def crop_size():
    if (orientation == ORIENTATION_PORTRAIT):
        return width
    else:
        return height


# initialize scrpt

GPIO_PIN=25
ORIENTATION_PORTRAIT = 0
ORIENTATION_LANDSCAPE = 1

gpio.setmode(gpio.BCM)
gpio.setup(GPIO_PIN, gpio.IN, pull_up_down=gpio.PUD_UP)

#detecting configured framebuffer size, you can force it in /boot/config.txt

p = Popen(['cat', '/sys/class/graphics/fb0/virtual_size'], stdin=PIPE, stdout=PIPE, stderr=PIPE)
output, err = p.communicate()
#print output,err
rc = p.returncode
width,height = string.split(output,",")
width = int(width)
height = int(height)
#print width,height


if height > width:
    orientation = ORIENTATION_PORTRAIT
else:
    orientation = ORIENTATION_LANDSCAPE

camera = picamera.PiCamera()
camera.led = False
camera.hflip = True
camera.resolution = (int(width), int(height))
camera.framerate = 24
camera.start_preview()

white_balance()





# Wait indefinitely until the user terminates the script
while True:
    input = gpio.input(GPIO_PIN)
    if input == False:
            print "button"
            start_capture()

    time.sleep(0.1)
