#! /usr/bin/env python
# File: fcntl-example-1.py
# Run with: python fcntl-example-1.py& python fcntl-example-1.py& python fcntl-example-1.py&

import fcntl, FCNTL
import os, time

FILE = "counter.txt"

if not os.path.exists(FILE):
    # create the counter file if it doesn't exist
    file = open(FILE, "w")
    file.write("0")
    file.close()

for i in range(1):
    # increment the counter
    file = open(FILE, "r+")
    print os.getpid(), ": waiting for lock:"
    fcntl.flock(file.fileno(), FCNTL.LOCK_EX)
    print os.getpid(), ": got lock, sleeping"
    time.sleep(10)
    print os.getpid(), ": finished sleeping, writing..."
    counter = int(file.readline()) + 1
    file.seek(0)
    file.write(str(counter))
    file.close() # unlocks the file
    print os.getpid(), "=>", counter
    time.sleep(0.1)
