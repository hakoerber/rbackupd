#!/usr/bin/env python

import os

import src

src.run(os.path.join(os.path.dirname(os.path.realpath(__file__)), "conf/rbackupd.conf"))
