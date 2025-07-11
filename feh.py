import subprocess
import signal
import time
from config import *

FULL_SCREEN = 1
ZOOM_100 = 2


class Feh:
    mode = 0
    current = ""
    def full_screen(self, dir):
        if self.mode == FULL_SCREEN and self.is_running():
            return

        self.stop()
        self.process = subprocess.Popen([FEH,"-x","--geometry","4096x2160+1920+0","-R", "30","-D", "10", "-Y", dir])
        self.mode = FULL_SCREEN

    def zoom_100(self, file, dir):
        subprocess.Popen([FEH,"-x","--geometry","4096x2160+1920+0", "-Y", "-R", str(sleep_time + buffer_time), "-C", font_dir, "-e", "yudit/40", "--draw-tinted","-K",'Caption/', file], cwd=dir)
        self.current = file
        self.mode = ZOOM_100


    def is_running(self):
        return self.process.poll() is None
    
    def stop(self):
        try:
            if self.mode != 0:
                self.process.kill()
        except OSError:
	        print("Process died itself")
