#!/usr/bin/python


import os
import sys
import datetime
import time
import glob
import re
import feh
from math import sqrt
from config import *

feh = feh.Feh()

list_counter = 0
files = []
user_files = []

sorted_raw_img_path = raw_img_path + "/"


def sleep(t):
    print "--- sleeping %s seconds... ---" % t
    print 

    time.sleep(t)

sleep(10)

while 1:

    # Scan for images in drop dir, else show raw data
    try: 
        user_files = os.listdir(drop_img_path)
    except OSError:
        print "OSError"
        sleep(def_sleep_time)
        continue

    if len(user_files) > 0:
        print "Full screen mode for user images"
        feh.full_screen(drop_img_path)

        sleep(def_sleep_time)
        continue

    print "Raw data mode in 100% zoom"

    try:
        files = os.listdir(raw_img_path)
    except OSError:
        print "OSerror"
        sleep(def_sleep_time)
        continue

    if 'Caption' in files:
        files.remove('Caption')

    # Cifs drops sometimes temp files in the directory. remove
    for fil in files:
        if re.match("cifs.{4}", fil):
            files.remove(fil)

    files.sort(key=lambda x: os.path.getctime(sorted_raw_img_path + x))

    num_of_files = len(files)

    if num_of_files == 0:
        sleep(def_sleep_time)
        continue

    current = files.pop(0)
    
    if os.path.exists(sorted_raw_img_path + current):
        print "Show %s" % current
        if feh.current!=current:
            feh.zoom_100(current, sorted_raw_img_path)
    else:
        print "File %s does not exist. Weird! System overloaded?" % current
        time.sleep(min_sleep_time)
        continue
        
    sleep_time = max_sleep_time/sqrt(num_of_files)

    if sleep_time<min_sleep_time:
        sleep(min_sleep_time)
    else:
        sleep(sleep_time)     

    if num_of_files>1:
        try:
            os.remove(sorted_raw_img_path + current)
            os.remove(sorted_raw_img_path + 'Caption/' + current + '.txt')
        except OSError, e:
            print "File already deleted."
            pass
