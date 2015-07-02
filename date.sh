#!/bin/bash

date -d"`stat -c %z $1`" +"%a, %F %R"
