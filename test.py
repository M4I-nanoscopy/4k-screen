import unittest
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
from scannerd import *


class ScanQueueTest(unittest.TestCase):

    def setUp(self):
        self.queue = queue("mkdir %s/test" % SCREEN_DIR)
        time.sleep(1)

    def test_queue(self):
        self.assertTrue(os.path.exists("%s/test" % SCREEN_DIR))

    def tearDown(self):
        self.queue = None
        subprocess.call(shlex.split('/usr/bin/tsp -n rm -d %s/test' % SCREEN_DIR))

class ScanText2DictTest(unittest.TestCase):

    def setUp(self):
        tfl = open('%s/test_file_list.txt' % SCREEN_DIR, 'w')
        tfl.write('test###0###1###2###3\nest###4\n')
        tfl.close()
        tfb = open('%s/test_file_bool.txt' % SCREEN_DIR, 'w')
        tfb.write('test###True\nest###False\n')
        tfb.close()
        time.sleep(1)

    def test_list(self):
        self.expected_list_dict = {'test' : ['0','1','2','3'], 'est' : ['4']}
        self.list_dict = text2dict('%s/test_file_list.txt' % SCREEN_DIR, 'list')
        self.assertEqual( self.expected_list_dict, self.list_dict)

    def test_bool(self):
        self.expected_bool_dict = {'test' : True, 'est' : False}
        self.bool_dict = text2dict('%s/test_file_bool.txt' % SCREEN_DIR, 'bool')
        self.assertEqual( self.expected_bool_dict, self.bool_dict)

    def tearDown(self):
        subprocess.call(shlex.split('/usr/bin/tsp -n rm %s/test_file_list.txt' % SCREEN_DIR))
        subprocess.call(shlex.split('/usr/bin/tsp -n rm %s/test_file_bool.txt' % SCREEN_DIR))
        self.expected_list_dict = None
        self.list_dict = None
        self.expected_bool_dict = None
        self.bool_dict = None

if __name__ == '__main__':
    unittest.main()
