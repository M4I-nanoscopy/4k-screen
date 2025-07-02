#!/usr/bin/python3

import os
import sys
import datetime
import time
import glob
import re
import shutil
import subprocess
import shlex
import argparse
import traceback

from config import *

ignore_datasets_started_days_ago = 14

MRC_TO_TIF = os.path.join(SCREEN_DIR, "mrc2tif.sh")
CONFIGTXT = os.path.join(SCREEN_DIR, "Config", "config.txt")

known_files = {}
ignored_dirs = {}

parser = argparse.ArgumentParser(description='Process some rawdata')
parser.add_argument('--skip', action='store_true', help='Put all the existing images in known files on the first round')
config = parser.parse_args()

def only_accept_extensions(fn, extlist, case_sensitive=False):
    if not case_sensitive:
        extlist = list(ext.lower() for ext in extlist)
        fn = fn.lower()
    for ext in extlist:
        if fn.endswith(ext):
            return True
    return False

def match_dataset(dirname):
    # match automatically generated dirnames like 20141124_rbg.ravelli
    m = re.match('^(20[0-9][0-9])([01][0-9])([0123][0-9])[_-].*', os.path.basename(dirname))
    if m is None:
        print(f"Ignoring from now on, not named like a dataset dir: {dirname!r}")
        return False

    # Does not find changes if a directory inside the directory is changed e.g : .*/20150721_rgb.ravelli/test/
    # if test is changed it will not detect it
    try:
        dir_epoch_time = os.path.getmtime(dirname)
        yr, mo, dy = time.localtime(dir_epoch_time)[:3]
    except OSError:
        # Fallback to the directory name, happens sometime with network issues
        print("Fallback to directory name")
        yr, mo, dy = m.groups()

    # no time, so be pessimistic about when on that day it was started
    dataset_datetime = datetime.datetime(int(yr), int(mo), int(dy), 23, 59)
    ago = now - dataset_datetime
    if ago.days > ignore_datasets_started_days_ago:
        print(f"Ignoring from now on, {ago.days} is more than {ignore_datasets_started_days_ago} days ago: {dirname!r}")
        return False

    return True

patterns = []
def file_blacklist(ffn):
    global patterns

    # Open the blacklist only once per run. It was not neccesary to check this more often
    if len(patterns) == 0:
        with open(WORKING_DIR + '/blacklist.txt') as f:
            patterns = f.read().splitlines()

    for pattern in patterns:
        m = re.match(pattern, ffn)
        
        if m is not None:
            return True

    return False

def process(ffn, copypath):
    conversions = text2dict(CONFIGTXT, 'list')

    for convert_function, patterns in conversions.items():
        for pattern in patterns:
            m = re.match(pattern, ffn)
        
            if m is not None:
                globals()[convert_function](ffn, copypath)
                return

    copy(ffn, copypath)

def text2dict(file, value_type):
    dictionary = {}
    with open(file, 'r') as f:
        lines = f.read().splitlines()
        for line in lines:
            splitline = line.split('###')
            key = splitline[0]
            if value_type == 'list':
                value = splitline[1:]
            elif value_type == 'bool':
                value = (splitline[1] == "True")
            dictionary[key] = value
    return dictionary

def mrc_convert_autoscale(ffn, copypath):
    queue(f"{MRC_TO_TIF} '{ffn}' '{copypath}'")

def autocontrast(ffn, copypath):
    queue(f"/usr/bin/convert -auto-level '{ffn}' '{copypath}'")

def no_doubles_caption(ffn, caption_dirpath, file_ext='.tif'):
    double_diff = 0
    captionpath = os.path.join(caption_dirpath, os.path.basename(ffn)[:-4] + f'{file_ext}.txt')
    copy_captionpath = captionpath
    while os.path.exists(copy_captionpath):
        double_diff += 1
        copy_captionpath = captionpath[:-8] + str(double_diff) + f'{file_ext}.txt'
    return os.path.basename(copy_captionpath)[:-4]  # returns file name

def info(ffn, dirname, copypath):
    head, tail = os.path.split(copypath)
    txtpath = head + '/Caption/' + tail
    with open(txtpath + '.txt', 'a') as f:
        date_epoch = os.path.getmtime(ffn)
        date_struct = time.localtime(date_epoch)
        date = time.strftime("%a, %Y-%m-%d %H:%M", date_struct)

        microscope = os.path.split(dirname)[0]
        microscope = os.path.basename(microscope)

        operator = os.path.basename(dirname)
        operator = operator[9:]

        f.write(f"{tail}, {date}, {microscope}, {operator}")

def size_test(ffn):
    size = os.stat(ffn).st_size
    return size < min_size

def copy(ffn, copypath):    
    queue(f"/bin/cp '{ffn}' '{copypath}'")  # when too many files processed it makes double errors

def queue(command):
    # Simply add a command to the queue
    subprocess.call(f'/usr/bin/tsp -n {command}', shell=True)

def main():
    new_file_stats = 0
    inspected_dirs = 0
    new_files = []  # ffn

    for dataset_dirname in glob.glob(os.path.join(RAWDATA, '*', '*')):
        if dataset_dirname in ignored_dirs:
            continue
    
        if not match_dataset(dataset_dirname):
            ignored_dirs[dataset_dirname] = True
            continue

        print(f'walking {dataset_dirname!r}')
        inspected_dirs += 1
    
        for r, ds, fs in os.walk(dataset_dirname):
            for fn in fs:
                if only_accept_extensions(fn, ('.tif', '.mrc')):
                    ffn = os.path.join(r, fn)
    
                    if ffn in known_files:
                        continue

                    if time.time() - os.path.getmtime(ffn) < 25:
                        continue

                    known_files[ffn] = True

                    if config.skip:
                        print(f"First round file {ffn}")
                        continue

                    if file_blacklist(ffn):
                        print(f"Blacklisted {ffn}")
                        continue

                    if size_test(ffn):
                        print(f"Too small for process {ffn}")
                        continue

                    new_files.append(ffn)

                    print(f"Processing {ffn} to serverscratch")
                    no_double_name = no_doubles_caption(ffn, os.path.join(WORKING_DIR, 'rawdata', 'Caption'))
                    no_double_path = os.path.join(WORKING_DIR, 'rawdata', no_double_name)
                    process(ffn, no_double_path)
                    try:
                        info(ffn, dataset_dirname, no_double_path)
                    except (OSError, IOError) as e:
                        print("Failure to write caption file")

    config.skip = False

    print(f"Inspected dataset dirs: {inspected_dirs}")
    print(f"Ignored dataset dirs:   {len(ignored_dirs)}")
    print(f"New files seen:         {len(new_files)}")

    print("--- sleeping... ---")
    print()

if __name__ == '__main__':
    while True:
        now = datetime.datetime.now()
        try:
            main()
        except OSError as e:
            print(traceback.format_exc())
            print("Fatal OS exception, restarting from top")
            time.sleep(300)
        time.sleep(30)
