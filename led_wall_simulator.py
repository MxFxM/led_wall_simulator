import pygame
from pygame.locals import *
import random
import threading
import pyaudio
import numpy as np
import math

###################################################################################################
# LED Stripe Setup                                                                                #
###################################################################################################

# set number of leds per stripe, distance between leds, number of stripes, and distance between stripes
led_size = 8
NUMBER_OF_LEDS_PER_STRIPE = 67
DISTANCE_BETWEEN_LEDS = 5
NUMBER_OF_STRIPES = 16
DISTANCE_BETWEEN_STRIPES = 70
ANGLESPEED = 0.01



###################################################################################################
# Global variables                                                                                #
###################################################################################################

# keep the led values in global memory
leds = [[] for _ in range(NUMBER_OF_STRIPES)]
for stripe in leds:
    for led in range(NUMBER_OF_LEDS_PER_STRIPE):
        # set LED color
        randomcolor = (random.random()*255, random.random()*255, random.random()*255)
        led_color = pygame.Color(randomcolor)
        stripe.append(led_color)

# flag to stop other threads when the pygame window is closed
stop_threads_flag = False

# angle offset for circular patterns
offset = 0



###################################################################################################
# LED Stripe Animation Class using Pygame                                                         #
###################################################################################################

class LEDAnimation(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.running = False

    def run(self):
        global leds
        global stop_threads_flag
        global offset

        # initialize Pygame
        pygame.init()

        # set window size
        window_size = (1600, 900)
        #screen = pygame.display.set_mode(window_size)
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        WIDTH, HEIGHT = screen.get_size()
        print(WIDTH, HEIGHT)

        # set the window title
        pygame.display.set_caption("LED Wall Simulator")

        # set window background color
        background_color = pygame.Color("black")

        # set desired framerate and initialize the clock
        framerate = 30
        clock = pygame.time.Clock()

        # run the animation loop
        self.running = True
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        #pygame.quit()
                        self.running = False

            # fill the background with the background color
            screen.fill(background_color)

            # calculate the starting x and y positions for the first LED
            x_start = (window_size[0] - (NUMBER_OF_STRIPES * (led_size + DISTANCE_BETWEEN_STRIPES))) / 2
            y_start = (window_size[1] - (NUMBER_OF_LEDS_PER_STRIPE * (led_size + DISTANCE_BETWEEN_LEDS))) / 2

            # draw the LED stripes
            offset += ANGLESPEED
            for i in range(NUMBER_OF_STRIPES):
                for j in range(NUMBER_OF_LEDS_PER_STRIPE):
                    #y = y_start + (j * (led_size + DISTANCE_BETWEEN_LEDS))
                    #x = x_start + (i * (led_size + DISTANCE_BETWEEN_STRIPES))

                    center_x = WIDTH / 2
                    center_y = HEIGHT / 2
                    radius = 0
                    if WIDTH > HEIGHT:
                        radius = HEIGHT / 2
                    else:
                        radius = WIDTH / 2
                    x = center_x + math.cos(toRadians((i / NUMBER_OF_STRIPES) * 360) + offset) * (radius - (j / NUMBER_OF_LEDS_PER_STRIPE) * radius)
                    y = center_y + math.sin(toRadians((i / NUMBER_OF_STRIPES) * 360) + offset) * (radius - (j / NUMBER_OF_LEDS_PER_STRIPE) * radius)

                    pygame.draw.circle(screen, leds[i][j], (x + led_size // 2, y + led_size // 2), led_size // 2)

            # update the display
            pygame.display.update()

            # limit the framerate to 60Hz
            clock.tick(framerate)

        # quit Pygame
        pygame.quit()

        # stop other threads
        stop_threads_flag = True



###################################################################################################
# Audio Recording and Handling                                                                    #
###################################################################################################

class AudioThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.stop_event = threading.Event()

    def run(self):
        global leds
        global stop_threads_flag

        # define the audio recording parameters
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 44100

        # initialize the audio stream
        p = pyaudio.PyAudio()
        stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)

        # start recording
        while not self.stop_event.is_set():
            # check global flag to stop executing
            if stop_threads_flag:
                break

            # read audio data from the stream
            data = stream.read(CHUNK)

            # convert the audio data to a numpy array
            audio_samples = np.frombuffer(data, dtype=np.int16)

            # process the audio data
            #leds = animation_sample_values(audio_samples, CHUNK, leds)
            leds =  animation_fft1024_one_bin_each(audio_samples, leds)
            #leds = animation_rainbow_left_to_right(leds)
            #leds = animation_rainbow_per_led(leds)
            #leds = animation_bass_from_right_to_left(audio_samples, leds)
            #leds = animation_bass_from_right_to_left_centered(audio_samples, leds)
            #leds = animation_bass_from_the_bottom_up_centered(audio_samples, leds)
            #leds = animation_rainbow_circular(leds)
            #leds = animation_bass_from_the_center_outwards_circular(audio_samples, leds)
            #leds = animation_bass_from_the_center_outwards_elliptical(audio_samples, leds)
            #leds = animation_blocks_for_each_frequency(audio_samples, leds)

        # stop recording
        stream.stop_stream()
        stream.close()
        p.terminate()

    def stop(self):
        self.stop_event.set()



###################################################################################################
# Helper Functions                                                                                #
###################################################################################################

def fft(samples):
    result = np.abs(np.fft.fft(samples))
    return result

def toHsv(r, g, b):
    r, g, b = r/255.0, g/255.0, b/255.0
    cmax = max(r, g, b)
    cmin = min(r, g, b)
    delta = cmax - cmin
    h = 0
    if delta == 0:
        h = 0
    elif cmax == r:
        h = 60 * (((g-b)/delta) % 6)
    elif cmax == g:
        h = 60 * (((b-r)/delta) + 2)
    elif cmax == b:
        h = 60 * (((r-g)/delta) + 4)
    s = 0 if cmax == 0 else delta/cmax
    v = cmax
    return (h, s, v)

def toRgb(h, s, v):
    h = h / 255.0
    s = s / 255.0
    v = v / 255.0
    i = int(h * 6)
    f = h * 6 - i
    p = v * (1 - s)
    q = v * (1 - f * s)
    t = v * (1 - (1 - f) * s)
    if i % 6 == 0:
        r, g, b = v, t, p
    elif i % 6 == 1:
        r, g, b = q, v, p
    elif i % 6 == 2:
        r, g, b = p, v, t
    elif i % 6 == 3:
        r, g, b = p, q, v
    elif i % 6 == 4:
        r, g, b = t, p, v
    else:
        r, g, b = v, p, q
    return (int(r * 255), int(g * 255), int(b * 255))

def animateHue():
    global hue

    try:
        hue = hue + 1
        if hue > 255:
            hue = hue - 255
    except Exception as _:
        hue = 0
    
    return hue

def mapValue(value, inmin, inmax, outmin, outmax):
    return (value - inmin) * (outmax - outmin) / (inmax - inmin) + outmin

def limitValue(value, min, max):
    if value < min:
        value = min
    if value > max:
        value = max
    return value

def getDistance(x, y):
    sum = x**2 + y**2
    return math.sqrt(sum)

def toRadians(degrees):
    radians = (degrees / 360) * 2 * math.pi
    return radians

def toDegrees(radians):
    degrees = (radians / (2 * math.pi)) * 360
    return degrees

###################################################################################################
# Different Animations for the Wall                                                               #
###################################################################################################
def animation_sample_values(audio_samples, length, leds):
    """
    The samples are read.
    Every n-th sample is selected, such that the number of selected samples equals the number of led stripes.
    Each led strip is lit up to the led number according to the absolute value of that selected sample.
    """
    # process values for the strips
    n = length // NUMBER_OF_STRIPES
    stripe_values = audio_samples[::n]
    stripe_values = [int((abs(v)/32767)*NUMBER_OF_LEDS_PER_STRIPE) for v in stripe_values]

    # update leds
    for stripe in range(NUMBER_OF_STRIPES):
        led_range = NUMBER_OF_LEDS_PER_STRIPE - stripe_values[stripe]
        leds[stripe][:led_range] = [(0, 0, 0)] * led_range
        leds[stripe][led_range:] = [(255, 255, 255)] * stripe_values[stripe]

    # return led values
    return leds

def animation_fft1024_one_bin_each(audio_samples, leds):
    """
    The samples are read.
    A 1024 bin fft is performed.
    The lowest n bins are used to decide how many of the x leds on each of n stripes should be lit.
    """
    # process values for the strips
    fft_result = fft(audio_samples)
    stripe_values = fft_result[:NUMBER_OF_STRIPES]
    maxval = np.max(stripe_values)
    if maxval == 0:
        maxval = 1
    stripe_values = [int((v/maxval)*NUMBER_OF_LEDS_PER_STRIPE) for v in stripe_values]

    # update leds
    for stripe in range(NUMBER_OF_STRIPES):
        led_range = NUMBER_OF_LEDS_PER_STRIPE - stripe_values[stripe]
        leds[stripe][:led_range] = [(0, 0, 0)] * led_range
        leds[stripe][led_range:] = [(255, 255, 255)] * stripe_values[stripe]

    # return led values
    return leds

def animation_rainbow_left_to_right(leds):
    hue = animateHue()

    for stripe in range(NUMBER_OF_STRIPES):
        color = toRgb(hue + 20*stripe, 255, 255)
        leds[stripe] = [color for _ in range(len(leds[stripe]))]
    
    return leds

def animation_rainbow_per_led(leds):
    hue = animateHue()

    for stripe in range(NUMBER_OF_STRIPES):
        for led in range(NUMBER_OF_LEDS_PER_STRIPE):
            leds[stripe][led] = toRgb(int(hue + 5 * led + NUMBER_OF_LEDS_PER_STRIPE * stripe), 255, 255)
        
    return leds

def animation_bass_from_right_to_left(audio_samples, leds):
    global stripes
    global peak

    hue = animateHue()

    try:
        for stripe in range(NUMBER_OF_STRIPES - 1):
            stripes[stripe] = stripes[stripe + 1]

        fft_result = fft(audio_samples)
        stripes[-1] = np.sum(fft_result[:3])

        if stripes[-1] > peak:
            peak = stripes[-1]
        if stripes[-1] < peak / 10:
            peak = peak * 0.75
    except Exception as _:
        stripes = [0 for _ in range(NUMBER_OF_STRIPES)]
        peak = 32767
    
    for stripe in range(NUMBER_OF_STRIPES):
        turnonnr = int(mapValue(stripes[stripe], 0, peak, 0, NUMBER_OF_LEDS_PER_STRIPE))
        turnonnr = limitValue(turnonnr, 0, NUMBER_OF_LEDS_PER_STRIPE)
        led_range = NUMBER_OF_LEDS_PER_STRIPE - turnonnr
        leds[stripe][:led_range] = [(0, 0, 0)] * led_range
        leds[stripe][led_range:] = [toRgb(hue, 255, 255)] * turnonnr
    
    return leds

def animation_bass_from_right_to_left_centered(audio_samples, leds):
    global stripes
    global peak

    hue = animateHue()

    try:
        for stripe in range(NUMBER_OF_STRIPES - 1):
            stripes[stripe] = stripes[stripe + 1]

        fft_result = fft(audio_samples)
        stripes[-1] = np.sum(fft_result[:3])

        if stripes[-1] > peak:
            peak = stripes[-1]
        if stripes[-1] < peak / 10:
            peak = peak * 0.75
    except Exception as _:
        stripes = [0 for _ in range(NUMBER_OF_STRIPES)]
        peak = 32767
    
    for stripe in range(NUMBER_OF_STRIPES):
        turnonnr = int(mapValue(stripes[stripe], 0, peak, 0, NUMBER_OF_LEDS_PER_STRIPE/2))
        turnonnr = limitValue(turnonnr, 0, NUMBER_OF_LEDS_PER_STRIPE/2)
        for led in range(NUMBER_OF_LEDS_PER_STRIPE):
            if led < NUMBER_OF_LEDS_PER_STRIPE/2 - turnonnr or led > NUMBER_OF_LEDS_PER_STRIPE/2 + turnonnr:
                leds[stripe][led] = (0, 0, 0)
            else:
                leds[stripe][led] = toRgb(hue, 255, 255)
    
    return leds

def animation_bass_from_the_bottom_up_centered(audio_samples, leds):
    global stripes
    global peak

    hue = animateHue()

    try:
        for stripe in range(NUMBER_OF_LEDS_PER_STRIPE - 1):
            stripes[stripe] = stripes[stripe + 1]

        fft_result = fft(audio_samples)
        stripes[-1] = np.sum(fft_result[:3])

        if np.max(stripes) > peak:
            peak = np.max(stripes)
        if np.max(stripes) < peak / 10:
            peak = peak * 0.75
    except Exception as _:
        stripes = [0 for _ in range(NUMBER_OF_LEDS_PER_STRIPE)]
        peak = 32767
    
    for led in range(NUMBER_OF_LEDS_PER_STRIPE):
        turnonnr = int(mapValue(stripes[led], 0, peak, 0, NUMBER_OF_STRIPES/2))
        turnonnr = limitValue(turnonnr, 0, NUMBER_OF_STRIPES/2)
        for stripe in range(NUMBER_OF_STRIPES):
            if stripe < NUMBER_OF_STRIPES/2 - turnonnr or stripe > NUMBER_OF_STRIPES/2 + turnonnr:
                leds[stripe][led] = (0, 0, 0)
            else:
                leds[stripe][led] = toRgb(hue + 2 * led, 255, 255)
    
    return leds

def animation_rainbow_circular(leds):
    hue = animateHue()
    maxdistance = getDistance(70 * NUMBER_OF_STRIPES/2, 5 * NUMBER_OF_LEDS_PER_STRIPE/2)

    for stripe in range(NUMBER_OF_STRIPES):
        for led in range(NUMBER_OF_LEDS_PER_STRIPE):
            x = (stripe - NUMBER_OF_STRIPES/2) * 70
            y = (led - NUMBER_OF_LEDS_PER_STRIPE/2) * 5
            hueadd = mapValue(getDistance(x, y), 0, maxdistance, 0, 255)
            thishue = int(hue + hueadd)
            leds[stripe][led] = toRgb(thishue, 255, 255)

    return leds

def animation_bass_from_the_center_outwards_circular(audio_samples, leds):
    global stripes
    global peak

    hue = animateHue()
    maxdistance = getDistance(70 * NUMBER_OF_STRIPES/2, 5 * NUMBER_OF_LEDS_PER_STRIPE/2)
    ringlength = 20

    try:
        for stripe in range(ringlength - 1, 0, -1):
            stripes[stripe] = stripes[stripe - 1]

        fft_result = fft(audio_samples)
        stripes[0] = np.sum(fft_result[:3])

        if np.max(stripes) > peak:
            peak = np.max(stripes)
        if np.max(stripes) < peak / 10:
            peak = peak * 0.75
    except Exception as _:
        stripes = [0 for _ in range(ringlength)]
        peak = 32767

    for stripe in range(NUMBER_OF_STRIPES):
        for led in range(NUMBER_OF_LEDS_PER_STRIPE):
            x = (stripe - NUMBER_OF_STRIPES/2) * 70
            y = (led - NUMBER_OF_LEDS_PER_STRIPE/2) * 5
            thisdistance = getDistance(x, y)
            lowerindex = int(mapValue(thisdistance, 0, maxdistance, 0, ringlength-2))
            thisvalue = (stripes[lowerindex+1] - stripes[lowerindex]) * (lowerindex/ringlength) + stripes[lowerindex]
            hueadd = mapValue(thisdistance, 0, maxdistance, 0, 255)
            thishue = int(hue + hueadd)
            myvalue = int(mapValue(thisvalue, 0, peak, 0, 255))
            leds[stripe][led] = toRgb(thishue, 255, myvalue)

    return leds

def animation_bass_from_the_center_outwards_elliptical(audio_samples, leds):
    global stripes
    global peak

    hue = animateHue()
    maxdistance = getDistance(4 * NUMBER_OF_STRIPES/2, NUMBER_OF_LEDS_PER_STRIPE/2)
    ringlength = 20

    try:
        for stripe in range(ringlength - 1, 0, -1):
            stripes[stripe] = stripes[stripe - 1]

        fft_result = fft(audio_samples)
        stripes[0] = np.sum(fft_result[:3])

        if np.max(stripes) > peak:
            peak = np.max(stripes)
        if np.max(stripes) < peak / 10:
            peak = peak * 0.75
    except Exception as _:
        stripes = [0 for _ in range(ringlength)]
        peak = 32767

    for stripe in range(NUMBER_OF_STRIPES):
        for led in range(NUMBER_OF_LEDS_PER_STRIPE):
            x = (stripe - (NUMBER_OF_STRIPES-1)/2) * 4
            y = (led - NUMBER_OF_LEDS_PER_STRIPE/2)
            thisdistance = getDistance(x, y)
            lowerindex = int(mapValue(thisdistance, 0, maxdistance, 0, ringlength-2))
            thisvalue = (stripes[lowerindex+1] - stripes[lowerindex]) * (lowerindex/ringlength) + stripes[lowerindex]
            hueadd = mapValue(thisdistance, 0, maxdistance, 0, 255)
            thishue = int(hue + hueadd)
            myvalue = int(mapValue(thisvalue, 0, peak, 0, 255))
            leds[stripe][led] = toRgb(thishue, 255, myvalue)

    return leds

def animation_blocks_for_each_frequency(audio_samples, leds):
    global stripes
    global peaks

    hue = animateHue()
    xblocks = 4
    yblocks = 3
    nrofblocks = xblocks * yblocks

    try:
        fft_result = fft(audio_samples)
        start = 0
        for x in range(xblocks):
            for y in range(yblocks):
                stripes[x * yblocks + y] = np.sum(fft_result[start:start+1])
                if stripes[x * yblocks + y] > peaks[x * yblocks + y]:
                    peaks[x * yblocks + y] = peaks[x * yblocks + y] * 2 #stripes[x * yblocks + y]
                if stripes[x * yblocks + y] < peaks[x * yblocks + y] / 10:
                    peaks[x * yblocks + y] = peaks[x * yblocks + y] * 0.75
                start = start + 1

    except Exception as _:
        stripes = [0 for _ in range(nrofblocks)]
        peaks = [32767 for _ in range(nrofblocks)]

    for stripe in range(NUMBER_OF_STRIPES):
        xblock = math.floor(stripe / (NUMBER_OF_STRIPES / xblocks)) #stripe
        for led in range(NUMBER_OF_LEDS_PER_STRIPE):
            yblock = math.floor(led / (NUMBER_OF_LEDS_PER_STRIPE / yblocks)) #stripe
            myvalue = mapValue(stripes[xblock * yblocks + yblock], 0, peaks[xblock * yblocks + yblock], 0, 255)
            myvalue = limitValue(myvalue, 0, 255)
            leds[stripe][led] = toRgb(hue + (xblock*yblocks + yblock) * 30, 255, myvalue)

    return leds
 


###################################################################################################
# Main Script to start all threads                                                                #
###################################################################################################

if __name__ == "__main__":
    led_animation = LEDAnimation()
    led_animation.start()

    audio_processing = AudioThread()
    audio_processing.start()