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
from config import *

ignore_datasets_started_days_ago = 1

MRC_TO_TIF = SCREEN_DIR + "/mrc2tif.sh"
CONFIGTXT = SCREEN_DIR + "/config.txt"
IGNORED_DIRS = SCREEN_DIR + "/ignored_dirs.txt"
KNOWN_FILES = SCREEN_DIR + "/known_files.txt"

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

    #Does not find changes if a directory inside the directory is changed e.g : .*/20150721_rgb.ravelli/test/
    #if test is changed it will not detect it
    dir_epoch_time = os.path.getmtime( dirname )
    yr,mo,dy = time.gmtime(dir_epoch_time)[:3]

    # no time, so be pessimistic about when on that day it was started
    dataset_datetime = datetime.datetime( yr, mo, dy, 23,59) 
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

def process( ffn, copypath ):
    conversions = text2dict( CONFIGTXT, 'list' )

    for convert_function, patterns in conversions.iteritems():
        for pattern in patterns:
            m = re.match(pattern, ffn)
        
            if m is not None:
                globals()[convert_function](ffn, copypath)
                return

    copy(ffn, copypath)

def text2dict( file, value_type ):
    dictionary = {}
    f =  open(file,'r')
    lines = f.read().splitlines()
    for line in lines :
        splitline = line.split('###')
        key = splitline[0]
        if value_type=='list':
            value = splitline[1:]
        elif value_type=='bool':
            value = (splitline[1]=="True")
        dictionary[key] = value
    f.close()
    return dictionary

def mrc_convert_autoscale( ffn, copypath ):
    queue("%s '%s' '%s'" % (MRC_TO_TIF, ffn, copypath ))

def autocontrast( ffn, copypath ):
    queue("/usr/bin/convert -auto-level '%s' '%s'" % (ffn, copypath))

def no_doubles( ffn ):
    double_diff = 0
    copypath = WORKING_DIR + '/rawdata/' + os.path.basename(ffn)[:-4] + '.tif'
    copy_copypath = copypath
    while os.path.exists(copy_copypath):
        double_diff+=1
        copy_copypath = copypath[:-4] + str(double_diff) + '.tif'
    return copy_copypath

def info( ffn , dirname , copypath ):
    head,tail=os.path.split(copypath)
    txtpath = head + '/Caption/' + tail
    f = open(txtpath+'.txt','a')

    date_epoch = os.path.getmtime( ffn )
    date_struct = time.gmtime(date_epoch+7200)
    year,month,mday,hour,mn,sec = date_struct[:6]
    date = str(year) + '/' + str(month) + '/' + str(mday) + ' ' + str(hour) + ':' + str(mn) + ':' + str(sec)
    f.write(date + ' ')

    microscope = os.path.split( dirname )[0]
    microscope = os.path.basename ( microscope)
    f.write(microscope + ' ')

    operator = os.path.basename( dirname )
    operator = operator[9:]
    f.write(operator)

    f.close()

def size_test( ffn ):
    size = os.stat(ffn).st_size
    return size<min_size

def copy( ffn, copypath ):    
    queue("/bin/cp '%s' '%s'" % (ffn, copypath))

def queue( command ):
    # Simply add a command to the queue
    subprocess.call(shlex.split('/usr/bin/tsp -n %s' % command))

if __name__ == '__main__' :

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

                        if size_test(ffn):
                            print "Too small for process %s" % ffn
                            continue

                        new_files.append( ffn )

                        print "Processing %s to serverscratch" % ffn
                        no_double_path = no_doubles( ffn )
                        process( ffn, no_double_path )
                        info ( ffn, dataset_dirname, no_double_path )

        print "Inspected dataset dirs: %s"%inspected_dirs
        print "Ignored dataset dirs:   %s"%len(ignored_dirs)
        print "New files seen:         %s"%len(new_files)

        print "--- sleeping... ---"
        print

        time.sleep(30)
