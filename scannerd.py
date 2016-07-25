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
import argparse
from config import *

ignore_datasets_started_days_ago = 1

MRC_TO_TIF = os.path.join(SCREEN_DIR, "mrc2tif.sh")
CONFIGTXT = os.path.join(SCREEN_DIR, "Config", "config.txt")

known_files = {}
ignored_dirs = {}

parser = argparse.ArgumentParser( description = 'Process some rawdata')
parser.add_argument('--skip', action='store_true', help = 'Put all the existing images in known files on the first round')
config = parser.parse_args()

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
    m = re.match( '^(20[0-9][0-9])([01][0-9])([0123][0-9])[_-].*', os.path.basename( dirname ) )
    if m == None:
        print "Ignoring from now on, not named like a dataset dir: %r" % dirname
        return False

    # Does not find changes if a directory inside the directory is changed e.g : .*/20150721_rgb.ravelli/test/
    # if test is changed it will not detect it
    try:
        dir_epoch_time = os.path.getmtime( dirname )
        yr,mo,dy = time.localtime( dir_epoch_time )[:3]
    except OSError:
         # Fallback to the directory name, happens sometime with network issues
         print "Fallback to directory name"
         yr,mo,dy = m.groups()

    # no time, so be pessimistic about when on that day it was started
    dataset_datetime = datetime.datetime( int(yr), int(mo), int(dy), 23,59) 
    ago = now - dataset_datetime
    if ago.days > ignore_datasets_started_days_ago:
        print "Ignoring from now on, %d is more than %s days ago: %r"%( ago.days, 
                                                                        ignore_datasets_started_days_ago,
                                                                        dirname )
        return False

    return True

def file_blacklist( ffn ):
    with open( WORKING_DIR + '/blacklist.txt' ) as f:
        patterns = f.read().splitlines()

    for pattern in patterns:
        m = re.match( pattern, ffn )
        
        if m is not None:
            return True

    return False

def process( ffn, copypath ):
    conversions = text2dict( CONFIGTXT, 'list' )

    for convert_function, patterns in conversions.iteritems():
        for pattern in patterns:
            m = re.match(pattern, ffn)
        
            if m is not None:
                globals()[convert_function]( ffn, copypath )
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
            value = ( splitline[1]=="True" )
        dictionary[key] = value
    f.close()
    return dictionary

def mrc_convert_autoscale( ffn, copypath ):
    queue("%s '%s' '%s'" % ( MRC_TO_TIF, ffn, copypath ))

def autocontrast( ffn, copypath ):
    queue("/usr/bin/convert -auto-level '%s' '%s'" % ( ffn, copypath ))

def no_doubles_caption( ffn, caption_dirpath, file_ext='.tif' ):
    double_diff = 0
    captionpath = os.path.join(caption_dirpath, os.path.basename( ffn )[:-4]+ '%s.txt' % file_ext)
    copy_captionpath = captionpath
    while os.path.exists(copy_captionpath):
        double_diff+=1
        copy_captionpath = captionpath[:-8] + str( double_diff )+ '%s.txt' % file_ext
    return os.path.basename(copy_captionpath)[:-4]   #returns file name

def info( ffn , dirname , copypath ):
    head,tail=os.path.split(copypath)
    txtpath = head + '/Caption/' + tail
    f = open(txtpath+'.txt','a')

    date_epoch = os.path.getmtime( ffn )
    date_struct = time.localtime(date_epoch)
    date = time.strftime( "%a, %Y-%m-%d %H:%M",date_struct )

    microscope = os.path.split( dirname )[0]
    microscope = os.path.basename ( microscope )

    operator = os.path.basename( dirname )
    operator = operator[9:]

    f.write( tail + ', ' + date + ', ' + microscope + ', ' + operator )
    f.close()

def size_test( ffn ):
    size = os.stat(ffn).st_size
    return size<min_size

def copy( ffn, copypath ):    
    queue("/bin/cp '%s' '%s'" % (ffn, copypath)) # when  too many files processed it makes double errors

def queue( command ):
    # Simply add a command to the queue
    subprocess.call('/usr/bin/tsp -n %s' % command, shell=True)

def main():
    
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

                    if time.time()-os.path.getmtime(ffn)<25:
                        continue

                    known_files[ffn] = True

                    if config.skip:
                        print "First round file %s" % ffn
                        continue

                    if file_blacklist(ffn):
                        print "Blacklisted %s" % ffn
                        continue

                    if size_test(ffn):
                        print "Too small for process %s" % ffn
                        continue

                    new_files.append( ffn )

                    print "Processing %s to serverscratch" % ffn
                    no_double_name = no_doubles_caption( ffn, os.path.join(WORKING_DIR,'rawdata','Caption') )
                    no_double_path = os.path.join(WORKING_DIR, 'rawdata', no_double_name)
                    process( ffn, no_double_path )
                    info ( ffn, dataset_dirname, no_double_path )

    config.skip = False

    print "Inspected dataset dirs: %s"%inspected_dirs
    print "Ignored dataset dirs:   %s"%len(ignored_dirs)
    print "New files seen:         %s"%len(new_files)

    print "--- sleeping... ---"
    print

if __name__ == '__main__' :

    while 1: 
        now = datetime.datetime.now()
        main()
        time.sleep(30)
