#!/usr/local/bin/python
from henmanager import HenManager
import sys, time

def main():
    if len(sys.argv) != 2:
        print "FAIL: nodeid not provided!"
        return -1
    
    nodeid = sys.argv[1]
    hm = HenManager()
    if (hm.power(sys.argv[1], "poweroff") < 0):
        print "FAIL: hm.power(%s, \"poweroff\") failed (cause unknown)!"\
                % nodeid
        return -1
    time.sleep(2)
    (sts, output) = hm.powerSilent(sys.argv[1], "status")
    if (sts < 0):
        print "FAIL: hm.power(%s, \"status\") returned: %s" % (nodeid, output)
        return -1
    if (output == "on"):
        print "FAIL: hm.power(%s, \"status\") says the node is still on!" \
                    % nodeid
        return -1
    if (output == "off"):
        print "SUCCESS: hm.power(%s, \"poweroff\") succeeded." % nodeid
        return 0
    print "FAIL: hm.power(%s, \"status\") returned: %s" % (nodeid, output)
    return -1

if __name__ == "__main__":
    main()
