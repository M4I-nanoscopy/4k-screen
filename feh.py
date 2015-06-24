import subprocess
import signal
import time

FEH = "/home/pi/feh-2.13/src/feh"
#FEH = "feh"

FULL_SCREEN = 1
ZOOM_100 = 2

class Feh:
    mode = 0

    def full_screen(self, dir):
        if self.mode == FULL_SCREEN and self.is_running():
            return

	    self.stop()
        self.process = subprocess.Popen([FEH, "-q", "-F","-R", "30","-D", "10", "-Y", dir])
        self.mode = FULL_SCREEN

    def zoom_100(self, file, dir):

        subprocess.Popen([FEH, "-q", "-F","--zoom", "100", "-Y","--info","stat -c %%z %F","-d", "-R", "40", "-C",  "/home/pi/feh-2.13/share/fonts/", "-e", "yudit/40", "--draw-tinted", file], cwd=dir)

        self.mode = ZOOM_100


    def is_running(self):
        return self.process.poll() is None
    
    def stop(self):
        try:
            if self.mode != 0:
                self.process.kill()
       	except OSError:
	        print "Process died itself"
