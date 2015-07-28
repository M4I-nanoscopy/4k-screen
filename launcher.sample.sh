#!/bin/bash

screen -d -m -S viewerd
screen -S viewerd -X stuff "python /home/local/UNIMAAS/h.boulanger/4k-screen/viewerd.py"`echo -ne '\015'` 

