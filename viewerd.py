#!/usr/bin/python


import os
import sys
import datetime
import time
import glob
import re
import feh

feh = feh.Feh()

list_counter = 0
files = []
user_files = []

def sleep():
    print "--- sleeping... ---"
    print 

    time.sleep(30)

while 1:

    # Scan for images in drop dir, else show raw data
    user_files = os.listdir("/mnt/serverscratch/4k-screen/drop_images_here")
    if len(user_files) > 0:
        print "Full screen mode for user images"
        feh.full_screen("/mnt/serverscratch/4k-screen/drop_images_here")

        sleep()
        continue

    if datetime.datetime.now().hour > 20 or datetime.datetime.now().hour < 7:
	print "Outside office hours, go home!"
	sleep()
	continue

    print "Raw data mode in 100% zoom"

    # Only refresh the directory listing every 6 iterations, or when the file list is empty
    files = os.listdir("/mnt/serverscratch/4k-screen/rawdata")

    files.sort(key=lambda x: os.path.getctime("/mnt/serverscratch/4k-screen/rawdata/" + x))

    if len(files) == 0:
        sleep()
        continue

    current = files.pop(0)

    # Cifs drops sometimes temp files in the directory. Skip
    if re.match("cifs.{4}", current):
        print "Skipping temp file %s "  % current
	time.sleep(10)
        continue

    if os.path.exists("/mnt/serverscratch/4k-screen/rawdata/" + current):
        print "Show %s" % current
        feh.zoom_100(current, "/mnt/serverscratch/4k-screen/rawdata/")
    else:
        print "File %s does not exist. Weird! System overloaded?" % current
        time.sleep(10)
        continue

    sleep()

    try:
        os.remove("/mnt/serverscratch/4k-screen/rawdata/" + current)
    except OSError, e:
        print "File already deleted."
        pass








