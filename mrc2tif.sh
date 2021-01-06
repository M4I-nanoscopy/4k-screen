#!/bin/bash

/mnt/export/scisoft/em2em/em2em_linux.sh -t <<- EOF
	2D
	MRC
	FEI_EPU
	SINGLE_IMAGE_FILE
	TIFF
	GREY_SCALE_IMAGE
	$1
	$2
	NO
	YES
EOF
