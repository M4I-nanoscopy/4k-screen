#!/usr/bin/python

import os
import sys
import datetime
import time
import glob
import re
import shutil
import subprocess
import shlex

ignore_datasets_started_days_ago = 1

' TODO: save scanned file list, so that we can load that, instead of having to do one initial scan. '
ignored_dirs = {}
known_files = {}

WORKING_DIR = "/home/admin/scannerd/serverscratch/4k-screen"
RAWDATA = "/home/admin/scannerd/rawdata_ro"

def only_accept_extensions(fn, extlist, case_sensitive=False):
    if not case_sensitive:
        extlist = list(ext.lower()    for ext in extlist)
        fn = fn.lower()
    for ext in extlist:
        if fn.endswith(ext):
            return True
    return False

def match_dataset( dirname ):
    # match automatically generated dirnames like 20141124_rbg.ravelli
    m = re.match('^(20[0-9][0-9])([01][0-9])([0123][0-9])[_-].*', os.path.basename(dirname) )
    if m == None:
        print "Ignoring from now on, not named like a dataset dir: %r" % dirname
        return False

    yr,mo,dy = m.groups()

    # no time, so be pessimistic about when on that day it was started
    dataset_datetime = datetime.datetime( int(yr), int(mo), int(dy), 23,59) 
    ago = now - dataset_datetime
    if ago.days > ignore_datasets_started_days_ago:
        print "Ignoring from now on, %d is more than %s days ago: %r"%( ago.days, 
                                                                        ignore_datasets_started_days_ago,
                                                                        dataset_dirname)
        return False

    return True

def file_blacklist( ffn ):
    with open(WORKING_DIR + '/blacklist.txt') as f:
        patterns = f.read().splitlines()

    for pattern in patterns:
        m = re.match(pattern, ffn)
        
        if m is not None:
            return True

    return False

def process( ffn ):
    conversions = {
        "autocontrast": [
            '.*/T12.*/.*.tif',
            '.*/ARCTICA/.*.tif'
        ],
        "mrc_convert_autoscale": [
            '.*.mrc'
        ]
    }

    for convert_function, patterns in conversions.iteritems():
        for pattern in patterns:
            m = re.match(pattern, ffn)
        
            if m is not None:
                globals()[convert_function](ffn)
                return

    copy(ffn)

def mrc_convert_autoscale( ffn ):
    queue("/home/admin/scannerd/mrc2tif.sh '%s' '%s'" % (ffn, WORKING_DIR + '/rawdata/' + os.path.basename(ffn).replace('.mrc','')))

def autocontrast( ffn ):
    queue("/usr/bin/convert -auto-level '%s' '%s'" % (ffn, WORKING_DIR + '/rawdata/' + os.path.basename(ffn)))

def copy( ffn ):
    queue("/bin/cp '%s' '%s'" % (ffn, WORKING_DIR + '/rawdata/' + os.path.basename(ffn)))

def queue( command ):
    # Simply add a command to the queue
    subprocess.call(shlex.split('/usr/bin/tsp -n %s' % command))

while 1: 
    now = datetime.datetime.now()

    new_file_stats = 0
    inspected_dirs = 0
    new_file_stats = 0
    new_files = [] # ffn

    for dataset_dirname in glob.glob( os.path.join( RAWDATA ,'*', '*') ):

        if dataset_dirname in ignored_dirs:
            continue

        if not match_dataset( dataset_dirname ):
            ignored_dirs[dataset_dirname] = True
            continue

        print 'walking %r' % dataset_dirname
        inspected_dirs += 1

        for r, ds, fs in os.walk( dataset_dirname ):

            for fn in fs:
                if only_accept_extensions( fn, ('.tif','.mrc')):
                    ffn = os.path.join(r, fn)

                    if ffn in known_files:
                        continue

                    known_files[ffn] = True

                    if file_blacklist(ffn):
                        print "Blacklisted %s" % ffn
                        continue

                    new_files.append( ffn )

    for ffn in new_files:
        print "Processing %s to serverscratch" % ffn
        process(ffn)
        
                
    print "Inspected dataset dirs: %s"%inspected_dirs
    print "Ignored dataset dirs:   %s"%len(ignored_dirs)
    print "New files seen:         %s"%len(new_files)

    print "--- sleeping... ---"
    print

    time.sleep(30)
