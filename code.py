import math
import adafruit_json_stream as json_stream
import os
import gc
import ipaddress
import wifi
import socketpool
import time
import ssl
import microcontroller
import adafruit_requests
import secrets
import neopixel
import board
num_pixels = 30


#connect both strips to one GPIO
pixel_pin = board.GP17
num_pixels = 30

pixels = neopixel.NeoPixel(pixel_pin, num_pixels, brightness=0.3, auto_write=False)

def color_chase(color, wait):
    for i in range(num_pixels):
        pixels[i] = color
        time.sleep(wait)
        pixels.show()
    time.sleep(0.5)

def colorwheel(pos):
    # Input a value 0 to 255 to get a color value.
    # The colours are a transition r - g - b - back to r.
    if pos < 0 or pos > 255:
        return (0, 0, 0, 0)
    if pos < 85:
        return (255 - pos * 3, pos * 3, 0, 0)
    if pos < 170:
        pos -= 85
        return (0, 255 - pos * 3, pos * 3, 0)
    pos -= 170
    return (pos * 3, 0, 255 - pos * 3, 0)

def rainbow_cycle(wait):
    for j in range(255):
        for i in range(num_pixels):
            rc_index = (i * 256 // num_pixels) + j
            pixels[i] = colorwheel(rc_index & 255)
        pixels.show()
        time.sleep(wait)


# turn off all the lights
pixels.fill((0,0,0))
pixels.show()

# let's do some rainbows!
for i in range(10):
    rainbow_cycle(0)  

# pause for photos
time.sleep(40)

# get the secret codes for each runner
runners = secrets.runners

print("Connecting to WiFi")
wifi.radio.connect(os.getenv('CIRCUITPY_WIFI_SSID'), os.getenv('CIRCUITPY_WIFI_PASSWORD'))
print("Connected to WiFi")
pool = socketpool.SocketPool(wifi.radio)
print("IP:", wifi.radio.ipv4_address)

auth_url = "https://www.strava.com/oauth/token"

for i, runner in enumerate(runners):
    # memory hack
    gc.collect()
    
    print("Runner "+str(i))
    # create a new request for each runner
    requests = adafruit_requests.Session(pool, ssl.create_default_context())

    # create a new payload with ids and secrets
    payload = {
    'client_id': str(secrets.payload['client_id']),
    'client_secret': str(secrets.payload['client_secret']),
    'refresh_token': str(runner['refresh_token']),
    'grant_type': "refresh_token",
    'f': 'json'}
    
    # first request is the access token
    res = requests.post(url=auth_url, data=payload)
    access_token = res.json()['access_token']
    
    # next request are the activities
    activites_url = "https://www.strava.com/api/v3/athlete/activities?after=1682899200"
    header = {'Authorization': 'Bearer ' + access_token}

    #get the data
    dataset = requests.get(activites_url, headers=header)
    
    # stream it into json
    json_data = json_stream.load(dataset.iter_content(32))

    # go through each run and get the total
    for runs in json_data:
        runner['total'] += runs['distance']
        

pixels.fill((0,0,0))
pixels.show()

#test data
'''runners=[]
runners.append({'colour': (255,0,0),'total': 14000})
runners.append({'colour': (0,255,0),'total': 28000})
runners.append({'colour': (0,0,255),'total': 42000})
'''

LED_total = 30
distance = 420 #ISS
#distance = 384400 #moon
LEDperKM = distance/LED_total
print("LED per KM:" +str(LEDperKM))

running_total = 30
for runner in runners:
    print("********************************")
    print(runner['name'])
    colour = runner['colour']
    
    km_total = runner['total']/1000 
    light_total = math.floor(km_total / LEDperKM)
    light_end = running_total - light_total
    
    if light_end < 0:
        light_end = 0
    
    print("km total :"+str(km_total))
    print("light total :"+str(light_total))
    print("Running total :"+str(running_total))
    print("Light end :"+str(light_end))
    
    if light_end <=30:
        # go from 30 to 30-11
        for i in range(running_total,light_end,-1):
            pixels[i-1] = colour
            pixels.show()
            time.sleep(0.2)
            
        running_total = light_end